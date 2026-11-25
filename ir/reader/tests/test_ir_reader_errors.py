from pathlib import PurePosixPath

from ir.reader import Code, ContractError, Diagnostic


def test_contract_error_lists_its_diagnostics() -> None:
    first = Diagnostic(
        PurePosixPath("node.py"),
        3,
        5,
        "flag",
        "limit",
        Code.DEFAULT_TYPE_MISMATCH,
        "the default is not of type integer",
    )
    second = Diagnostic(
        PurePosixPath("node.py"), 1, 1, None, None, Code.IMPORT_STAR, "a wildcard import hides the names it binds"
    )

    error = ContractError((first, second))

    assert str(error).splitlines() == [
        "node.py:3:5 flag.limit: the default is not of type integer [default.type_mismatch]",
        "node.py:1:1: a wildcard import hides the names it binds [import.star]",
    ]
