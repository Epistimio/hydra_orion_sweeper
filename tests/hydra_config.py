{
    "hydra": {
        "run": {"dir": "outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}"},
        "sweep": {"dir": "None", "subdir": "${hydra.job.num}"},
        "launcher": {
            "_target_": "hydra._internal.core_plugins.basic_launcher.BasicLauncher"
        },
        "sweeper": {
            "_target_": "hydra_plugins.hydra_orion_sweeper.orion_sweeper.OrionSweeper",
            "orion": {
                "name": None,
                "version": None,
                "branching": None,
                "debug": "False",
                "workspace": None,
            },
            "worker": {
                "n_workers": 3,
                "pool_size": None,
                "reservation_timeout": 120,
                "max_trials": 8,
                "max_trials_per_worker": 1000000,
                "max_broken": 3,
            },
            "algorithm": {"type": "random", "config": {}},
            "storage": {
                "type": "legacy",
                "database": {"type": "pickleddb", "host": "orion_database.pkl"},
                "use_hydra_path": True,
            },
            "parametrization": None,
            "params": {"a": "uniform(0, 1)"},
        },
        "help": {
            "app_name": "${hydra.job.name}",
            "header": "${hydra.help.app_name} is powered by Hydra.\n",
            "footer": "Powered by Hydra (https://hydra.cc)\nUse --hydra-help to view Hydra specific help\n",
            "template": "${hydra.help.header}\n== Configuration groups ==\nCompose your configuration from those groups (group=option)\n\n$APP_CONFIG_GROUPS\n\n== Config ==\nOverride anything in the config (foo.bar=value)\n\n$CONFIG\n\n${hydra.help.footer}\n",
        },
        "hydra_help": {
            "template": "Hydra (${hydra.runtime.version})\nSee https://hydra.cc for more info.\n\n== Flags ==\n$FLAGS_HELP\n\n== Configuration groups ==\nCompose your configuration from those groups (For example, append hydra/job_logging=disabled to command line)\n\n$HYDRA_CONFIG_GROUPS\n\nUse '--cfg hydra' to Show the Hydra config.\n",
            "hydra_help": "???",
        },
        "hydra_logging": {
            "version": 1,
            "formatters": {"simple": {"format": "[%(asctime)s][HYDRA] %(message)s"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"level": "INFO", "handlers": ["console"]},
            "loggers": {"logging_example": {"level": "DEBUG"}},
            "disable_existing_loggers": False,
        },
        "job_logging": {
            "version": 1,
            "formatters": {
                "simple": {
                    "format": "[%(asctime)s][%(name)s][%(levelname)s] - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "simple",
                    "filename": "${hydra.runtime.output_dir}/${hydra.job.name}.log",
                },
            },
            "root": {"level": "INFO", "handlers": ["console", "file"]},
            "disable_existing_loggers": False,
        },
        "env": {},
        "mode": None,
        "searchpath": [],
        "callbacks": {},
        "output_subdir": ".hydra",
        "overrides": {
            "hydra": [
                "hydra/sweeper=orion",
                "hydra/launcher=basic",
                "hydra.sweeper.worker.max_trials=8",
                "hydra.sweeper.worker.n_workers=3",
                "hydra.sweep.dir=None",
            ],
            "task": ["a='choices([1, 2])'"],
        },
        "job": {
            "name": "a_module",
            "chdir": None,
            "override_dirname": "a='choices([4, 5, 6, 7, 8])'",
            "id": "???",
            "num": "???",
            "config_name": "compose.yaml",
            "env_set": {},
            "env_copy": [],
            "config": {
                "override_dirname": {"kv_sep": "=", "item_sep": ",", "exclude_keys": []}
            },
        },
        "runtime": {
            "version": "1.2.0",
            "version_base": "1.1",
            "cwd": "/mnt/c/Users/Newton/work/hydra_orion_sweeper",
            "config_sources": [
                {"path": "hydra.conf", "schema": "pkg", "provider": "hydra"},
                {
                    "path": "hydra.test_utils.configs",
                    "schema": "pkg",
                    "provider": "main",
                },
                {"path": "", "schema": "structured", "provider": "schema"},
            ],
            "output_dir": "???",
            "choices": {
                "group2": "file1",
                "group1": "file1",
                "hydra/env": "default",
                "hydra/callbacks": None,
                "hydra/job_logging": "default",
                "hydra/hydra_logging": "default",
                "hydra/hydra_help": "default",
                "hydra/help": "default",
                "hydra/sweeper": "orion",
                "hydra/launcher": "basic",
                "hydra/output": "default",
            },
        },
        "verbose": False,
    },
    "a": "uniform(0, 1)",
}
