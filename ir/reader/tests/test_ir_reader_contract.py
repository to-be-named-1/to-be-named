import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from ir.reader import IR_VERSION, Input, NodeTypeContract, Output, contract, read

CORPUS = Path(__file__).parents[2] / "conformance/v0/python"
VALID = sorted(path for path in (CORPUS / "valid").iterdir() if path.is_dir())
HAND_WRITTEN = CORPUS.parent / "valid"
ANY_ORDER = HAND_WRITTEN / "node-type-outliers-keys-in-any-order.yaml"
IN_ORDER = sorted(set(HAND_WRITTEN.glob("node-type-*.yaml")) - {ANY_ORDER})
# The reader depends on no other package, so its tests read the schema from the repository, as they read the corpus.
SCHEMA = Path(__file__).parents[2] / f"schema/src/ir/schema/v{IR_VERSION}"
NODE_TYPE = json.loads((SCHEMA / "node_type.schema.json").read_text(encoding="utf-8"))
PARAMETER = json.loads((SCHEMA / "common.schema.json").read_text(encoding="utf-8"))["$defs"]["parameter"]


def misordered(document: dict[str, Any]) -> list[str]:
    """Return where the keys of a node-type document, or of a code node's mapping, stray from the schema's order."""
    defs = NODE_TYPE["$defs"]
    found = stray(document, NODE_TYPE, "document")
    for name, port in document.get("inputs", {}).items():
        found += stray(port, defs["input_port"], f"inputs.{name}")
    for name, port in document.get("outputs", {}).items():
        found += stray(port, defs["output_port"], f"outputs.{name}")
    for collection in ("params", "values"):
        for name, schema in document.get(collection, {}).items():
            found += parameter_strays(schema, f"{collection}.{name}")
    for role in ("grouping", "order"):
        if role in document:
            found += stray(document[role], defs["parameter_reference"], role)
    if "side_effects" in document:
        found += stray(document["side_effects"], NODE_TYPE["properties"]["side_effects"], "side_effects")
    return found


def parameter_strays(schema: dict[str, Any], where: str) -> list[str]:
    found = stray(schema, PARAMETER, where)
    for nested in ("items", "additionalProperties"):
        if nested in schema:
            found += parameter_strays(schema[nested], f"{where}.{nested}")
    return found


def stray(mapping: dict[str, Any], schema: dict[str, Any], where: str) -> list[str]:
    return [] if list(mapping) == [key for key in schema["properties"] if key in mapping] else [where]


def load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_writes_keys_in_the_order_the_schema_lists_them() -> None:
    assert contract._DOCUMENT_ORDER == tuple(NODE_TYPE["properties"])
    assert contract._PARAMETER_ORDER == tuple(PARAMETER["properties"])


@pytest.mark.parametrize("case", VALID, ids=lambda path: path.name)
def test_documents_and_corpus_follow_the_schema_order_at_every_level(case: Path) -> None:
    contracts = read(case, kind="node_type").checked()
    written = [load(path) for path in (case / "expected").glob("*.yaml")]
    documents = [
        *(contract.document(image="platform-base") for contract in contracts),
        *(contract.mapping() for contract in contracts),
        *written,
    ]

    assert [misordered(document) for document in documents] == [[] for _ in documents]


@pytest.mark.parametrize("path", IN_ORDER, ids=lambda path: path.name)
def test_hand_written_node_types_follow_the_schema_order_at_every_level(path: Path) -> None:
    assert misordered(load(path)) == []


def test_document_with_keys_in_any_order_holds_the_same_as_its_original() -> None:
    any_order = load(ANY_ORDER)

    assert any_order == load(HAND_WRITTEN / "node-type-outliers.yaml")
    assert misordered(any_order) == [
        "document",
        "outputs.flagged",
        "params.seed",
        "params.group_by",
        "params.threshold",
        "params.method",
        "params.columns",
        "values.outlier_rate",
    ]


def test_orders_keys_by_the_schema_whatever_order_the_contract_holds_them_in() -> None:
    contract = NodeTypeContract(
        module="nodes.mix",
        function="mix",
        language="python",
        plan="ibis",
        version=1,
        memory_class="streaming",
        dialects=("duckdb",),
        tags=("mixing",),
        title="Mix",
        inputs={"data": Input("ibis", many=True, optional=True)},
        outputs={"data": Output("ibis")},
        params={
            "weights": {"default": {}, "additionalProperties": {"minimum": 0, "type": "integer"}, "type": "object"},
            "labels": {"description": "Labels.", "items": {"pattern": "^[a-z]+$", "type": "string"}, "type": "array"},
        },
        values={"total": {"title": "Total", "type": "number"}},
    )

    document = contract.document(image="platform-base")

    assert misordered(document) == []
    assert misordered(contract.mapping()) == []
    assert list(document["params"]) == ["weights", "labels"]
