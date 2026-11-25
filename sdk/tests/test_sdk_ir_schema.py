from ir.schema import schema


def test_reads_the_ir_schema_from_its_package() -> None:
    assert schema("node_type", 0)["properties"]["kind"] == {"const": "node_type"}
