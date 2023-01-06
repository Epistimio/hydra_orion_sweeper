import pytest

from hydra_plugins.hydra_orion_sweeper.orion_sweeper import (
    AlgorithmConf,
    OrionClientConf,
    OrionSweeper,
    StorageConf,
    WorkerConf,
)


# >>> Remove with Issue #8
def test_parametrization_is_deprecated():
    with pytest.warns(DeprecationWarning) as warnings:
        OrionSweeper(
            OrionClientConf(),
            WorkerConf(),
            AlgorithmConf(),
            StorageConf(),
            dict(),
            None,
        )

    assert len(warnings) == 1
    assert (
        warnings[0]
        .message.args[0]
        .startswith("`hydra.sweeper.experiment.parametrization` is deprecated;")
    )


def test_parametrization_and_params():
    with pytest.warns(DeprecationWarning) as warnings:
        OrionSweeper(
            OrionClientConf(),
            WorkerConf(),
            AlgorithmConf(),
            StorageConf(),
            dict(),
            dict(),
        )

    assert len(warnings) == 1
    assert (
        warnings[0]
        .message.args[0]
        .startswith("Both `hydra.sweeper.experiment.parametrization` and")
    )


def test_no_warnings_with_params(recwarn):
    OrionSweeper(
        OrionClientConf(),
        WorkerConf(),
        AlgorithmConf(),
        StorageConf(),
        None,
        dict(),
    )

    assert len(recwarn) == 0


# <<< Remove with Issue #8
