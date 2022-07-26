import pytest

from hydra_plugins.hydra_orion_sweeper.implementation import (
    InvalidResult,
    choices,
    to_objective,
)
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
        .startswith("`hydra.sweeper.orion.parametrization` is deprecated;")
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
        .startswith("Both `hydra.sweeper.orion.parametrization` and")
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


choices_formats = [[4, 6, 8], ["a", "b", "c", "d"]]


@pytest.mark.parametrize("options", choices_formats)
def test_choices(options):

    dim = choices(options)("dimname")

    assert dim.get_prior_string() == f"choices({options})"


value_formats = [
    123,
    dict(name="objective", type="objective", value=123),
    [dict(name="objective", type="objective", value=123)],
]


@pytest.mark.parametrize("value", value_formats)
def test_to_objective(value):
    value = to_objective(value)
    assert value == [dict(name="objective", type="objective", value=123)]


def test_bad_objective_value():
    with pytest.raises(InvalidResult):
        to_objective("not a numberic value")
