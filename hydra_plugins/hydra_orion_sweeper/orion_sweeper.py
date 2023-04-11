# -*- coding: utf-8 -*-
"""
Implements a sweeper plugin for Orion
"""
from typing import List, Optional
from warnings import warn

from hydra import TaskFunction
from hydra.plugins.sweeper import Sweeper
from hydra.types import HydraContext
from omegaconf import DictConfig

from .config import AlgorithmConf, OrionClientConf, StorageConf, WorkerConf


class OrionSweeper(Sweeper):
    """Class to interface with Orion"""

    def __init__(
        self,
        experiment: Optional[OrionClientConf],
        worker: WorkerConf,
        algorithm: AlgorithmConf,
        storage: StorageConf,
        parametrization: Optional[DictConfig],
        params: Optional[DictConfig],
        orion: Optional[OrionClientConf] = None,
    ):
        from .implementation import OrionSweeperImpl

        # >>> Remove with Issue #8
        if parametrization is not None and params is None:
            warn(
                "`hydra.sweeper.parametrization` is deprecated;"
                "use `hydra.sweeper.params` instead",
                DeprecationWarning,
            )
            params = parametrization

        elif parametrization is not None and params is not None:
            warn(
                "Both `hydra.sweeper.parametrization` and `hydra.sweeper.params` are defined;"
                "using `hydra.sweeper.params`",
                DeprecationWarning,
            )
        # <<<

        if params is None:
            params = dict()

        compat = False
        if orion is not None:
            compat = True
            warn(
                "`hydra.sweeper.orion` as dreprecated in favour of `hydra.sweeper.experiment`."
                "Please update to avoid misconfiguration",
                DeprecationWarning,
            )

        if experiment is None:
            experiment = orion

        self.sweeper = OrionSweeperImpl(
            experiment, worker, algorithm, storage, params, compat
        )

    def setup(
        self,
        *,
        hydra_context: HydraContext,
        task_function: TaskFunction,
        config: DictConfig,
    ) -> None:
        return self.sweeper.setup(
            hydra_context=hydra_context, task_function=task_function, config=config
        )

    def sweep(self, arguments: List[str]) -> None:
        return self.sweeper.sweep(arguments)
