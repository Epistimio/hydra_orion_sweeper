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
    version: Optional[int] = None
    branching: Optional[str] = None
    debug: Optional[bool] = False
    workspace: Optional[str] = None

    # Set by the plugin
    id: Optional[str] = None
    trial: Optional[str] = None
    uuid: Optional[str] = None


@dataclass
class WorkerConf:
    """Orion Worker configuration

    See `worker <https://orion.readthedocs.io/en/stable/user/config.html#worker>`_
    """

    n_workers: int = 1
    pool_size: Optional[int] = None
    reservation_timeout: int = 120
    max_trials: int = 10000000
    max_trials_per_worker: int = 1000000
    max_broken: int = 3


@dataclass
class Database:
    """Orion database configuration

    See `Database <https://orion.readthedocs.io/en/stable/user/config.html#database>`_
    """

    type: str = "pickleddb"
    host: str = "orion_database.pkl"


@dataclass
class StorageConf:
    """Orion storage configuration

    See `storage <https://orion.readthedocs.io/en/stable/user/storage.html>`_
    """

    type: str = "legacy"
    database: Database = field(default_factory=Database)

    # if true filesystem based databases will use hydra working dir as base path
    # if you want a single database for all your run you should set this to false
    use_hydra_path: bool = True


@dataclass
class AlgorithmConf:
    """Orion optimization algorithm configuration

    See `algorithms <https://orion.readthedocs.io/en/stable/user/algorithms.html>`_
    """

    type: str = "random"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrionSweeperConf:
    """Orion Sweeper configuration"""

    _target_: str = "hydra_plugins.hydra_orion_sweeper.orion_sweeper.OrionSweeper"

    orion: OrionClientConf = field(default_factory=OrionClientConf)

    worker: WorkerConf = field(default_factory=WorkerConf)

    algorithm: AlgorithmConf = field(default_factory=AlgorithmConf)

    storage: StorageConf = field(default_factory=StorageConf)

    # deprecated, use params instead
    parametrization: Optional[Dict[str, Any]] = None

    # Search space (Optuna & default)
    # See `Search Space <https://orion.readthedocs.io/en/stable/user/searchspace.html>`_
    params: Optional[Dict[str, Any]] = None

    # Note: Ax space is configured as hydra.sweeper.ax.ax_config.params
    # which is a bit too convoluted for us to support


ConfigStore.instance().store(
    group="hydra/sweeper",
    name="orion",
    node=OrionSweeperConf,
    provider="orion",
)
