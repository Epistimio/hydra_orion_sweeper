# -*- coding: utf-8 -*-
"""
Implements a sweeper plugin for Orion.
"""
import logging
import os
import re
import uuid
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from typing import Any, List, Optional, Sequence, Union

from hydra.core import utils
from hydra.core.override_parser.overrides_parser import OverridesParser
from hydra.core.override_parser.types import Override, QuotedString
from hydra.core.plugins import Plugins
from hydra.core.utils import JobReturn
from hydra.plugins.launcher import Launcher
from hydra.plugins.sweeper import Sweeper
from hydra.types import HydraContext, TaskFunction
from omegaconf import DictConfig, OmegaConf
from orion.algo.space import Dimension, Space
from orion.client import create_experiment
from orion.client.experiment import ExperimentClient
from orion.core.io.space_builder import DimensionBuilder, SpaceBuilder
from orion.core.utils.exceptions import (
    BrokenExperiment,
    CompletedExperiment,
    InvalidResult,
    ReservationRaceCondition,
    WaitingForTrials,
)
from orion.core.utils.flatten import flatten
from orion.core.worker.trial import AlreadyReleased, Trial
from orion.storage.base import setup_storage

from .config import AlgorithmConf, OrionClientConf, StorageConf, WorkerConf

logger = logging.getLogger(__name__)

NESTED_DIM_REGEX = re.compile(r"[A-Za-z0-9]*(\.[A-Za-z0-9]*)+=.*")

# pylint: disable=too-few-public-methods
class SpaceFunction:
    """Type to recognize orion functions parsed by the override parser"""

    def __init__(self, fun) -> None:
        self.fun = fun

    def __call__(self, name: str) -> Any:
        return self.fun(name)


def uniform(
    low: Union[int, float],
    high: Union[int, float],
    discrete: bool = False,
    precision: int = 4,
    shape: Optional[List] = None,
) -> SpaceFunction:
    """Builds a uniform dimension"""

    def dim(name):
        builder = DimensionBuilder()
        builder.name = name
        return builder.uniform(
            low, high, discrete=discrete, precision=precision, shape=shape
        )

    return SpaceFunction(dim)


def loguniform(
    low: Union[int, float],
    high: Union[int, float],
    discrete: bool = False,
    precision: int = 4,
    shape: Optional[List] = None,
) -> SpaceFunction:
    """Builds a uniform dimension"""

    def dim(name):
        builder = DimensionBuilder()
        builder.name = name
        return builder.loguniform(
            low, high, discrete=discrete, precision=precision, shape=shape
        )

    return SpaceFunction(dim)


def normal(
    loc: Union[int, float],
    scale: Union[int, float],
    discrete: bool = False,
    precision: int = 4,
    shape: Optional[List] = None,
) -> SpaceFunction:
    """Builds a normal dimension"""

    def dim(name):
        builder = DimensionBuilder()
        builder.name = name
        return builder.normal(
            loc, scale, discrete=discrete, precision=precision, shape=shape
        )

    return SpaceFunction(dim)


def fidelity(
    low: Union[int, float], high: Union[int, float], base: Union[int, float] = 2
) -> SpaceFunction:
    """Builds a fidelity dimension"""

    def dim(name):
        builder = DimensionBuilder()
        builder.name = name
        return builder.fidelity(low, high, base=base)

    return SpaceFunction(dim)


def choices(options) -> SpaceFunction:
    """Builds a choices dimension"""

    def tovalue(v):
        if isinstance(v, QuotedString):
            return v.text
        return v

    if isinstance(options, list):
        options = [tovalue(option) for option in options]

    def dim(name):
        builder = DimensionBuilder()
        builder.name = name
        return builder.choices(options)

    return SpaceFunction(dim)


def override_dict(**kwargs):
    """Simple dictionary function"""
    return kwargs


def override_parser():
    """Create an override parser with Orion's functions"""
    parser = OverridesParser.create()
    parser.functions.register(name="uniform", func=uniform)
    parser.functions.register(name="loguniform", func=loguniform)
    parser.functions.register(name="normal", func=normal)
    parser.functions.register(name="choices", func=choices)
    parser.functions.register(name="fidelity", func=fidelity)
    parser.functions.register(name="dict", func=override_dict)
    return parser


def as_overrides(trial, additional, uuid):
    """Returns the trial arguments as hydra overrides"""
    kwargs = deepcopy(additional)
    kwargs.update(flatten(trial.params))

    args = [f"{k}={v}" for k, v in kwargs.items()]
    args += [
        f"hydra.sweeper.orion.id={trial.experiment}",
        f"hydra.sweeper.orion.trial={trial.id}",
        f"hydra.sweeper.orion.uuid={uuid}",
    ]
    return tuple(args)


def to_objective(value):
    """Convert a return value into an Orion objective"""

    if isinstance(value, (float, int)):
        return [dict(name="objective", type="objective", value=value)]

    if isinstance(value, dict):
        return [value]

    if isinstance(value, (list, tuple)):
        return value

    raise InvalidResult(
        f"Value '{value}' of type '{str(type(value))}' is not an expected return type"
    )


class SpaceParser:
    """Generate an Orion space from parameters and overrides"""

    def __init__(self) -> None:
        self.base_space = dict()
        self.overrides = dict()
        self.arguments = dict()

    def space(self) -> Space:
        """Generate the final space after overrides that will be used for the optimization"""
        configuration = deepcopy(self.base_space)
        configuration.update(self.overrides)
        space = SpaceBuilder().build(configuration)

        return space, self.arguments

    def add_from_parametrization(self, parametrization: Optional[DictConfig]) -> None:
        """Use the parametrization retrieved from the configuration to generate a
        preliminary research space

        """
        self._recursive_dim_builder(self.arguments, self.base_space, parametrization)

    def _recursive_dim_builder(
        self, args, dest, parametrization: Optional[DictConfig], depth: int = 0
    ) -> None:
        for k, v in parametrization.items():
            if isinstance(v, (dict, DictConfig)):
                subspace = dict()
                subargs = dict()

                self._recursive_dim_builder(subargs, subspace, v, depth + 1)

                if subargs:
                    args[k] = subargs

                if subspace:
                    dest[k] = subspace

                continue

            try:
                dim = DimensionBuilder().build(k, v)
                dest[dim.name] = dim.get_prior_string()
            except (TypeError, NameError):
                # Regular argument
                args[k] = v

    def add_from_overrides(self, arguments: List[str]) -> None:
        """Create a dictionary of overrides to modify the research space"""

        self._recursive_overrides(self.arguments, self.overrides, arguments)

    def _recursive_overrides(self, args, overrides, arguments):
        regular_args = []
        nested_overrides = defaultdict(list)
        for arg in arguments:
            if NESTED_DIM_REGEX.match(arg):
                name, rest = arg.split(".", 1)
                nested_overrides[name].append(rest)
            else:
                regular_args.append(arg)

        parser = override_parser()
        parsed = parser.parse_overrides(regular_args)

        for name, nestedargs in nested_overrides.items():
            suboverrides = dict()
            subargs = dict()

            self._recursive_overrides(subargs, suboverrides, nestedargs)

            if subargs:
                args[name] = subargs

            if suboverrides:
                overrides[name] = suboverrides

        for override in parsed:
            dim = self.process_overrides(override)

            if dim is None:
                args[override.get_key_element()] = override.value()
            else:
                overrides[dim.name] = dim.get_prior_string()

    def process_overrides(self, override: Override) -> Dimension:
        """Identify the sweep overrides and build a matching dimension"""
        values = override.value()
        name = override.get_key_element()

        def build_dim(name):
            builder = DimensionBuilder()
            builder.name = name
            return builder

        if isinstance(values, SpaceFunction):
            return values(name)

        elif override.is_choice_sweep():
            return build_dim(name).choices(*values.list)

        elif override.is_range_sweep():
            if values.step == 1:
                return build_dim(name).uniform(values.start, values.stop, discrete=True)

            choices = list(range(values.start, values.stop + values.step, values.step))
            return build_dim(name).choices(*choices)

        elif override.is_interval_sweep():
            discrete = type(values.start) is int
            log = "log" in values.tags

            cast_type = float
            if discrete or values.start % 1 == values.end % 1 == 0.0:
                cast_type = int

            method = build_dim(name).uniform
            if log:
                method = build_dim(name).loguniform

            return method(
                cast_type(values.start), cast_type(values.end), discrete=discrete
            )
        else:
            try:
                # Not sweep override but could still be orion
                return DimensionBuilder().build(name, values)
            except (TypeError, NameError):
                # Not a hyperparameter space definition
                logger.debug("Could not process dimension %s: %s", name, values)


@contextmanager
def clientctx(client):
    """Automatically close an orion client"""
    try:
        yield client
    finally:
        client.close()


# pylint: disable=too-many-public-methods,too-many-instance-attributes
class OrionSweeperImpl(Sweeper):
    """Implementation of the orion Sweeper"""

    def __init__(
        self,
        orion: OrionClientConf,
        worker: WorkerConf,
        algorithm: AlgorithmConf,
        storage: StorageConf,
        params: Optional[DictConfig],
    ):
        self.space = None
        self.arguments = dict()
        self.pending_trials = set()
        self.client = None
        self.storage = None
        self.uuid = uuid.uuid1().hex

        self.orion_config = orion
        self.worker_config = worker
        self.algo_config = algorithm
        self.storage_config = storage

        self.launcher: Optional[Launcher] = None
        self.hydra_context: Optional[HydraContext] = None
        self.job_results = None
        self.job_idx: Optional[int] = None

        self.space_parser = SpaceParser()
        self.space_parser.add_from_parametrization(params)

    def setup(
        self,
        *,
        hydra_context: HydraContext,
        task_function: TaskFunction,
        config: DictConfig,
    ) -> None:
        """Setup the hydra launcher"""
        self.job_idx = 0
        self.config = config
        self.hydra_context = hydra_context

        self.pending_trials = set()
        self.space = None
        self.arguments = dict()

        logger.debug("Starting launcher")

        self.launcher = Plugins.instance().instantiate_launcher(
            hydra_context=hydra_context,
            task_function=task_function,
            config=config,
        )

    def working_directory(self):
        """Fetch working directory"""
        return self.config.hydra.sweep.dir

    def n_workers(self):
        """Fetch the number of worker"""
        n = self.worker_config.n_workers
        if n <= 0:
            return os.cpu_count()

        return n

    def suggest_trials(self, count) -> List[Trial]:
        """Suggest a bunch of trials to be dispatched to the workers"""
        trials = []

        for _ in range(count):
            try:
                trial = self.client.suggest(pool_size=count)
                trials.append(trial)

            # non critical errors
            except WaitingForTrials:
                break

            except ReservationRaceCondition:
                break

            except CompletedExperiment:
                break

        return trials

    def _patch_database_path(self, config):
        database = config.get("database", {})
        dbtype = database.get("type")
        use_hydra_path = config.pop("use_hydra_path", True)

        if use_hydra_path and dbtype in ("pickleddb",):
            database["host"] = os.path.join(self.working_directory(), database["host"])

        return config

    def new_experiment(self, arguments) -> ExperimentClient:
        """Initialize orion client from the config and the arguments"""

        self.space_parser.add_from_overrides(arguments)
        self.space, self.arguments = self.space_parser.space()

        dict_config = OmegaConf.to_container(self.algo_config)
        algo_type = dict_config.pop("type", "random")
        algo_config = dict_config.pop("config", dict())

        storage_config = self._patch_database_path(
            OmegaConf.to_container(self.storage_config)
        )

        self.storage = setup_storage(storage_config)

        logger.info("Orion Optimizer %s", self.algo_config)
        logger.info("with parametrization %s", self.space.configuration)

        return create_experiment(
            name=self.orion_config.name,
            version=self.orion_config.version,
            space=self.space,
            algorithms={algo_type: algo_config},
            strategy=None,
            max_trials=self.worker_config.max_trials,
            max_broken=self.worker_config.max_broken,
            storage=storage_config,
            branching=self.orion_config.branching,
            max_idle_time=None,
            heartbeat=None,
            working_dir=self.orion_config.workspace,
            debug=self.orion_config.debug,
            executor=None,
        )

    def sweep(self, arguments: List[str]) -> None:
        """Execute the optimization process"""

        assert self.config is not None
        assert self.launcher is not None
        assert self.job_idx is not None

        logger.debug("Starting new experiment")
        self.client = self.new_experiment(arguments)

        with clientctx(self.client):
            try:
                self.optimize(self.client)
            except Exception as e:
                self.release_all()
                raise e

    def release_all(self) -> None:
        """Make sure not trials remain reserved"""
        for trial in self.pending_trials:
            try:
                self.client.release(trial, status="interrupted")
            except AlreadyReleased:
                pass

    def optimize(self, _: ExperimentClient) -> None:
        """Run the hyperparameter search in batches"""
        failures = []

        while not self.client.is_done:
            trials = self.sample_trials()

            returns = self.execute_trials(trials)

            self.observe_results(trials, returns, failures)

            if self.client.is_broken:
                if len(failures) == 0:
                    logger.error(
                        "Experiment has reached is maximum amount of broken trials"
                    )
                    raise BrokenExperiment("Max broken trials reached, stopping")

                # make the `Future` raise the exception it received
                try:
                    exception = failures[-1].return_value
                    raise exception

                except Exception as e:
                    raise BrokenExperiment("Max broken trials reached, stopping") from e

            if len(failures) > 0:
                for failure in failures:
                    logger.error("Exception was received %s", failure.return_value)

        self.show_results()

    def sample_trials(self) -> List[Trial]:
        """Sample a new batch of trials"""

        trials = self.suggest_trials(self.n_workers())
        logger.debug("Suggest %d new trials", len(trials))
        self.pending_trials.update(set(trials))
        return trials

    def execute_trials(self, trials: List[Trial]) -> Sequence[JobReturn]:
        """Execture the given batch of trials"""

        overrides = list(as_overrides(t, self.arguments, self.uuid) for t in trials)
        self.validate_batch_is_legal(overrides)

        returns = self.launcher.launch(overrides, initial_job_idx=self.job_idx)
        self.job_idx += len(returns)
        return returns

    def observe_one(
        self, trial: Trial, result: JobReturn, failures: Sequence[JobReturn]
    ) -> None:
        """Observe a single trial"""
        value = result.return_value

        try:
            objective = to_objective(value)
            self.client.observe(trial, objective)

        except Exception as e:  # pylint: disable=broad-except
            self.client.release(trial, status="broken")
            result.status = utils.JobStatus.FAILED
            result.return_value = e
            failures.append(result)

    def observe_results(
        self,
        trials: List[Trial],
        returns: Sequence[JobReturn],
        failures: Sequence[JobReturn],
    ):
        """Record the result of each trials"""
        for trial, result in zip(trials, returns):
            self.pending_trials.remove(trial)

            if result.status == utils.JobStatus.COMPLETED:
                self.observe_one(trial, result, failures)

            elif result.status == utils.JobStatus.FAILED:
                # We probably got an exception
                self.client.release(trial, status="broken")
                failures.append(result)

            elif result.status == utils.JobStatus.UNKNOWN:
                # Might be interrupted by user
                self.client.release(trial, status="interrupted")

    def show_results(self) -> None:
        """Retrieve the optimization stats and show which config was the best"""
        results = self.client.stats

        best_params = self.client.get_trial(uid=results.best_trials_id).params

        results = asdict(results)
        results["name"] = "orion"
        results["best_evaluated_params"] = best_params
        results["start_time"] = str(results["start_time"])
        results["finish_time"] = str(results["finish_time"])
        results["duration"] = str(results["duration"])

        OmegaConf.save(
            OmegaConf.create(results),
            f"{self.config.hydra.sweep.dir}/optimization_results.yaml",
        )

        logger.info(
            "Best parameters: %s", " ".join(f"{x}={y}" for x, y in best_params.items())
        )
