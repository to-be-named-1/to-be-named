from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest
import yaml

from ir.reader import DOCUMENT_FIELDS, Code, CodeNodeContract, ContractError, Diagnostic, Kind, NodeTypeContract, read

CORPUS = Path(__file__).parents[2] / "conformance/v0/python"
VALID = sorted(path for path in (CORPUS / "valid").iterdir() if path.is_dir())
INVALID: list[tuple[Kind, Path]] = [
    *(("code_node", path) for path in sorted((CORPUS / "invalid" / "code_nodes").iterdir())),
    *(("node_type", path) for path in sorted((CORPUS / "invalid" / "node_types").iterdir())),
]


def load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def expected_documents(case: Path) -> dict[str, Any]:
    return {path.stem: load(path) for path in (case / "expected").glob("*.yaml")}


@pytest.mark.parametrize("case", VALID, ids=lambda path: path.name)
def test_reads_valid_case_as_node_types_into_expected_documents(case: Path) -> None:
    reading = read(case, kind="node_type")

    assert reading.diagnostics == ()
    documents = {contract.function: contract.document(image="platform-base") for contract in reading.contracts}
    assert documents == expected_documents(case)


@pytest.mark.parametrize("case", VALID, ids=lambda path: path.name)
def test_reads_valid_case_as_code_nodes_without_what_only_node_types_state(case: Path) -> None:
    reading = read(case, kind="code_node")

    assert reading.diagnostics == ()
    left_out = {*DOCUMENT_FIELDS, *(f.name for f in NodeTypeContract.own_fields())}
    expected = {
        name: {key: value for key, value in document.items() if key not in left_out}
        for name, document in expected_documents(case).items()
    }
    assert {contract.function: contract.mapping() for contract in reading.contracts} == expected
    assert all(type(contract) is CodeNodeContract for contract in reading.contracts)


@pytest.mark.parametrize(("kind", "case"), INVALID, ids=lambda value: value.name if isinstance(value, Path) else value)
def test_reports_invalid_case_errors_by_code_and_location(kind: Kind, case: Path) -> None:
    reading = read(case, kind=kind)

    assert [entry(d) for d in reading.diagnostics] == load(case / "errors.yaml")


def entry(diagnostic: Diagnostic) -> dict[str, object]:
    # Parsers place syntax errors differently, so the corpus gives them by code and file only.
    if diagnostic.code == "syntax.invalid":
        return {"code": diagnostic.code, "path": diagnostic.path.as_posix()}
    return {
        "code": diagnostic.code,
        "path": diagnostic.path.as_posix(),
        "line": diagnostic.line,
        "column": diagnostic.column,
        "node": diagnostic.node,
        "field": diagnostic.field,
    }


def test_checked_raises_with_every_error() -> None:
    reading = read(CORPUS / "invalid" / "code_nodes" / "role_duplicate", kind="code_node")

    with pytest.raises(ContractError) as raised:
        reading.checked()

    assert raised.value.diagnostics == reading.diagnostics
    assert "seeds.second" in str(raised.value)


def test_checked_returns_contracts_when_valid() -> None:
    contracts = read(CORPUS / "valid" / "filter", kind="node_type").checked()

    assert [(contract.name, contract.version) for contract in contracts] == [("filter", 1)]


def test_keeps_the_table_class_of_every_port() -> None:
    (combine,) = read(CORPUS / "valid" / "ports", kind="code_node").checked()
    (deduplicate,) = read(CORPUS / "valid" / "output_class", kind="code_node").checked()

    assert {name: port.table for name, port in combine.inputs.items()} == {
        "main": "pandas",
        "parts": "arrow",
        "extra": "polars_frame",
        "more": "arrow",
    }
    assert {name: port.table for name, port in combine.outputs.items()} == {"data": "arrow"}
    assert {name: port.table for name, port in deduplicate.outputs.items()} == {"data": "ibis", "removed": "ibis"}


def test_only_node_types_hold_what_only_node_types_state() -> None:
    own = {f.name for f in NodeTypeContract.own_fields()}

    assert own
    assert own.isdisjoint(f.name for f in fields(CodeNodeContract))


def test_reads_only_the_paths_given(tmp_path: Path) -> None:
    (tmp_path / "first.py").write_text("from sdk import node\n\n\n@node()\ndef first() -> None: ...\n")
    (tmp_path / "second.py").write_text("def broken(:\n")

    reading = read(tmp_path, [tmp_path / "first.py"], kind="code_node")

    assert [contract.name for contract in reading.contracts] == ["first"]
    assert reading.diagnostics == ()


def test_rejects_a_path_outside_the_root(tmp_path: Path) -> None:
    (tmp_path / "root").mkdir()
    (tmp_path / "elsewhere.py").write_text("from sdk import node\n\n\n@node()\ndef away() -> None: ...\n")

    with pytest.raises(ValueError, match="is not under the root"):
        read(tmp_path / "root", [tmp_path / "elsewhere.py"], kind="code_node")


def test_gives_no_contracts_from_a_file_with_errors_of_its_own(tmp_path: Path) -> None:
    (tmp_path / "clean.py").write_text("from sdk import node\n\n\n@node()\ndef clean() -> None: ...\n")
    (tmp_path / "starred.py").write_text(
        "from sdk import node\nfrom string import *\n\n\n@node()\ndef starred() -> None: ...\n"
    )

    reading = read(tmp_path, kind="code_node")

    assert [contract.name for contract in reading.contracts] == ["clean"]
    assert [(d.path.as_posix(), d.code) for d in reading.diagnostics] == [("starred.py", "import.star")]


def test_reports_a_node_nested_too_deeply_and_reads_the_others(tmp_path: Path) -> None:
    union = " | ".join(["int"] * 3000)
    (tmp_path / "deep.py").write_text(
        "from sdk import node\n\n\n"
        f"@node()\ndef deep(*, value: {union}) -> None: ...\n\n\n"
        "@node()\ndef shallow() -> None: ...\n"
    )

    reading = read(tmp_path, kind="code_node")

    assert [contract.name for contract in reading.contracts] == ["shallow"]
    assert [(d.code, d.line, d.node) for d in reading.diagnostics] == [("limit.nesting", 5, "deep")]


def test_reports_a_file_nested_too_deeply_to_parse(tmp_path: Path) -> None:
    (tmp_path / "deep.py").write_text("value = " + "-" * 100_000 + "1\n")

    reading = read(tmp_path, kind="code_node")

    assert [(d.path.as_posix(), d.code, d.line) for d in reading.diagnostics] == [("deep.py", "limit.nesting", 1)]


def test_every_code_the_corpus_expects_is_a_code_of_the_reader() -> None:
    expected = {entry["code"] for path in (CORPUS / "invalid").rglob("errors.yaml") for entry in load(path)}

    assert expected <= {code.value for code in Code}


def test_rejects_a_relative_import_in_the_roots_own_init(tmp_path: Path) -> None:
    (tmp_path / "__init__.py").write_text("from . import helpers\n")

    reading = read(tmp_path, kind="code_node")

    assert [(d.path.as_posix(), d.code) for d in reading.diagnostics] == [("__init__.py", Code.IMPORT_OUTSIDE_ROOT)]


def test_finds_a_module_in_the_order_python_looks_for_it(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg.py").write_text('from typing import Literal\n\ntype Mode = Literal["module"]\n')
    (tmp_path / "pkg" / "__init__.py").write_text('from typing import Literal\n\ntype Mode = Literal["package"]\n')
    (tmp_path / "node.py").write_text(
        'from pkg import Mode\nfrom sdk import node\n\n\n@node()\ndef pick(*, mode: Mode = "package") -> None: ...\n'
    )

    (contract,) = read(tmp_path, [tmp_path / "node.py"], kind="code_node").checked()

    assert contract.params["mode"]["enum"] == ["package"]
