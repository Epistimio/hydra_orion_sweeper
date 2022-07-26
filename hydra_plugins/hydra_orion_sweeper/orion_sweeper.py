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
        orion: OrionClientConf,
        worker: WorkerConf,
        algorithm: AlgorithmConf,
        storage: StorageConf,
        parametrization: Optional[DictConfig],
        params: Optional[DictConfig],
    ):
        from .implementation import OrionSweeperImpl

        # >>> Remove with Issue #8
        if parametrization is not None and params is None:
            warn(
                "`hydra.sweeper.orion.parametrization` is deprecated;"
                "use `hydra.sweeper.params` instead",
                DeprecationWarning,
            )
            params = parametrization

        elif parametrization is not None and params is not None:
            warn(
                "Both `hydra.sweeper.orion.parametrization` and `hydra.sweeper.params` are defined;"
                "using `hydra.sweeper.params`",
                DeprecationWarning,
            )
        # <<<

        if params is None:
            params = dict()

        self.sweeper = OrionSweeperImpl(orion, worker, algorithm, storage, params)

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
