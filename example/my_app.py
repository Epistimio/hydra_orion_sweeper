import logging

import hydra
from omegaconf import DictConfig
import os
import sys

log = logging.getLogger(__name__)



def _load_checkpoint(path, model):
    checkpoint = os.path.join(path, 'chk.pt')
    
    if os.path.exists(checkpoint):
        # load checkpoint
        # ...
        return True
    
    return False

    
def load_checkpoint(model):
    current_checkpoint_path = os.getenv("CURRENT_CHECKPOINT")
    assert current_checkpoint_path is not None
    
    # if checkpoint file exist then always load it as it is the most recent
    if _load_checkpoint(current_checkpoint_path, model):
        return True
    
    # Previous checkpoint points to a job that finished and that we want to resume from
    # this is useful for genetic algo or algo that gradually improve on previous solutions
    prev_checkpoint_path = os.getenv("PREVIOUS_CHECKPOINT")
    
    if prev_checkpoint_path and _load_checkpoint(prev_checkpoint_path, model):
        return True
    
    return False

    

def save_checkpoint(model):
    current_checkpoint_path = os.getenv("CURRENT_CHECKPOINT")
    checkpoint = os.path.join(current_checkpoint_path, 'chk.pt')
    
    with open(checkpoint, 'w') as fp:
        # save checkpoint
        # ...
        pass


@hydra.main(config_path=".", config_name="config", version_base="1.1")
def dummy_training(cfg: DictConfig) -> float:
    """A dummy function to minimize
    Minimum is 0.0 at:
    lr = 0.12, dropout=0.33, opt=Adam, batch_size=4
    """
    
    # print(cfg.hydra )
    
    # makes sure folders are unique
    os.makedirs('newdir', exist_ok=False)
    
    model = None
    
    if load_checkpoint(model):
        print('Resuming from checkpoint')
    else:
        print('No checkpoint found')
    
    do = cfg.dropout
    bs = cfg.batch_size
    out = float(
        abs(do - 0.33) + int(cfg.optimizer.name == "Adam") + abs(cfg.optimizer.lr - 0.12) + abs(bs - 4)
    )
    log.info(
        f"dummy_training(dropout={do:.3f}, lr={cfg.optimizer.lr:.3f}, opt={cfg.optimizer.name}, batch_size={bs}) = {out:.3f}",
    )
    
    save_checkpoint(model)
    
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
