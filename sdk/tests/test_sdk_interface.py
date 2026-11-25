import dataclasses

import pytest

import sdk


def test_node_returns_the_function_unchanged() -> None:
    def build() -> None: ...

    assert sdk.node(plan="ibis", version=1, tags=["a"])(build) is build


@pytest.mark.parametrize(
    "marker",
    [sdk.Minimum(0), sdk.Column(of="data"), sdk.Binding(), sdk.Seed()],
    ids=lambda marker: type(marker).__name__,
)
def test_markers_are_immutable(marker: object) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        marker.__setattr__("of", "other")


def test_value_is_defined_without_its_extras_being_imported() -> None:
    assert sdk.Value.__name__ == "Value"
