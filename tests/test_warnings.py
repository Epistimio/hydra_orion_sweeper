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
            None,
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
        .startswith("`hydra.sweeper.parametrization` is deprecated;")
    )


def test_parametrization_and_params():
    with pytest.warns(DeprecationWarning) as warnings:
        OrionSweeper(
            None,
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
        .startswith("Both `hydra.sweeper.parametrization` and")
    )


def test_no_warnings_with_params(recwarn):
    OrionSweeper(
        None,
        OrionClientConf(),
        WorkerConf(),
        AlgorithmConf(),
        StorageConf(),
        None,
        dict(),
    )

    assert len(recwarn) == 0


# <<< Remove with Issue #8


def test_sweeper_orion_is_deprecated():
    with pytest.warns(DeprecationWarning) as warnings:
        OrionSweeper(
            OrionClientConf(),
            OrionClientConf(),
            WorkerConf(),
            AlgorithmConf(),
            StorageConf(),
            None,
            dict(),
        )

    assert len(warnings) == 1
    assert (
        warnings[0].message.args[0].startswith("`hydra.sweeper.orion` is deprecated;")
    )


def test_sweeper_orion_is_deprecated_2():
    with pytest.warns(DeprecationWarning) as warnings:
        OrionSweeper(
            OrionClientConf(),
            None,
            WorkerConf(),
            AlgorithmConf(),
            StorageConf(),
            None,
            dict(),
        )

    assert len(warnings) == 1
    assert (
        warnings[0].message.args[0].startswith("`hydra.sweeper.orion` is deprecated;")
    )


def test_no_warnings_with_experiment(recwarn):
    OrionSweeper(
        None,
        OrionClientConf(),
        WorkerConf(),
        AlgorithmConf(),
        StorageConf(),
        None,
        dict(),
    )

    assert len(recwarn) == 0
