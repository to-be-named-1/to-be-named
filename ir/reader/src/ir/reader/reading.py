"""Reading node code into contracts from its source text, without executing it.

The rules are those of the Python interface in the IR specification, `docs/ir/03-node-types.md`.
"""

import ast
import builtins
import datetime
import re
from collections.abc import Iterable
from dataclasses import MISSING, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast, overload

from ir.reader.contract import CodeNodeContract, Input, Json, NodeTypeContract, Output, Table
from ir.reader.errors import Code, ContractError, Diagnostic

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_NOT_IDENTIFIERS = frozenset(
    "false in null true as break const continue else for function if import let loop package namespace return var "
    "void while y n yes no on off".split()
)
_MEMORY_FLOOR = re.compile(r"^[1-9][0-9]*(Ki|Mi|Gi|Ti)$")

# Every name a reader recognizes, by the dotted path it is imported from.
_KNOWN = {
    "builtins.str": "str",
    "builtins.int": "int",
    "builtins.float": "float",
    "builtins.bool": "bool",
    "datetime.datetime": "datetime",
    "datetime.date": "date",
    "datetime.timedelta": "timedelta",
    "typing.Annotated": "Annotated",
    "typing.Literal": "Literal",
    "typing.Sequence": "Sequence",
    "typing.Mapping": "Mapping",
    "collections.abc.Sequence": "Sequence",
    "collections.abc.Mapping": "Mapping",
    "dataclasses.dataclass": "dataclass",
    "ibis.Table": "ibis",
    "ibis.expr.types.Table": "ibis",
    "polars.LazyFrame": "polars_lazy",
    "polars.DataFrame": "polars_frame",
    "pyarrow.Table": "arrow",
    "pandas.DataFrame": "pandas",
    "sdk.node": "node",
    "sdk.Value": "Value",
    **{
        f"sdk.{marker}": marker
        for marker in (
            "Minimum Maximum Pattern Title Column ColumnSelector Binding Secret Grouping Order Seed SideEffectTarget"
        ).split()
    },
}
_RECOGNIZED_MODULES = ("sdk", "typing", "collections", "datetime", "dataclasses", "ibis", "polars", "pyarrow", "pandas")
_PRIMITIVES = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "datetime": {"type": "string", "format": "date-time"},
    "timedelta": {"type": "string", "format": "duration"},
    "date": {"type": "string", "format": "date"},
}
_TABLES_OF_PLAN = {"ibis": ("ibis",), "polars": ("polars_lazy",), None: ("arrow", "polars_frame", "pandas")}
_PLAN_NAMES = {"ibis": "an Ibis plan", "polars": "a Polars plan"}
_TABLE_NAMES = {
    "ibis": "ibis.Table",
    "polars_lazy": "polars.LazyFrame",
    "arrow": "pyarrow.Table",
    "polars_frame": "polars.DataFrame",
    "pandas": "pandas.DataFrame",
}
_CONSTRAINTS = ("Minimum", "Maximum", "Pattern", "Title")
_FORMATS = ("Column", "ColumnSelector", "Binding", "Secret")
_ROLES = ("Grouping", "Order", "Seed", "SideEffectTarget")
_DECORATOR_ARGUMENTS = ("plan", "version", "title", "tags", "gpu", "memory_class", "memory_floor", "dialects")
# Decorator arguments that only node types state, named like the fields only a node type's contract holds.
_NODE_TYPE_ONLY = frozenset(f.name for f in NodeTypeContract.own_fields())


type Kind = Literal["node_type", "code_node"]
"""What a reader reads code as: node types, which state what only node types state, or code nodes, for which
those arguments are ignored."""


@dataclass(frozen=True)
class Reading[C: CodeNodeContract]:
    """The contracts read from the node code under a root, and the errors found in it.

    A contract is given only for a node read without errors, from a file that has no errors of its own.
    """

    contracts: tuple[C, ...]
    diagnostics: tuple[Diagnostic, ...]

    def checked(self) -> tuple[C, ...]:
        """Return the contracts, or raise ContractError with every error if any was found."""
        if self.diagnostics:
            raise ContractError(self.diagnostics)
        return self.contracts


@overload
def read(
    root: Path, paths: Iterable[Path] | None = None, *, kind: Literal["node_type"]
) -> Reading[NodeTypeContract]: ...
@overload
def read(
    root: Path, paths: Iterable[Path] | None = None, *, kind: Literal["code_node"]
) -> Reading[CodeNodeContract]: ...
def read(root: Path, paths: Iterable[Path] | None = None, *, kind: Kind) -> Reading[Any]:
    """Read the nodes in Python files under a root.

    Args:
        root: The directory on Python's import path, such as a plugin package's `src` folder or a project's
            `code/` folder. Names are followed into modules within it.
        paths: The files whose nodes to read; every Python file under the root when None.
        kind: Whether the nodes are read as node types or as code nodes.

    Raises:
        ValueError: A path is not under the root.
    """
    reader = _Reader(root.resolve(), kind)
    files = sorted(reader.root.rglob("*.py")) if paths is None else sorted(Path(p).resolve() for p in paths)
    for path in files:
        if not path.is_relative_to(reader.root):
            raise ValueError(f"{path} is not under the root {reader.root}")
    contracts: list[CodeNodeContract] = []
    for path in files:
        module = reader.module_at(path)
        if module is None:
            continue
        found = reader.read_nodes(module)
        # A file with errors of its own, such as an import that cannot work, gives no contracts. Its nodes are
        # still read, so that every error in it is reported; all of its own errors exist once it is loaded.
        if not any(d.path == module.path for d in reader.load_diagnostics):
            contracts.extend(found)
    # Files sort by their path as a string, which every reader can reproduce, rather than part by part.
    diagnostics = sorted(
        {*reader.diagnostics, *reader.load_diagnostics},
        key=lambda d: (d.path.as_posix(), d.line, d.column, d.code, d.field or ""),
    )
    return Reading(tuple(contracts), tuple(diagnostics))


# A module-level binding of a name.
@dataclass(frozen=True)
class _Import:
    module: str
    node: ast.AST


@dataclass(frozen=True)
class _ImportFrom:
    module: str
    name: str
    node: ast.AST


@dataclass(frozen=True)
class _Definition:
    node: ast.TypeAlias | ast.ClassDef


@dataclass(frozen=True)
class _Other:
    node: ast.AST


type _Binding = _Import | _ImportFrom | _Definition | _Other


@dataclass
class _Module:
    name: str
    path: PurePosixPath
    tree: ast.Module
    bindings: dict[str, list[_Binding]] = field(default_factory=dict[str, list[_Binding]])


# What a name or annotation resolves to.
@dataclass(frozen=True)
class _Known:
    path: str


@dataclass(frozen=True)
class _RootModule:
    name: str


@dataclass(frozen=True)
class _Local:
    module: _Module
    node: ast.TypeAlias | ast.ClassDef


type _Symbol = _Known | _RootModule | _Local

_MUTABLE = (_Known("builtins.list"), _Known("builtins.dict"))


# Types, as an annotation describes them.
@dataclass(frozen=True)
class _Primitive:
    kind: str


@dataclass(frozen=True)
class _Literal:
    members: tuple[Json, ...]
    kind: str


@dataclass(frozen=True)
class _Sequence:
    item: _Type


@dataclass(frozen=True)
class _Mapping:
    value: _Type


@dataclass(frozen=True)
class _Table:
    kind: Table


@dataclass(frozen=True)
class _Optional:
    inner: _Type


@dataclass(frozen=True)
class _Value:
    inner: _Type


@dataclass(frozen=True)
class _Marker:
    kind: str
    args: tuple[Any, ...]
    keywords: dict[str, Any]
    node: ast.AST


@dataclass(frozen=True)
class _Annotated:
    inner: _Type
    markers: tuple[_Marker, ...]


@dataclass(frozen=True)
class _Class:
    module: _Module
    node: ast.ClassDef


@dataclass(frozen=True)
class _NoneType:
    pass


type _Type = (
    _Primitive | _Literal | _Sequence | _Mapping | _Table | _Optional | _Value | _Annotated | _Class | _NoneType
)


@dataclass
class _Scope:
    module: _Module
    node: str | None = None
    field: str | None = None


class _Reader:
    def __init__(self, root: Path, kind: Kind) -> None:
        self.root = root
        self.kind = kind
        self.modules: dict[Path, _Module | None] = {}
        self.diagnostics: list[Diagnostic] = []
        # Errors found while loading a module, which no later step may discard.
        self.load_diagnostics: list[Diagnostic] = []

    def report(self, scope: _Scope, at: ast.AST, code: Code, message: str) -> None:
        self.diagnostics.append(_diagnostic(scope, at, code, message))

    def report_load(self, scope: _Scope, at: ast.AST, code: Code, message: str) -> None:
        self.load_diagnostics.append(_diagnostic(scope, at, code, message))

    # Modules.

    def module_at(self, path: Path) -> _Module | None:
        """Load the file at an absolute path under the root as a module, parsed once per read, and record its bindings.

        Example: <root>/pkg/__init__.py -> _Module(name="pkg", path=PurePosixPath("pkg/__init__.py")); a file that
        does not parse -> None, with a syntax.invalid error.
        """
        if path in self.modules:
            return self.modules[path]
        relative = path.relative_to(self.root)
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        posix = PurePosixPath(relative.as_posix())
        try:
            tree = ast.parse(path.read_bytes(), filename=str(posix))
        except SyntaxError as error:
            self.modules[path] = None
            message = f"the file does not parse: {error.msg}"
            line, column = error.lineno or 1, error.offset or 1
            self.load_diagnostics.append(Diagnostic(posix, line, column, None, None, Code.SYNTAX_INVALID, message))
            return None
        except RecursionError, MemoryError:
            # The parser gives up on source nested beyond its stack, such as a very long chain of operators.
            self.modules[path] = None
            message = "the file is nested too deeply to read"
            self.load_diagnostics.append(Diagnostic(posix, 1, 1, None, None, Code.LIMIT_NESTING, message))
            return None
        module = _Module(".".join(parts), posix, tree)
        self.modules[path] = module
        self._bind(module, tree.body)
        return module

    def module_named(self, name: str) -> _Module | None:
        """Find the module of a dotted name within the root, in the order Python looks for it.

        Example: "pkg.sub" -> the module of <root>/pkg/sub/__init__.py, else of <root>/pkg/sub.py, else the
        namespace package <root>/pkg/sub/; none of them -> None.
        """
        base = self.root.joinpath(*name.split("."))
        for path in (base / "__init__.py", base.with_suffix(".py")):
            if path.is_file():
                return self.module_at(path.resolve())
        if name and base.is_dir():
            return self._namespace(base.resolve(), name)
        return None

    def _namespace(self, directory: Path, name: str) -> _Module:
        # A directory without __init__.py is a namespace package, as in Python: it binds no names of its own, and
        # its submodules are reached through it.
        module = self.modules.get(directory)
        if module is None:
            path = PurePosixPath(directory.relative_to(self.root).as_posix())
            module = _Module(name, path, ast.Module(body=[], type_ignores=[]))
            self.modules[directory] = module
        return module

    def _bind(self, module: _Module, body: list[ast.stmt]) -> None:
        """Record how each top-level name of a module is bound, without resolving any of them.

        Example: `import pyarrow as pa` -> bindings["pa"] == [_Import("pyarrow")].
        """
        scope = _Scope(module)
        for statement in body:
            match statement:
                case ast.Import(names=names):
                    for alias in names:
                        bound = alias.asname or alias.name.split(".")[0]
                        target = alias.name if alias.asname else alias.name.split(".")[0]
                        self._add(module, bound, _Import(target, statement))
                case ast.ImportFrom(names=names):
                    source = self._absolute(module, statement)
                    for alias in names:
                        if alias.name == "*":
                            self.report_load(
                                scope, statement, Code.IMPORT_STAR, "a wildcard import hides the names it binds"
                            )
                        elif source is not None:
                            self._add(module, alias.asname or alias.name, _ImportFrom(source, alias.name, statement))
                case ast.TypeAlias(name=ast.Name(id=name)):
                    self._add(module, name, _Definition(statement))
                case ast.ClassDef(name=name):
                    self._add(module, name, _Definition(statement))
                case ast.FunctionDef(name=name) | ast.AsyncFunctionDef(name=name):
                    self._add(module, name, _Other(statement))
                case ast.Assign(targets=targets):
                    for target in targets:
                        for name_node in ast.walk(target):
                            if isinstance(name_node, ast.Name):
                                self._add(module, name_node.id, _Other(statement))
                case ast.AnnAssign(target=ast.Name(id=name)):
                    self._add(module, name, _Other(statement))
                case ast.If(test=test, body=inner) if _is_type_checking(test):
                    self._bind(module, inner)
                case _:
                    pass

    def _add(self, module: _Module, name: str, binding: _Binding) -> None:
        module.bindings.setdefault(name, []).append(binding)

    def _absolute(self, module: _Module, statement: ast.ImportFrom) -> str | None:
        """Return the absolute name of the module an import names, resolving a relative import as Python does.

        Example: `from ..common import Flag` in pkg/sub/mod.py -> "pkg.common".
        """
        if statement.level == 0:
            return statement.module or ""
        is_package = module.path.name == "__init__.py"
        # The root's own __init__.py has the empty name and belongs to no package.
        names = module.name.split(".") if module.name else []
        package = names if is_package else names[:-1]
        if statement.level > len(package):
            message = "the relative import reaches outside its package or the root"
            self.report_load(_Scope(module), statement, Code.IMPORT_OUTSIDE_ROOT, message)
            return None
        base = package[: len(package) - (statement.level - 1)]
        return ".".join([*base, *([statement.module] if statement.module else [])])

    # Names.

    def resolve(self, scope: _Scope, module: _Module, expression: ast.expr, stack: tuple[str, ...]) -> _Symbol | None:
        """Resolve a name or a dotted attribute in a module to what it stands for.

        Example: `pa.Table` after `import pyarrow as pa` -> _Known("pyarrow.Table"); a class of the root -> _Local.
        """
        match expression:
            case ast.Name(id=name):
                return self._resolve_name(scope, module, name, expression, stack)
            case ast.Attribute(value=value, attr=attribute):
                owner = self.resolve(scope, module, value, stack)
                match owner:
                    case _Known(path=path):
                        return _Known(f"{path}.{attribute}")
                    case _RootModule(name=name):
                        return self._resolve_in(scope, name, attribute, expression, stack)
                    case None:
                        return None
                    case _:
                        self.report(scope, expression, Code.ANNOTATION_UNSUPPORTED, "an attribute of a definition")
                        return None
            case _:
                self.report(scope, expression, Code.ANNOTATION_UNSUPPORTED, "the expression is not a name")
                return None

    def _resolve_name(
        self, scope: _Scope, module: _Module, name: str, at: ast.AST, stack: tuple[str, ...]
    ) -> _Symbol | None:
        """Resolve one name through a module's bindings, following imports into modules within the root.

        Example: "Sequence" after `from collections.abc import Sequence` -> _Known("collections.abc.Sequence");
        "Flag" after `from .common import Flag` -> the _Local type alias defined in pkg/common.py.
        """
        key = f"{module.name}:{name}"
        if key in stack:
            self.report(scope, at, Code.IMPORT_CYCLE, f"{name} refers back to itself through imports")
            return None
        stack = (*stack, key)
        bindings = module.bindings.get(name)
        if not bindings:
            if name in vars(builtins):
                return _Known(f"builtins.{name}")
            self.report(scope, at, Code.ANNOTATION_UNRESOLVED, f"{name} is not imported or defined in {module.path}")
            return None
        if len(bindings) > 1:
            other = _Scope(module, scope.node, scope.field)
            self.report(other, bindings[1].node, Code.NAME_REBOUND, f"{name} is bound more than once in the module")
            return None
        match bindings[0]:
            case _Import(module=target):
                if target.split(".")[0] in _RECOGNIZED_MODULES:
                    return _Known(target)
                if self.module_named(target) is not None:
                    return _RootModule(target)
                self.report(scope, at, Code.IMPORT_OUTSIDE_ROOT, f"{target} is neither recognized nor within the root")
                return None
            case _ImportFrom(module=source, name=imported):
                if source.split(".")[0] in _RECOGNIZED_MODULES:
                    return _Known(f"{source}.{imported}")
                return self._resolve_in(scope, source, imported, at, stack)
            case _Definition(node=node):
                return _Local(module, node)
            case _Other(node=ast.Assign() | ast.AnnAssign()):
                message = f"{name} is assigned; write a type alias with a type statement"
                self.report(scope, at, Code.ALIAS_ASSIGNMENT, message)
                return None
            case _Other():
                self.report(scope, at, Code.ANNOTATION_UNSUPPORTED, f"{name} is not a type")
                return None

    def _resolve_in(self, scope: _Scope, source: str, name: str, at: ast.AST, stack: tuple[str, ...]) -> _Symbol | None:
        """Resolve a name inside a module of the root: a name the module binds, or one of its submodules.

        Example: ("pkg.common", "Flag") -> what Flag is bound to in pkg/common.py; ("pkg", "sub") ->
        _RootModule("pkg.sub").
        """
        module = self.module_named(source)
        if module is None:
            self.report(scope, at, Code.IMPORT_OUTSIDE_ROOT, f"{source} is neither recognized nor within the root")
            return None
        if name in module.bindings:
            return self._resolve_name(scope, module, name, at, stack)
        if self.module_named(f"{source}.{name}") is not None:
            return _RootModule(f"{source}.{name}")
        self.report(scope, at, Code.ANNOTATION_UNRESOLVED, f"{name} is not defined in {module.path}")
        return None

    def known(self, symbol: _Symbol | None) -> str | None:
        """Return the short kind of a recognized name, or None.

        Example: _Known("pyarrow.Table") -> "arrow"; _Known("typing.Optional") -> None.
        """
        return _KNOWN.get(symbol.path) if isinstance(symbol, _Known) else None

    # Annotations.

    def type_of(
        self, scope: _Scope, module: _Module, annotation: ast.expr, stack: tuple[str, ...] = ()
    ) -> _Type | None:
        """Turn an annotation into the type tree that the rest of the reader matches on.

        Example: `Sequence[pa.Table]` -> _Sequence(_Table("arrow")); `pl.DataFrame | None` ->
        _Optional(_Table("polars_frame")).
        """
        match annotation:
            case ast.Constant(value=None):
                return _NoneType()
            case ast.Constant(value=str()):
                self.report(scope, annotation, Code.ANNOTATION_STRING, "write the annotation itself, not a string")
                return None
            case ast.BinOp(left=left, op=ast.BitOr(), right=right):
                first = self.type_of(scope, module, left, stack)
                second = self.type_of(scope, module, right, stack)
                if first is None or second is None:
                    return None
                if isinstance(second, _NoneType) and not isinstance(first, _NoneType):
                    return _Optional(first)
                self.report(scope, annotation, Code.ANNOTATION_UNSUPPORTED, "a union other than an optional input")
                return None
            case ast.Subscript(value=base, slice=index):
                return self._subscript(scope, module, annotation, base, index, stack)
            case ast.Name() | ast.Attribute():
                symbol = self.resolve(scope, module, annotation, stack)
                return self._named(scope, annotation, symbol, stack)
            case _:
                self.report(scope, annotation, Code.ANNOTATION_UNSUPPORTED, "the annotation is not a type")
                return None

    def _named(self, scope: _Scope, at: ast.expr, symbol: _Symbol | None, stack: tuple[str, ...]) -> _Type | None:
        """Turn a resolved name into a type: a primitive, a table class, a type alias's value or a local class.

        Example: _Known("builtins.str") -> _Primitive("str"); _Known("pandas.DataFrame") -> _Table("pandas").
        """
        if symbol is None:
            return None
        kind = self.known(symbol)
        if kind in _PRIMITIVES:
            return _Primitive(kind)
        if kind in _TABLE_NAMES:
            return _Table(cast(Table, kind))
        match symbol:
            case _Local(module=module, node=ast.TypeAlias(type_params=[], value=value) as alias):
                key = f"{module.name}:type:{alias.name.id}"
                if key in stack:
                    self.report(scope, at, Code.IMPORT_CYCLE, "the type alias refers back to itself")
                    return None
                return self.type_of(scope, module, value, (*stack, key))
            case _Local(module=module, node=ast.ClassDef() as node):
                return _Class(module, node)
            case _Known(path="builtins.list" | "builtins.dict"):
                self.report(scope, at, Code.ANNOTATION_UNSUPPORTED, "use Sequence or Mapping, which are read-only")
                return None
            case _:
                self.report(
                    scope, at, Code.ANNOTATION_UNSUPPORTED, f"{ast.unparse(at)} has no counterpart in the profile"
                )
                return None

    def _subscript(
        self, scope: _Scope, module: _Module, at: ast.expr, base: ast.expr, index: ast.expr, stack: tuple[str, ...]
    ) -> _Type | None:
        """Type a subscripted annotation: Annotated, Literal, Sequence, Mapping or Value.

        Example: `Mapping[str, int]` -> _Mapping(_Primitive("int")); `Annotated[int, Minimum(0)]` ->
        _Annotated(_Primitive("int"), (<Minimum(0)>,)).
        """
        arguments = list(index.elts) if isinstance(index, ast.Tuple) else [index]
        symbol = self.resolve(scope, module, base, stack)
        if symbol is None:
            return None
        kind = self.known(symbol)
        if kind is None:
            hint = "use Sequence or Mapping, which are read-only" if symbol in _MUTABLE else "it is not recognized"
            self.report(scope, at, Code.ANNOTATION_UNSUPPORTED, f"{ast.unparse(base)} has no counterpart: {hint}")
            return None
        match kind, arguments:
            case "Annotated", [inner, *metadata] if metadata:
                inner_type = self.type_of(scope, module, inner, stack)
                markers = [self._marker(scope, module, item, stack) for item in metadata]
                if inner_type is None or None in markers:
                    return None
                return _Annotated(inner_type, tuple(m for m in markers if m is not None))
            case "Literal", members:
                return self._literal(scope, at, members)
            case "Sequence", [item]:
                item_type = self.type_of(scope, module, item, stack)
                return None if item_type is None else _Sequence(item_type)
            case "Mapping", [key, value]:
                key_type = self.type_of(scope, module, key, stack)
                value_type = self.type_of(scope, module, value, stack)
                if key_type is None or value_type is None:
                    return None
                if key_type != _Primitive("str"):
                    self.report(scope, key, Code.ANNOTATION_UNSUPPORTED, "a mapping's keys are strings")
                    return None
                return _Mapping(value_type)
            case "Value", [inner]:
                inner_type = self.type_of(scope, module, inner, stack)
                return None if inner_type is None else _Value(inner_type)
            case _:
                self.report(
                    scope, at, Code.ANNOTATION_UNSUPPORTED, f"{ast.unparse(at)} has no counterpart in the profile"
                )
                return None

    def _literal(self, scope: _Scope, at: ast.expr, members: list[ast.expr]) -> _Type | None:
        """Type a Literal whose members are all strings or all integers.

        Example: `Literal["a", "b"]` -> _Literal(("a", "b"), "str"); `Literal["a", 1]` -> None, with literal.invalid.
        """
        values: list[Json] = []
        for member in members:
            try:
                values.append(ast.literal_eval(member))
            except ValueError:
                self.report(scope, member, Code.LITERAL_INVALID, "a Literal member must be a string or an integer")
                return None
        kinds = {"bool" if isinstance(v, bool) else type(v).__name__ for v in values}
        if kinds not in ({"str"}, {"int"}):
            message = "the members of a Literal are all strings or all integers"
            self.report(scope, at, Code.LITERAL_INVALID, message)
            return None
        return _Literal(tuple(values), kinds.pop())

    def _marker(self, scope: _Scope, module: _Module, item: ast.expr, stack: tuple[str, ...]) -> _Marker | None:
        """Read one marker of an Annotated annotation, checking its arguments.

        Example: `Minimum(0)` -> _Marker("Minimum", (0,), {}); `Column(of="data")` -> _Marker("Column", (),
        {"of": "data"}).
        """
        if not isinstance(item, ast.Call):
            self.report(scope, item, Code.MARKER_UNKNOWN, "Annotated metadata must be one of the SDK's markers")
            return None
        symbol = self.resolve(scope, module, item.func, stack)
        if symbol is None:
            return None
        kind = self.known(symbol)
        if kind not in (*_CONSTRAINTS, *_FORMATS, *_ROLES):
            self.report(scope, item, Code.MARKER_UNKNOWN, "Annotated metadata must be one of the SDK's markers")
            return None
        try:
            args = tuple(ast.literal_eval(a) for a in item.args)
            keywords = {k.arg: ast.literal_eval(k.value) for k in item.keywords if k.arg is not None}
        except ValueError:
            self.report(scope, item, Code.MARKER_INVALID_ARGUMENT, f"the arguments of {kind} must be literals")
            return None
        expected: dict[str, tuple[int, tuple[str, ...]]] = {
            "Minimum": (1, ()),
            "Maximum": (1, ()),
            "Pattern": (1, ()),
            "Title": (1, ()),
            "Column": (0, ("of",)),
            "ColumnSelector": (0, ("of",)),
        }
        count, names = expected.get(kind, (0, ()))
        valid = len(args) == count and len(item.keywords) == len(names) and set(keywords) == set(names)
        if valid and kind in ("Minimum", "Maximum"):
            valid = isinstance(args[0], int | float) and not isinstance(args[0], bool)
        elif valid and kind in ("Pattern", "Title"):
            valid = isinstance(args[0], str)
        elif valid and names:
            valid = isinstance(keywords["of"], str)
        if valid and kind == "Pattern":
            try:
                re.compile(str(args[0]))
            except re.error:
                valid = False
        if not valid:
            self.report(scope, item, Code.MARKER_INVALID_ARGUMENT, f"{kind} does not take these arguments")
            return None
        return _Marker(kind, args, keywords, item)

    # Nodes.

    def read_nodes(self, module: _Module) -> list[CodeNodeContract]:
        """Read every node of a module: each module-level function decorated with node(...).

        Example: a module defining `@node(version=1) def combine(...)` -> [the contract of combine].
        """
        contracts: list[CodeNodeContract] = []
        top_level = set(map(id, module.tree.body))
        for function in ast.walk(module.tree):
            if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            scope = _Scope(module, function.name)
            # Reading recurses over the syntax tree, so an annotation nested deeply enough, such as a long chain of
            # unions, exhausts Python's stack; the function is then reported rather than the read failing.
            try:
                decorator = self._node_decorator(scope, module, function)
                if decorator is None:
                    continue
                if id(function) not in top_level:
                    self.report(scope, function, Code.NODE_NOT_MODULE_LEVEL, "a node is a module-level function")
                    continue
                if isinstance(function, ast.AsyncFunctionDef):
                    self.report(scope, function, Code.NODE_ASYNC_FUNCTION, "a node is not an async function")
                    continue
                if not module.name:
                    message = "an __init__.py directly in the root belongs to no module; move the node into a module"
                    self.report(scope, function, Code.MODULE_UNNAMED, message)
                    continue
                contract = self._read_node(scope, module, function, decorator)
            except RecursionError:
                self.report(scope, function, Code.LIMIT_NESTING, f"{function.name} is nested too deeply to read")
                continue
            if contract is not None:
                contracts.append(contract)
        return contracts

    def _node_decorator(
        self, scope: _Scope, module: _Module, function: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.Call | None:
        """Return a function's node(...) decorator, or None when it has none.

        Example: `@node(version=1)` -> its ast.Call; a bare `@node` -> None, with decorator.not_called.
        """
        found: ast.Call | None = None
        others: list[ast.expr] = []
        for decorator in function.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not isinstance(target, ast.Name | ast.Attribute):
                others.append(decorator)
                continue
            # Any decorator is resolved to see whether it is node, but one that is not node must not produce errors
            # of its own, so the errors resolving it reports are dropped. Errors found while loading a module it
            # leads to are kept, since they go to load_diagnostics.
            silent = _Scope(module, scope.node)
            mark = len(self.diagnostics)
            kind = self.known(self.resolve(silent, module, target, ()))
            del self.diagnostics[mark:]
            if kind != "node":
                others.append(decorator)
            elif isinstance(decorator, ast.Call):
                found = decorator
            else:
                self.report(scope, decorator, Code.DECORATOR_NOT_CALLED, "write node(...) with its arguments")
                return None
        if found is not None:
            for other in others:
                self.report(scope, other, Code.DECORATOR_UNSUPPORTED, "a node carries no decorator besides node")
        return found

    def _read_node(
        self, scope: _Scope, module: _Module, function: ast.FunctionDef, decorator: ast.Call
    ) -> CodeNodeContract | None:
        """Read one node function into its contract, or None when any error is found in it.

        Example: `@node(version=1) def combine(main: pd.DataFrame) -> pa.Table` ->
        NodeTypeContract(function="combine", version=1, inputs={"main": Input("pandas")},
        outputs={"data": Output("arrow")}).
        """
        start = len(self.diagnostics)
        if not _is_identifier(function.name):
            self.report(scope, function, Code.NAME_INVALID, f"{function.name} is not an identifier of the IR")
        options = self._decorator_options(scope, decorator)
        plan = options.get("plan")
        description, arg_descriptions = _docstring(ast.get_docstring(function))

        arguments = function.args
        if arguments.vararg or arguments.kwarg:
            at = arguments.vararg or arguments.kwarg
            self.report(scope, at or function, Code.SIGNATURE_VARIADIC, "a node takes no *args or **kwargs")
        positional = [*arguments.posonlyargs, *arguments.args]
        defaults: list[ast.expr | None] = [None] * (len(positional) - len(arguments.defaults)) + list(
            arguments.defaults
        )
        inputs: dict[str, Input] = {}
        for argument, default in zip(positional, defaults, strict=True):
            port = self._input(_Scope(module, function.name, argument.arg), module, argument, default, plan)
            if port is not None:
                inputs[argument.arg] = port

        params: dict[str, dict[str, Json]] = {}
        roles: dict[str, str] = {}
        for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True):
            argument_scope = _Scope(module, function.name, argument.arg)
            schema = self._parameter(argument_scope, module, argument, default, inputs, roles)
            if schema is not None:
                if argument.arg in arg_descriptions:
                    schema["description"] = arg_descriptions[argument.arg]
                params[argument.arg] = schema

        outputs, values = self._outputs(scope, module, function, plan)
        own: dict[str, Any] = {}
        if self.kind == "node_type":
            for own_field in NodeTypeContract.own_fields():
                if own_field.name in options:
                    own[own_field.name] = options[own_field.name]
                elif own_field.default is MISSING and own_field.default_factory is MISSING:
                    message = f"a node type states {own_field.name}="
                    self.report(scope, decorator, Code.DECORATOR_MISSING_ARGUMENT, message)
        if len(self.diagnostics) > start:
            return None
        contract = NodeTypeContract if self.kind == "node_type" else CodeNodeContract
        return contract(
            **own,
            language="python",
            module=module.name,
            function=function.name,
            plan=plan,
            title=options.get("title"),
            description=description,
            tags=tuple(options.get("tags", ())),
            gpu=options.get("gpu"),
            memory_class=options.get("memory_class"),
            memory_floor=options.get("memory_floor"),
            dialects=tuple(options.get("dialects", ())),
            inputs=inputs,
            outputs=outputs,
            params=params,
            values=values,
            grouping=roles.get("Grouping"),
            order=roles.get("Order"),
            seed=roles.get("Seed"),
            side_effect_target=roles.get("SideEffectTarget"),
        )

    def _decorator_options(self, scope: _Scope, decorator: ast.Call) -> dict[str, Any]:
        """Read the node decorator's keyword arguments into checked literal values.

        Example: `node(plan="ibis", tags=("joins",))` -> {"plan": "ibis", "tags": ["joins"]}.
        """
        options: dict[str, Any] = {}
        for argument in decorator.args:
            self.report(scope, argument, Code.DECORATOR_INVALID_ARGUMENT, "node takes keyword arguments only")
        for keyword in decorator.keywords:
            if keyword.arg is None:
                self.report(scope, keyword, Code.DECORATOR_INVALID_ARGUMENT, "node takes keyword arguments only")
                continue
            if keyword.arg not in _DECORATOR_ARGUMENTS:
                self.report(scope, keyword, Code.DECORATOR_UNKNOWN_ARGUMENT, f"node has no argument {keyword.arg}")
                continue
            if self.kind == "code_node" and keyword.arg in _NODE_TYPE_ONLY:
                continue
            try:
                value = ast.literal_eval(keyword.value)
            except ValueError:
                message = f"the argument {keyword.arg} must be a literal"
                self.report(scope, keyword.value, Code.DECORATOR_ARGUMENT_NOT_LITERAL, message)
                continue
            problem = _decorator_problem(keyword.arg, value)
            if problem is not None:
                self.report(scope, keyword.value, Code.DECORATOR_INVALID_VALUE, problem)
                continue
            options[keyword.arg] = list(value) if isinstance(value, tuple) else value
        if options.get("dialects") and options.get("plan") != "ibis":
            at = next(k for k in decorator.keywords if k.arg == "dialects")
            self.report(scope, at, Code.DECORATOR_DIALECTS_NOT_ALLOWED, "only an Ibis plan lists dialects")
        return options

    def _input(
        self, scope: _Scope, module: _Module, argument: ast.arg, default: ast.expr | None, plan: str | None
    ) -> Input | None:
        """Read a parameter before `*` into an input port.

        Example: `more: Sequence[pa.Table] = []` -> Input(table="arrow", optional=True, many=True).
        """
        if not _is_identifier(argument.arg):
            self.report(scope, argument, Code.NAME_INVALID, f"{argument.arg} is not an identifier of the IR")
        if argument.annotation is None:
            self.report(scope, argument, Code.ANNOTATION_MISSING, "an input is annotated with a table type")
            return None
        kind = self.type_of(scope, module, argument.annotation)
        if kind is None:
            return None
        optional = many = False
        match kind:
            case _Table():
                table = kind
                if default is not None:
                    self.report(scope, default, Code.INPUT_INVALID_DEFAULT, "a required input has no default")
            case _Optional(inner=_Table() as table):
                optional = True
                if not (isinstance(default, ast.Constant) and default.value is None):
                    message = "an optional input has the default None"
                    self.report(scope, default or argument, Code.INPUT_INVALID_DEFAULT, message)
            case _Sequence(item=_Table() as table):
                many, optional = True, default is not None
                if default is not None and _literal_or_none(default) not in ([], ()):
                    self.report(scope, default, Code.INPUT_INVALID_DEFAULT, "an input with many edges defaults to []")
            case _Annotated():
                self.report(scope, argument.annotation, Code.MARKER_NOT_ALLOWED, "markers do not annotate inputs")
                return None
            case _:
                message = "a parameter before * is an input, annotated with a table type"
                self.report(scope, argument.annotation, Code.INPUT_NOT_TABLE, message)
                return None
        if table.kind not in _TABLES_OF_PLAN[plan]:
            self.report(scope, argument.annotation, Code.INPUT_WRONG_TABLE_TYPE, _table_message(plan))
            return None
        return Input(table=table.kind, optional=optional, many=many)

    def _parameter(
        self,
        scope: _Scope,
        module: _Module,
        argument: ast.arg,
        default: ast.expr | None,
        inputs: dict[str, Input],
        roles: dict[str, str],
    ) -> dict[str, Json] | None:
        """Read a keyword-only parameter into its schema in the parameter profile, recording any role it marks.

        Example: `batch: Annotated[int, Minimum(1)] = 500` -> {"type": "integer", "minimum": 1, "default": 500}.
        """
        if not _is_identifier(argument.arg):
            self.report(scope, argument, Code.NAME_INVALID, f"{argument.arg} is not an identifier of the IR")
        if argument.annotation is None:
            self.report(scope, argument, Code.ANNOTATION_MISSING, "a parameter is annotated")
            return None
        kind = self.type_of(scope, module, argument.annotation)
        if kind is None:
            return None
        markers: tuple[_Marker, ...] = ()
        if isinstance(kind, _Annotated):
            kind, markers = kind.inner, kind.markers
        at = argument.annotation
        if _holds_table(kind):
            self.report(scope, at, Code.PARAMETER_TABLE_TYPE, "a table type marks an input, which comes before *")
            return None
        schema = self._schema(scope, at, kind, nested=False)
        if schema is None:
            return None
        if not self._apply_markers(scope, kind, markers, schema, inputs):
            return None
        for marker in markers:
            if marker.kind in _ROLES:
                if not _role_fits(marker.kind, kind, schema):
                    message = f"{marker.kind} marks {_ROLE_TARGETS[marker.kind]}"
                    self.report(scope, marker.node, Code.MARKER_NOT_ALLOWED, message)
                elif marker.kind in roles:
                    message = f"{marker.kind} marks one parameter of a node"
                    self.report(scope, marker.node, Code.ROLE_DUPLICATE, message)
                else:
                    roles[marker.kind] = argument.arg
        if default is not None:
            value = self._default(scope, module, default, kind)
            if value is _MISSING:
                return None
            problem = _violation(value, schema)
            if problem is not None:
                code = Code.DEFAULT_TYPE_MISMATCH if problem.startswith("is not") else Code.DEFAULT_VIOLATES_CONSTRAINT
                self.report(scope, default, code, f"the default {problem}")
                return None
            schema["default"] = value
        return schema

    def _schema(self, scope: _Scope, at: ast.expr, kind: _Type, *, nested: bool) -> dict[str, Json] | None:
        """Map a type onto the parameter profile; markers are applied to the outer type by the caller.

        Example: _Sequence(_Primitive("str")) -> {"type": "array", "items": {"type": "string"}}.
        """
        match kind:
            case _Primitive(kind=name):
                return dict(_PRIMITIVES[name])
            case _Literal(members=members, kind=member_kind):
                return {"type": "string" if member_kind == "str" else "integer", "enum": list(members)}
            case _Sequence(item=item):
                items = self._schema(scope, at, item, nested=True)
                return None if items is None else {"type": "array", "items": items}
            case _Mapping(value=value):
                values = self._schema(scope, at, value, nested=True)
                return None if values is None else {"type": "object", "additionalProperties": values}
            case _Annotated(inner=inner, markers=markers) if nested:
                schema = self._schema(scope, at, inner, nested=True)
                if schema is None:
                    return None
                for marker in markers:
                    if marker.kind not in _CONSTRAINTS:
                        message = f"{marker.kind} annotates a parameter, not the items or values of a collection"
                        self.report(scope, marker.node, Code.MARKER_NOT_ALLOWED, message)
                        return None
                return schema if self._apply_markers(scope, inner, markers, schema, {}) else None
            case _:
                self.report(
                    scope, at, Code.ANNOTATION_UNSUPPORTED, f"{ast.unparse(at)} has no counterpart in the profile"
                )
                return None

    def _apply_markers(
        self,
        scope: _Scope,
        kind: _Type,
        markers: tuple[_Marker, ...],
        schema: dict[str, Json],
        inputs: dict[str, Input],
    ) -> bool:
        """Add the constraints and formats of a parameter's markers to its schema; return False after an error.

        Example: `Column(of="data")` on a str parameter -> the schema gains {"format": "column", "of": "data"}.
        """
        seen: set[str] = set()
        formats = [m for m in markers if m.kind in _FORMATS]
        if len(formats) > 1:
            self.report(scope, formats[1].node, Code.MARKER_CONFLICT, "a parameter has at most one format")
            return False
        for marker in markers:
            if marker.kind in seen:
                self.report(scope, marker.node, Code.MARKER_DUPLICATE, f"{marker.kind} appears more than once")
                return False
            seen.add(marker.kind)
            if marker.kind in _ROLES:
                continue
            if not _marker_fits(marker.kind, kind):
                message = f"{marker.kind} annotates {_MARKER_TARGETS[marker.kind]}"
                self.report(scope, marker.node, Code.MARKER_NOT_ALLOWED, message)
                return False
            match marker.kind:
                case "Minimum":
                    schema["minimum"] = marker.args[0]
                case "Maximum":
                    schema["maximum"] = marker.args[0]
                case "Pattern":
                    schema["pattern"] = marker.args[0]
                case "Title":
                    schema["title"] = marker.args[0]
                case "Column" | "ColumnSelector":
                    source = marker.keywords["of"]
                    port = inputs.get(source)
                    if port is None:
                        message = f"{source} is not an input of this node"
                        self.report(scope, marker.node, Code.COLUMN_UNKNOWN_INPUT, message)
                        return False
                    if port.optional or port.many:
                        message = f"{source} must be a required input with a single edge"
                        self.report(scope, marker.node, Code.COLUMN_INVALID_INPUT, message)
                        return False
                    schema.pop("items", None)
                    schema["format"] = "column" if marker.kind == "Column" else "column_selector"
                    schema["of"] = source
                case "Binding" | "Secret":
                    schema["format"] = marker.kind.lower()
        return True

    def _default(self, scope: _Scope, module: _Module, default: ast.expr, kind: _Type) -> Json:
        """Evaluate a parameter's default statically, into the IR's data model.

        Example: `timedelta(days=7, hours=12)` -> "P7DT12H"; `date(2026, 1, 31)` -> "2026-01-31"; `(1, 2)` -> [1, 2].
        """
        if kind == _Primitive("datetime"):
            self.report(scope, default, Code.DEFAULT_NOT_ALLOWED, "a date-time parameter has no default")
            return _MISSING
        if kind in (_Primitive("date"), _Primitive("timedelta")):
            expected = "date" if kind == _Primitive("date") else "timedelta"
            if isinstance(default, ast.Call) and self.known(self.resolve(scope, module, default.func, ())) == expected:
                try:
                    args = [ast.literal_eval(a) for a in default.args]
                    keywords = {name: ast.literal_eval(k.value) for k in default.keywords if (name := k.arg)}
                    if expected == "date":
                        return datetime.date(*args, **keywords).isoformat()
                    duration = datetime.timedelta(*args, **keywords)
                except ValueError, TypeError, OverflowError:
                    self.report(scope, default, Code.DEFAULT_NOT_LITERAL, "the default is built from literals")
                    return _MISSING
                if duration < datetime.timedelta(0):
                    self.report(scope, default, Code.DEFAULT_VIOLATES_CONSTRAINT, "a duration is not negative")
                    return _MISSING
                return _duration(duration)
            message = f"the default is written {expected}(...) with literal arguments"
            self.report(scope, default, Code.DEFAULT_TYPE_MISMATCH, message)
            return _MISSING
        try:
            value = ast.literal_eval(default)
        except ValueError:
            self.report(scope, default, Code.DEFAULT_NOT_LITERAL, "the default is a literal")
            return _MISSING
        return _json(value)

    def _outputs(
        self, scope: _Scope, module: _Module, function: ast.FunctionDef, plan: str | None
    ) -> tuple[dict[str, Output], dict[str, dict[str, Json]]]:
        """Read a node's return annotation into its output ports and value outputs.

        Example: `-> pa.Table` -> ({"data": Output("arrow")}, {}); `-> None` -> ({}, {}).
        """
        if function.returns is None:
            self.report(scope, function, Code.ANNOTATION_MISSING, "a node's return type is annotated")
            return {}, {}
        kind = self.type_of(scope, module, function.returns)
        match kind:
            case None:
                return {}, {}
            case _NoneType():
                return {}, {}
            case _Table(kind=table):
                if table not in _TABLES_OF_PLAN[plan]:
                    self.report(scope, function.returns, Code.OUTPUT_WRONG_TABLE_TYPE, _table_message(plan))
                return {"data": Output(table=table)}, {}
            case _Class(module=class_module, node=node):
                return self._output_class(scope, class_module, node, plan)
            case _:
                message = "a node returns one table, an output class or None"
                self.report(scope, function.returns, Code.OUTPUT_UNSUPPORTED, message)
                return {}, {}

    def _output_class(
        self, scope: _Scope, module: _Module, node: ast.ClassDef, plan: str | None
    ) -> tuple[dict[str, Output], dict[str, dict[str, Json]]]:
        """Read the frozen dataclass a node returns into its output ports and value outputs.

        Example: fields `data: ibis.Table` and `removed: Value[int]` -> ({"data": Output("ibis")},
        {"removed": {"type": "integer"}}).
        """
        class_scope = _Scope(module, scope.node)
        if not any(self._is_frozen_dataclass(class_scope, module, d) for d in node.decorator_list):
            message = f"{node.name} is a dataclass declared with frozen=True"
            self.report(class_scope, node, Code.OUTPUT_CLASS_NOT_FROZEN_DATACLASS, message)
            return {}, {}
        outputs: dict[str, Output] = {}
        values: dict[str, dict[str, Json]] = {}
        for statement in node.body:
            if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
                continue
            name = statement.target.id
            field_scope = _Scope(module, scope.node, name)
            if not _is_identifier(name):
                self.report(field_scope, statement, Code.NAME_INVALID, f"{name} is not an identifier of the IR")
            if statement.value is not None:
                self.report(field_scope, statement.value, Code.OUTPUT_CLASS_FIELD_DEFAULT, "an output has no default")
                continue
            kind = self.type_of(field_scope, module, statement.annotation)
            match kind:
                case None:
                    continue
                case _Table(kind=table):
                    if table not in _TABLES_OF_PLAN[plan]:
                        message = _table_message(plan)
                        self.report(field_scope, statement.annotation, Code.OUTPUT_WRONG_TABLE_TYPE, message)
                    outputs[name] = Output(table=table)
                case _Value(inner=inner):
                    markers: tuple[_Marker, ...] = ()
                    if isinstance(inner, _Annotated):
                        inner, markers = inner.inner, inner.markers
                    schema = self._schema(field_scope, statement.annotation, inner, nested=False)
                    if schema is None:
                        continue
                    for marker in markers:
                        if marker.kind not in _CONSTRAINTS:
                            message = f"{marker.kind} does not annotate a value output"
                            self.report(field_scope, marker.node, Code.MARKER_NOT_ALLOWED, message)
                            schema = None
                            break
                    if schema is not None and self._apply_markers(field_scope, inner, markers, schema, {}):
                        values[name] = schema
                case _:
                    message = "an output-class field is a table type or Value[...]"
                    self.report(field_scope, statement.annotation, Code.OUTPUT_CLASS_INVALID_FIELD, message)
        return outputs, values

    def _is_frozen_dataclass(self, scope: _Scope, module: _Module, decorator: ast.expr) -> bool:
        if not isinstance(decorator, ast.Call):
            return False
        if self.known(self.resolve(scope, module, decorator.func, ())) != "dataclass":
            return False
        frozen = [k for k in decorator.keywords if k.arg == "frozen"]
        return bool(frozen) and isinstance(frozen[0].value, ast.Constant) and frozen[0].value.value is True


_MISSING: Any = object()


def _diagnostic(scope: _Scope, at: ast.AST, code: Code, message: str) -> Diagnostic:
    line = getattr(at, "lineno", 1)
    column = getattr(at, "col_offset", 0) + 1
    return Diagnostic(scope.module.path, line, column, scope.node, scope.field, code, message)


_MARKER_TARGETS = {
    "Minimum": "an int or float parameter",
    "Maximum": "an int or float parameter",
    "Pattern": "a str parameter",
    "Title": "any parameter",
    "Column": "a str parameter",
    "ColumnSelector": "a Sequence[str] parameter",
    "Binding": "a str parameter",
    "Secret": "a str parameter",
}
_ROLE_TARGETS = {
    "Grouping": "a Column or ColumnSelector parameter",
    "Order": "a Column or ColumnSelector parameter",
    "Seed": "an int parameter",
    "SideEffectTarget": "a Binding parameter",
}


def _marker_fits(marker: str, kind: _Type) -> bool:
    match marker:
        case "Minimum" | "Maximum":
            return kind in (_Primitive("int"), _Primitive("float"))
        case "Pattern" | "Column" | "Binding" | "Secret":
            return kind == _Primitive("str")
        case "ColumnSelector":
            return kind == _Sequence(_Primitive("str"))
        case _:
            return True


def _role_fits(role: str, kind: _Type, schema: dict[str, Json]) -> bool:
    match role:
        case "Grouping" | "Order":
            return schema.get("format") in ("column", "column_selector")
        case "Seed":
            return kind == _Primitive("int")
        case _:
            return schema.get("format") == "binding"


def _holds_table(kind: _Type) -> bool:
    match kind:
        case _Table():
            return True
        case _Optional(inner=inner) | _Sequence(item=inner):
            return _holds_table(inner)
        case _:
            return False


def _table_message(plan: str | None) -> str:
    allowed = " or ".join(_TABLE_NAMES[k] for k in _TABLES_OF_PLAN[plan])
    return f"{_PLAN_NAMES[plan] if plan else 'eager code'} takes and returns {allowed}"


def _is_type_checking(test: ast.expr) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _is_identifier(name: str) -> bool:
    return bool(_IDENTIFIER.match(name)) and name not in _NOT_IDENTIFIERS


def _literal_or_none(expression: ast.expr) -> Any:
    try:
        return ast.literal_eval(expression)
    except ValueError:
        return None


def _decorator_problem(argument: str, value: Any) -> str | None:
    match argument:
        case "plan":
            return None if value in ("ibis", "polars") else 'plan is "ibis" or "polars"'
        case "version":
            ok = isinstance(value, int) and not isinstance(value, bool) and value >= 1
            return None if ok else "version is an integer of at least 1"
        case "title":
            return None if isinstance(value, str) else "title is a string"
        case "tags":
            if not isinstance(value, list | tuple) or not all(isinstance(t, str) and _is_identifier(t) for t in value):
                return "tags is a list of identifiers"
            return None if len(set(value)) == len(value) else "tags are distinct"
        case "gpu":
            return None if value in ("none", "supported", "required") else 'gpu is "none", "supported" or "required"'
        case "memory_class":
            ok = value in ("streaming", "blocking_spilling", "blocking_non_spilling")
            return None if ok else 'memory_class is "streaming", "blocking_spilling" or "blocking_non_spilling"'
        case "memory_floor":
            ok = isinstance(value, str) and bool(_MEMORY_FLOOR.match(value))
            return None if ok else 'memory_floor is a quantity such as "1Gi"'
        case _:
            ok = isinstance(value, list | tuple) and all(isinstance(d, str) and _is_identifier(d) for d in value)
            return None if ok else "dialects is a list of identifiers"


def _docstring(text: str | None) -> tuple[str | None, dict[str, str]]:
    """Split a Google-style docstring into the description without its Args section and the arguments'."""
    if not text:
        return None, {}
    lines = text.splitlines()
    descriptions: dict[str, str] = {}
    kept: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() in ("Args:", "Arguments:") and not lines[index].startswith(" "):
            index += 1
            current: str | None = None
            indent: int | None = None
            while index < len(lines) and (not lines[index].strip() or lines[index].startswith(" ")):
                line = lines[index]
                index += 1
                if not line.strip():
                    continue
                depth = len(line) - len(line.lstrip())
                indent = depth if indent is None else indent
                entry = re.match(r"^(\w+)\s*(?:\([^)]*\))?:\s*(.*)$", line.strip())
                if depth == indent and entry:
                    current = str(entry.group(1))
                    descriptions[current] = str(entry.group(2))
                elif current is not None:
                    descriptions[current] = f"{descriptions[current]} {line.strip()}".strip()
            continue
        kept.append(lines[index])
        index += 1
    description = "\n".join(kept).strip()
    return description or None, descriptions


def _duration(value: datetime.timedelta) -> str:
    seconds = value.total_seconds()
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, rest = divmod(rest, 60)
    text = "P" + (f"{int(days)}D" if days else "")
    clock = (f"{int(hours)}H" if hours else "") + (f"{int(minutes)}M" if minutes else "")
    clock += f"{rest:g}S" if rest else ""
    return text + ("T" + clock if clock else "") if days or clock else "PT0S"


def _json(value: Any) -> Json:
    if isinstance(value, tuple):
        return [_json(v) for v in value]
    if isinstance(value, list):
        return [_json(v) for v in value]
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    return value


def _violation(value: Json, schema: dict[str, Json]) -> str | None:
    """State how a default breaks a parameter schema: starting with "is not" for a wrong type."""
    kind = schema["type"]
    checks = {
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, int | float) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict) and all(isinstance(k, str) for k in value),
    }
    if not checks[kind]:
        return f"is not of type {kind}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{value!r} is not one of {schema['enum']}"
    if "minimum" in schema and value < schema["minimum"]:
        return f"{value!r} is below the minimum {schema['minimum']}"
    if "maximum" in schema and value > schema["maximum"]:
        return f"{value!r} is above the maximum {schema['maximum']}"
    if "pattern" in schema and isinstance(value, str) and not re.search(schema["pattern"], value):
        return f"{value!r} does not match the pattern {schema['pattern']}"
    members: list[Json] = []
    member_schema: dict[str, Json] = {}
    if isinstance(value, list) and "items" in schema:
        members, member_schema = list(value), schema["items"]
    elif isinstance(value, dict):
        members, member_schema = list(value.values()), schema["additionalProperties"]
    for member in members:
        problem = _violation(member, member_schema)
        if problem is not None:
            return problem
    return None
