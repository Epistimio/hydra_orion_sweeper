import pytest

from hydra_plugins.hydra_orion_sweeper.implementation import (
    InvalidResult,
    SpaceParser,
    choices,
    to_objective,
)

choices_formats = [[4, 6, 8], ["a", "b", "c", "d"], dict(a=0.25, b=0.75)]


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


override_formats = [
    "a=uniform(0, 1)",
    "a=loguniform(1, 2)",
    "a=normal(0, 1)",
    "a=choices([1, 2])",
    "a=choices(dict(a=0.25, b=0.75))",
    "a=fidelity(1, 3)",
]


@pytest.mark.parametrize("override", override_formats)
def test_parse_override(override):
    parser = SpaceParser()
    parser.add_from_overrides([override])

    space, _ = parser.space()

    if "dict" not in override:
        assert space.get("a").get_prior_string() == override.split("=", 1)[-1]
    else:
        assert space.get("a").get_prior_string() == "choices({'a': 0.25, 'b': 0.75})"
