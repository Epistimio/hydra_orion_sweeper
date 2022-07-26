import ast
import os
import shutil
from collections import defaultdict
from contextlib import contextmanager

import pytest
from hydra.core.utils import JobReturn, JobStatus
from hydra.types import HydraContext
from omegaconf import DictConfig, OmegaConf
from orion.core.utils.exceptions import (
    BrokenExperiment,
    CompletedExperiment,
    InvalidResult,
    ReservationRaceCondition,
    WaitingForTrials,
)

from hydra_plugins.hydra_orion_sweeper.orion_sweeper import (
    AlgorithmConf,
    OrionClientConf,
    OrionSweeper,
    StorageConf,
    WorkerConf,
)


def load_hydra_testing_config():
    dir = os.path.dirname(__file__)

    with open(os.path.join(dir, "hydra_config.py"), "r") as conf:
        hydra_config = ast.literal_eval(conf.read())

    try:
        shutil.rmtree("orion-test-tmp/")
    except:
        pass

    hydra_config["hydra"]["sweep"]["dir"] = "orion-test-tmp/"
    return hydra_config


def orion_configuration():
    return dict(
        orion=OmegaConf.structured(OrionClientConf()),
        worker=OmegaConf.structured(WorkerConf()),
        algorithm=OmegaConf.structured(AlgorithmConf()),
        storage=OmegaConf.structured(StorageConf()),
        parametrization=None,
        params=dict(a="uniform(0, 1)"),
    )


def my_task(*args, **kwargs):
    print(args, kwargs)


def setup_orion_sweeper():
    sweeper = OrionSweeper(**orion_configuration())

    hydra_context = HydraContext(None, None)
    config = DictConfig(load_hydra_testing_config())

    sweeper.setup(hydra_context=hydra_context, task_function=my_task, config=config)
    return sweeper


def test_sweeper_n_workers():
    sweeper = setup_orion_sweeper().sweeper

    sweeper.worker_config.n_workers = 0
    assert sweeper.n_workers() == os.cpu_count()

    sweeper.worker_config.n_workers = -1
    assert sweeper.n_workers() == os.cpu_count()

    sweeper.worker_config.n_workers = 2
    assert sweeper.n_workers() == 2


errors = [None, WaitingForTrials, ReservationRaceCondition, CompletedExperiment]


@pytest.mark.parametrize("error", errors)
def test_orion_suggest_error_are_handled(monkeypatch, error):
    sweeper = setup_orion_sweeper().sweeper

    class FakeClient:
        def __init__(self) -> None:
            self.count = 0

        def suggest(self, *args, **kwargs):
            self.count += 1

            if error is not None:
                raise error

    monkeypatch.setattr(sweeper, "client", FakeClient())
    sweeper.suggest_trials(10)

    if error:
        assert sweeper.client.count == 1
    else:
        assert sweeper.client.count == 10


def test_optimize_exception_are_reraised(monkeypatch):
    sweeper = setup_orion_sweeper().sweeper

    def optimize(*args, **kwargs):
        raise RuntimeError()

    class Release:
        def __init__(self) -> None:
            self.released = False

        def release_all(self):
            self.released = True

        def close(self):
            pass

    traker = Release()
    monkeypatch.setattr(sweeper, "new_experiment", lambda *args: traker)
    monkeypatch.setattr(sweeper, "optimize", optimize)
    monkeypatch.setattr(sweeper, "release_all", traker.release_all)

    with pytest.raises(RuntimeError):
        sweeper.sweep([])

    assert traker.release_all


def test_job_status_processing(monkeypatch):
    sweeper = setup_orion_sweeper().sweeper

    class FakeTrial:
        def __init__(self, fails) -> None:
            self.fails = fails

        def __repr__(self) -> str:
            return f"Trial({self.fails})"

    class FakeClient:
        def __init__(self) -> None:
            self.count = 0
            self.stats = defaultdict(int)

        def release(self, trial, status):
            self.stats[status] += 1

        def observe(self, trial, objective):
            if trial.fails:
                raise RuntimeError()

            self.stats["finished"] += 1

    monkeypatch.setattr(sweeper, "client", FakeClient())

    status = [
        JobStatus.COMPLETED,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.UNKNOWN,
    ]

    mytrials = [FakeTrial(i == 1) for i, _ in enumerate(status)]
    sweeper.pending_trials = set(mytrials)
    failures = []
    sweeper.observe_results(
        mytrials,
        [JobReturn(status=s, _return_value=1) for s in status],
        failures,
    )

    assert len(failures) == 2
    assert sweeper.client.stats["broken"] == 2
    assert sweeper.client.stats["interrupted"] == 1
    assert sweeper.client.stats["finished"] == 1


def test_experiment_is_broken(monkeypatch):
    sweeper = setup_orion_sweeper().sweeper

    class FakeClient:
        @property
        def is_done(self):
            return False

        @property
        def is_broken(self):
            return True

    monkeypatch.setattr(sweeper, "client", FakeClient())
    monkeypatch.setattr(sweeper, "sample_trials", lambda *args: [])
    monkeypatch.setattr(sweeper, "execute_trials", lambda *args: [])

    with pytest.raises(BrokenExperiment):
        sweeper.optimize(None)


def test_experiment_is_broken_with_hint(monkeypatch):
    sweeper = setup_orion_sweeper().sweeper

    class FakeClient:
        @property
        def is_done(self):
            return False

        @property
        def is_broken(self):
            return True

    class SpecificException(Exception):
        pass

    def observe_results(trials, returns, failures):
        failures.append(
            JobReturn(status=JobStatus.FAILED, _return_value=SpecificException("Oh oh"))
        )

    monkeypatch.setattr(sweeper, "client", FakeClient())
    monkeypatch.setattr(sweeper, "sample_trials", lambda *args: [])
    monkeypatch.setattr(sweeper, "execute_trials", lambda *args: [])
    monkeypatch.setattr(sweeper, "observe_results", observe_results)

    try:
        sweeper.optimize(None)
        assert False, "Should have raised"
    except Exception as err:
        assert hasattr(err, "__cause__")
        assert isinstance(err.__cause__, SpecificException)
