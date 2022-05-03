# -*- coding: utf-8 -*-
"""
Implements a sweeper plugin for Orion
"""
from typing import List, Optional

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
    ):
        from .implementation import OrionSweeperImpl

        self.sweeper = OrionSweeperImpl(
            orion, worker, algorithm, storage, parametrization
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
