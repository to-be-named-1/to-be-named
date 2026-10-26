# Documents

What every IR document shares: its kind, its envelope and IR version, the form of its keys, the identifiers authors choose, how entities keep their identity, and how collections are written ([D56](../architecture/decisions/0056-ir-documents-and-identifiers.md)).

## Kinds of document

There are two classes of IR document: the project documents, which a project commits, and node-type documents.

A project commits five kinds of project document, each at a fixed location ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)):

| Kind | Location | Holds |
|---|---|---|
| `project` | `project.yaml` | The project's configuration, including its reproducibility setting ([D36](../architecture/decisions/0036-data-engineering-practice-first-reproducibility-by-choice.md)) |
| `workflow` | `workflows/<name>.yaml` | One workflow, with its schedule and logical interval ([D13](../architecture/decisions/0013-partitioning-intervals-and-dataset-ownership.md)) |
| `layout` | `workflows/<name>.layout.yaml` | The canvas layout of the workflow of the same name; never part of the semantic model |
| `dataset` | `datasets/<path>.yaml` | One dataset declaration |
| `environment` | `environments/<env>.yaml` | The bindings of one environment |

`<name>` and `<env>` are identifiers, and `<path>` is one or more identifiers separated by `/`. Files under `code/` are referenced by path from workflows and are not IR documents.

A **node-type document**, of kind `node_type`, describes one version of a node type ([Node types](03-node-types.md)). Projects do not commit node-type documents; they belong to the platform's catalog of built-in node types and to plugins, and the rule of locations does not apply to them.

A document file MUST have the extension `.yaml`. A reader MUST NOT treat a file with any other extension, such as `.yml`, as an IR document.

## Envelope

Every document MUST contain the keys `ir_version` and `kind`. The fields of its kind follow at the top level, beside them.

- `ir_version` is the document's IR version.
- `kind` is one of the six kinds above. The kind of a project document MUST match its location; a reader MUST reject a project document whose kind does not.

Writers MUST write `ir_version` and `kind` first, in that order. Readers MUST NOT depend on the order of keys.

```yaml
ir_version: 0
kind: workflow
```

## IR version

The IR version is the version of the document format, distinct from node-type versions, workflow versions, the key-schema version and the version of the unit specification ([D8](../architecture/decisions/0008-cache-keying.md), [D40](../architecture/decisions/0040-protocol-between-the-control-and-data-planes.md), [D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)).

- It is a non-negative integer.
- Once an IR version is frozen, its format never changes: any change, additive or not, produces the next IR version.
- A reader MUST reject a document whose IR version is newer than the newest it supports, stating that a newer platform is needed.
- A reader supports a window of older IR versions. It MUST validate a document of an older version against that version's schema before migrating it to the newest version ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)).
- A migrated document is written back only by an explicit commit, never by rewriting the repository silently ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)).

## Keys

- Every key the specification defines is snake_case, so that it can be selected in CEL.
- A reader MUST reject a key the specification does not define for its position.
- Keys the specification defines are identifiers, and so never contain `.` or `/`; neither do the names of built-in node types and format types.

## Identifiers

An **identifier** is a name chosen for a node, a parameter, a value output, a carried value, a workflow, an environment or a segment of a dataset path. An identifier:

- MUST match `[a-z][a-z0-9_]{0,62}`: a lowercase letter, then up to 62 lowercase letters, digits or underscores. Lowercase avoids collisions on file systems that ignore case.
- MUST NOT be one of the CEL keywords and reserved words, `false`, `in`, `null`, `true`, `as`, `break`, `const`, `continue`, `else`, `for`, `function`, `if`, `import`, `let`, `loop`, `package`, `namespace`, `return`, `var`, `void` and `while`, which CEL does not accept where identifiers are expected.
- MUST NOT be `y`, `n`, `yes`, `no`, `on` or `off`, which some YAML parsers read as booleans when they appear as keys.

A node MAY carry a `title`, free text shown in place of its key.

### Generated keys

Authors are never required to type a node key. A writer that creates a node generates its key:

1. From the title if one is given, otherwise from the node type's name.
2. Lowercased, with every run of characters outside `[a-z0-9]` replaced by one underscore, and leading and trailing underscores removed.
3. Prefixed with the node type's name, normalized as in step 2, if the result is empty or does not begin with a letter.
4. Suffixed with `_2`, `_3` and so on, the first that makes it unique, if it equals another node's key, an excluded word or a key reserved by a pending rename.
5. Shortened before any suffix, so that the key with its suffix has at most 63 characters.

Until the node is first deployed, a writer MAY regenerate its key whenever its title changes, rewriting every reference. Once the node has been deployed, its key changes only through an explicit rename.

Keys written by hand need only satisfy the rules for identifiers.

## Identity

### Nodes

A node's key is unique within its workflow, including the nodes inside frames, since expressions reference value outputs as `outputs.<node>.<value>` ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)).

A **rename** changes a deployed node's key. It rewrites every reference to the node, in expressions, edges and the layout, and adds `renamed_from` to the node:

- `renamed_from` names the node's key in the deployed version of the workflow, even after several renames before deployment.
- It is not part of the semantic model and never affects cache keys.
- Deployment uses it to carry the node's identity in the platform, so that the node's history, statistics and plan comparisons continue under the new key. The three-way merge uses it to rewrite references to the old key made on another branch.
- Until the rename is deployed, no other node of the workflow may take the key named in `renamed_from`.
- A `renamed_from` that names no key of the deployed version has no effect, and a reader SHOULD report it as a note. Once the rename is deployed, writers drop it.

A reader MUST treat a reference to a key that no node has as an error, and SHOULD name the node whose `renamed_from` matches it. It MUST NOT resolve the reference through `renamed_from`.

A node renamed by hand keeps its identity only if `renamed_from` is added.

### Workflows, datasets and environments

A workflow, dataset or environment is named by its location. The platform assigns it an immutable internal identifier when it is first deployed, which history, lineage, cache keys and schedules reference, and never writes that identifier into the document ([D19](../architecture/decisions/0019-stable-dataset-identity.md)). A document moved to another location is a removal and an addition: its history does not follow it, and deployment warns of this.

## Collections

A collection of entities, such as a workflow's nodes or parameters, is a mapping keyed by identifier ([D44](../architecture/decisions/0044-minimum-technology-stack.md)). The order of a mapping's entries carries no meaning: a reader MUST NOT derive meaning from it.

A collection whose order carries meaning, such as a schema's columns or a dataset's partition keys, is a list whose items each carry a `name`, an identifier unique within the list. Merges and comments address an item by its `name`.

A list of plain values, such as the columns of a sort key, is a plain list.

## Validation

A reader checks a document in three layers, and reports every error with its line:

1. The YAML subset, on the YAML syntax tree ([YAML subset](02-yaml-subset.md)).
2. The schema of the document's IR version.
3. The semantic checks of the compiler, such as references between nodes, the kind against the location, uniqueness of `name` within lists, and expressions ([D47](../architecture/decisions/0047-control-plane-structure.md)).
