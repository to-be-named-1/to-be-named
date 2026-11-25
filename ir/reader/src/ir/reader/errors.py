"""Errors the reader reports."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath


class Code(StrEnum):
    """The stable code of each error a reader reports, which the conformance corpus gives and callers may act on.

    A member equals its string, such as `Code.IMPORT_CYCLE == "import.cycle"`.
    """

    ALIAS_ASSIGNMENT = "alias.assignment"
    ANNOTATION_MISSING = "annotation.missing"
    ANNOTATION_STRING = "annotation.string"
    ANNOTATION_UNRESOLVED = "annotation.unresolved"
    ANNOTATION_UNSUPPORTED = "annotation.unsupported"
    COLUMN_INVALID_INPUT = "column.invalid_input"
    COLUMN_UNKNOWN_INPUT = "column.unknown_input"
    DECORATOR_ARGUMENT_NOT_LITERAL = "decorator.argument_not_literal"
    DECORATOR_DIALECTS_NOT_ALLOWED = "decorator.dialects_not_allowed"
    DECORATOR_INVALID_ARGUMENT = "decorator.invalid_argument"
    DECORATOR_INVALID_VALUE = "decorator.invalid_value"
    DECORATOR_MISSING_ARGUMENT = "decorator.missing_argument"
    DECORATOR_NOT_CALLED = "decorator.not_called"
    DECORATOR_UNKNOWN_ARGUMENT = "decorator.unknown_argument"
    DECORATOR_UNSUPPORTED = "decorator.unsupported"
    DEFAULT_NOT_ALLOWED = "default.not_allowed"
    DEFAULT_NOT_LITERAL = "default.not_literal"
    DEFAULT_TYPE_MISMATCH = "default.type_mismatch"
    DEFAULT_VIOLATES_CONSTRAINT = "default.violates_constraint"
    IMPORT_CYCLE = "import.cycle"
    IMPORT_OUTSIDE_ROOT = "import.outside_root"
    IMPORT_STAR = "import.star"
    INPUT_INVALID_DEFAULT = "input.invalid_default"
    INPUT_NOT_TABLE = "input.not_table"
    INPUT_WRONG_TABLE_TYPE = "input.wrong_table_type"
    LIMIT_NESTING = "limit.nesting"
    LITERAL_INVALID = "literal.invalid"
    MARKER_CONFLICT = "marker.conflict"
    MARKER_DUPLICATE = "marker.duplicate"
    MARKER_INVALID_ARGUMENT = "marker.invalid_argument"
    MARKER_NOT_ALLOWED = "marker.not_allowed"
    MARKER_UNKNOWN = "marker.unknown"
    MODULE_UNNAMED = "module.unnamed"
    NAME_INVALID = "name.invalid"
    NAME_REBOUND = "name.rebound"
    NODE_ASYNC_FUNCTION = "node.async_function"
    NODE_NOT_MODULE_LEVEL = "node.not_module_level"
    OUTPUT_UNSUPPORTED = "output.unsupported"
    OUTPUT_WRONG_TABLE_TYPE = "output.wrong_table_type"
    OUTPUT_CLASS_FIELD_DEFAULT = "output_class.field_default"
    OUTPUT_CLASS_INVALID_FIELD = "output_class.invalid_field"
    OUTPUT_CLASS_NOT_FROZEN_DATACLASS = "output_class.not_frozen_dataclass"
    PARAMETER_TABLE_TYPE = "parameter.table_type"
    ROLE_DUPLICATE = "role.duplicate"
    SIGNATURE_VARIADIC = "signature.variadic"
    SYNTAX_INVALID = "syntax.invalid"


@dataclass(frozen=True)
class Diagnostic:
    """One error found in node code.

    Attributes:
        path: The file, relative to the root it was read from.
        line: The line, counted from 1.
        column: The column, counted from 1.
        node: The function the error concerns, if any.
        field: The parameter, input or output-class field the error concerns, if any.
        code: A stable code naming the rule that was broken, shared by every reader.
        message: What is wrong and how to fix it.
    """

    path: PurePosixPath
    line: int
    column: int
    node: str | None
    field: str | None
    code: Code
    message: str

    def __str__(self) -> str:
        where = ".".join(part for part in (self.node, self.field) if part)
        prefix = f"{self.path}:{self.line}:{self.column}"
        return f"{prefix} {where}: {self.message} [{self.code}]" if where else f"{prefix}: {self.message} [{self.code}]"


class ReaderError(Exception):
    """Base class of the errors the reader raises."""


class ContractError(ReaderError):
    """Node code that cannot be read into a contract, with every error found."""

    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        self.diagnostics = diagnostics
        super().__init__("\n".join(str(diagnostic) for diagnostic in diagnostics))
