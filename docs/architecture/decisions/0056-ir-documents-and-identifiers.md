# 56. IR documents and identifiers

Date: 2026-10-23
Applies to: platform.webApp, platform.controlPlane

## Status

Accepted

Amends [41. IR text form, round-trip and structure](0041-ir-text-form-round-trip-and-structure.md)
Amends [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amended by [57. Node-type contract](0057-node-type-contract.md)

## Context

[D3](0003-ir-and-execution-engines.md) requires a formal specification of the IR with a version from the start, and [D41](0041-ir-text-form-round-trip-and-structure.md) fixes its text form, its repository layout and how it is versioned, leaving the detail to that specification. Its first part concerns what every committed document shares: how a file declares what it is and which version of the format it follows, how the entities inside it are named and keep their identity, and exactly which YAML is accepted.

Git remains authoritative for git-connected projects and the text is written for people to read, review and edit ([D41](0041-ir-text-form-round-trip-and-structure.md), [D45](0045-isolation-enforcement-and-role-model.md)). Keeping definitions in the platform with a one-way export to git was reconsidered and not taken: round-tripping between the canvas and text in git ([CORE 1.6]({workspace}/documentation#3)), linting and testing every change in CI ([MLE 6.1]({workspace}/documentation#6)), promotion across environments ([MLE 6.2]({workspace}/documentation#6)) and standard data-engineering practice ([D36](0036-data-engineering-practice-first-reproducibility-by-choice.md)) all rest on authors and reviewers working with the files in git. The format therefore has to stay readable, writable by hand and merge-friendly, while every tool that reads a file must find the same values in it.

## Decision

The envelope, versioning, keys, identifiers, identity, collections, data model and schema of every IR document. The normative detail is stated in the IR specification (`docs/ir/`) and its machine-readable schema.

- **Documents.** A project commits five kinds of IR document: `project` (`project.yaml`), `workflow` (`workflows/<name>.yaml`), `layout` (the sidecar `workflows/<name>.layout.yaml`), `dataset` (`datasets/<path>.yaml`) and `environment` (`environments/<env>.yaml`). Files under `code/` are referenced by path and are not IR documents. Node-type documents, of kind `node_type`, are not committed by projects ([D57](0057-node-type-contract.md)). Only the extension `.yaml` is used.
- **Envelope.** Every document begins with two keys, `ir_version` and `kind`, followed by the fields of its kind at the top level. The kind of a project document must match its location, so that a single file can be validated on its own and a misplaced file is an error.
- **IR version.** The version of the document format is called the IR version, kept apart from node-type versions, workflow versions, the key-schema version and the unit specification ([D8](0008-cache-keying.md), [D40](0040-protocol-between-the-control-and-data-planes.md), [D41](0041-ir-text-form-round-trip-and-structure.md)). It is a single integer. Once an IR version is frozen its format never changes: any change, additive or not, produces the next version. A reader refuses a document whose IR version is newer than the newest it supports; an older document within the supported window is validated against its own version's schema and migrated on read ([D41](0041-ir-text-form-round-trip-and-structure.md)).
- **Keys.** Keys defined by the specification are snake_case, so that they can be selected in CEL. A reader rejects any key the specification does not define for its position, which catches misspellings. Keys defined by the specification and the names of built-in node and format types are identifiers, which never contain `.` or `/`, so names qualified by a publisher can be added for plugins later without colliding with them ([S26]({workspace}/documentation#7.25)).
- **Identifiers.** Names chosen for nodes, parameters, value outputs, carried values, workflows, environments and dataset path segments match `[a-z][a-z0-9_]{0,62}` and are none of the CEL keywords and reserved words, nor `y`, `n`, `yes`, `no`, `on` or `off`, which some YAML parsers read as booleans. Lowercase avoids collisions on file systems that ignore case. A node may carry a free-text `title`, shown in place of its key.
- **Generated keys.** Authors never have to type a node key. The canvas generates it from the node type, or from the title once one is given, keeping only the allowed characters and appending `_2`, `_3` on a collision or a reserved word; the SDK derives it from the author's own names. Until the node is first deployed its key follows its title; afterwards it changes only by an explicit refactor.
- **Node identity and renames.** Node keys are unique within a workflow, frames included, since expressions reference them as `outputs.<node>`. A rename rewrites every reference, and the renamed node carries `renamed_from`, naming its key in the deployed version; the field is not part of the semantic model. Deployment uses it to carry the node's identity in the platform, so that per-node statistics, run history and pinned-plan comparison continue across the rename, and the three-way merge uses it to rewrite references made on another branch. Until the rename is deployed, no other node of the workflow may take the old key; once it is deployed, the hint is dropped. A reference left with the old key is an error naming the new one, never an alias.
- **Workflow, dataset and environment identity.** A workflow, dataset or environment is named by its path. The platform assigns it an immutable internal identifier at first deployment, which history, lineage, cache keys and schedules reference, and never writes it into the file, following [D19](0019-stable-dataset-identity.md). A file moved in git is a removal and an addition, of which deployment warns.
- **Collections.** A collection of entities is a mapping keyed by identifier ([D44](0044-minimum-technology-stack.md)). A collection whose order carries meaning, such as a schema's columns or a dataset's partition keys, is a list whose items carry a `name`, unique within the list, by which comments and merges address them. The order of a mapping's entries carries no meaning.
- **Data model and YAML subset.** Every document decodes to the data model of I-JSON (RFC 7493), so that it converts to JSON without loss. A document is one YAML document in UTF-8, without anchors, aliases, merge keys, tags, directives or keys that are not strings. Unquoted values are typed by the specification, not by the parser, through a closed rule: an unquoted value beginning with a digit, a sign or a point must be a decimal integer or number; the words parsers read as booleans or null must be lowercase `true`, `false` or `null`; every other unquoted value is a string. Every value that parsers type in different ways falls under the first two parts, so values such as `no`, `012`, `1e3` or a date are quoted. Integers stay within ±(2^53−1), since the canvas runs in a browser. Writers quote such values themselves.
- **Schema.** The structure of each kind is defined by JSON Schema 2020-12, normative for structure while the specification's prose is normative for meaning. The schema belongs to the authoring context of the control plane, which embeds it and validates every committed version and every draft. The web application and the CLI reach it through the control plane, and the SDK uses the schema published with each release. Schemas carry no `$id` and documents no `$schema`. A document is checked in three layers: the YAML subset on the syntax tree, then the schema of its IR version, then the semantic checks of the compiler ([D47](0047-control-plane-structure.md)).
- **Amends.** [D41](0041-ir-text-form-round-trip-and-structure.md): the text form's data model and the typing of its values, node keys generated and renamed as above, and the IR version as the name of the document format's version. [D44](0044-minimum-technology-stack.md): a collection whose order carries meaning is a list whose items carry a unique name.

## Consequences

- The compiler builds each document's value from the YAML syntax tree itself and reports subset errors, schema errors and semantic errors in one form, with the line and the fix.
- A conformance corpus of valid and invalid documents accompanies the schema and is checked on every change.
- A rename made by hand in git keeps a node's identity only if its author adds `renamed_from`.

## Rejected alternatives

- JSON as the text form. It would remove the quoting rules, but not the strict reading: Go's `encoding/json` accepts a duplicated key by keeping the last value and rounds integers beyond 2^53 without an error. It would cost every author and reviewer comments, multi-line expressions and merge-friendly diffs, since adding a last entry changes the line before it.
- Typing values as a YAML 1.2 parser does. goccy/go-yaml follows neither YAML 1.1 nor 1.2 throughout, reading `012` as octal and `1e3` as a string, and YAML 1.1 parsers read `yes` and dates differently again, so the same file would hold different values in different tools.
- A header and body envelope (`metadata`, `spec`). It adds a level of nesting to every document and noise to every diff.
- The IR version in `project.yaml` only, with the kind taken from the path. Files could not be validated alone or copied between projects, and a project could not hold several versions during a migration.
- A `major.minor` IR version, with older readers accepting newer minor versions by ignoring unknown keys. It conflicts with rejecting unknown keys, which catches misspellings.
- camelCase or kebab-case keys. Kebab-case cannot be selected in CEL; snake_case suits authors who write Python and SQL.
- Generated node identifiers with author-chosen names as aliases. Expressions must reference something readable, so the name would have to be unique and stable anyway, and renaming it would still rewrite every reference; files would carry two identifiers per node.
- Generated identifiers written into workflow and dataset files. A copied file would duplicate its identity, and the platform would have to commit into authors' files.
- Node keys following their titles permanently. Every edit of a title would rewrite references and block the old name.
- Detecting renames at deployment by similarity of type, parameters and edges. It is unreliable and invisible to the author.
- Ordered collections as mappings relying on the order of their entries. YAML and JSON define mappings as unordered, so meaning cannot rest on that order.

## Follow-ups

- Names qualified by a publisher for the node types, format types and document keys that plugins provide ([S26]({workspace}/documentation#7.25)).
- Allowing a renamed node's old key to be reused before the rename is deployed, with the compiler rejecting references that existed in the deployed version and would now bind to a different node, and listing newly added ones for review.
- Renaming workflows and datasets through the same hint, once their names are no longer fixed ([D19](0019-stable-dataset-identity.md)).
