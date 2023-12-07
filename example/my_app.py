import logging

import hydra
from omegaconf import DictConfig
import os
import sys

log = logging.getLogger(__name__)


@hydra.main(config_path=".", config_name="config", version_base=None)
def dummy_training(cfg: DictConfig) -> float:
    """A dummy function to minimize
    Minimum is 0.0 at:
    lr = 0.12, dropout=0.33, opt=Adam, batch_size=4
    """

    print(cfg)

    do = cfg.dropout
    bs = cfg.batch_size
    out = float(
        abs(do - 0.33)
        + int(cfg.optimizer.name == "Adam")
        + abs(cfg.optimizer.lr - 0.12)
        + abs(bs - 4)
    )
    # ..../hydra_orion_sweeper/example/multirun/2022-11-08/11-56-45/39
    # print(os.getcwd())
    log.info(
        f"dummy_training(dropout={do:.3f}, lr={cfg.optimizer.lr:.3f}, opt={cfg.optimizer.name}, batch_size={bs}) = {out:.3f}",
    )
    if cfg.error:
        raise RuntimeError("cfg.error is True")

    if cfg.return_type == "float":
        return out

    if cfg.return_type == "dict":
        return dict(name="objective", type="objective", value=out)

    if cfg.return_type == "list":
        return [dict(name="objective", type="objective", value=out)]

    if cfg.return_type == "none":
        return None


if __name__ == "__main__":
    dummy_training()
