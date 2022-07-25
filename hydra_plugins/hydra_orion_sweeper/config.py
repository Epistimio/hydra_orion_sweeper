# -*- coding: utf-8 -*-
"""
Defines the orion configuration that is exposed to hydra
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from hydra.core.config_store import ConfigStore


@dataclass
class OrionClientConf:
    """Orion EVC options"""

    name: Optional[str] = None
    version: Optional[str] = None
    branching: Optional[str] = None
    debug: Optional[str] = False
    workspace: Optional[str] = None


@dataclass
class WorkerConf:
    """Orion Worker configuration"""

    n_workers: int = 1
    pool_size: Optional[int] = None
    reservation_timeout: int = 120
    max_trials: int = 10000000
    max_trials_per_worker: int = 1000000
    max_broken: int = 3


@dataclass
class Database:
    """Orion database configuration"""

    type: str = "pickleddb"
    host: str = "orion_database.pkl"


@dataclass
class StorageConf:
    """Orion storage configuration"""

    type: str = "legacy"
    database: Database = Database()

    # if true filesystem based databases will use hydra working dir as base path
    # if you want a single database for all your run you should set this to false
    use_hydra_path: bool = True


@dataclass
class AlgorithmConf:
    """Orion optimization algorithm configuration"""

    type: str = "random"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrionSweeperConf:
    """Orion Sweeper configuration"""

    _target_: str = "hydra_plugins.hydra_orion_sweeper.orion_sweeper.OrionSweeper"

    orion: OrionClientConf = OrionClientConf()

    worker: WorkerConf = WorkerConf()

    algorithm: AlgorithmConf = AlgorithmConf()

    storage: StorageConf = StorageConf()

    # default parametrization of the search space
    parametrization: Dict[str, Any] = field(default_factory=dict)


ConfigStore.instance().store(
    group="hydra/sweeper",
    name="orion",
    node=OrionSweeperConf,
    provider="orion",
)
