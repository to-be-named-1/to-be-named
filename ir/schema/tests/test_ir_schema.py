import pytest

from ir.schema import schema


def test_reads_a_schema_of_an_ir_version() -> None:
    node_type = schema("node_type", 0)

    assert list(node_type["properties"])[:2] == ["ir_version", "kind"]


def test_fails_for_an_unknown_schema() -> None:
    with pytest.raises(FileNotFoundError):
        schema("unknown", 0)
