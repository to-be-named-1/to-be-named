# IR specification

The intermediate representation (IR) is the platform's description of the work to be done: the files a project commits, which the canvas edits, the compiler reads and git holds ([D3](../architecture/decisions/0003-ir-and-execution-engines.md), [D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)). This specification states their normative detail. The decisions in the architecture record (`docs/architecture/decisions/`) state the choices and their reasons; this specification cites them and never contradicts them, and where the two disagree the decision prevails until it is amended.

This specification describes IR version 0.

## Contents

| Chapter | Covers |
|---|---|
| [Documents](01-documents.md) | The kinds of document, the envelope, the IR version, keys, identifiers, identity and collections |
| [YAML subset](02-yaml-subset.md) | The data model, the YAML accepted, the typing of unquoted values, and numbers |
| [Node types](03-node-types.md) | Node-type documents, languages and plans, ports, parameters and expressions in them, value outputs, execution properties and code nodes |

## Machine-readable schema

The structure of each kind of document is defined by JSON Schema 2020-12, in [`controlplane/internal/authoring/ir/schema/`](../../controlplane/internal/authoring/ir/schema/), one folder per IR version. The schema is normative for structure and this specification for meaning; a disagreement between them is a defect in one of them. The control plane embeds the schema; the web application and the CLI reach it through the control plane, and the SDK uses the schema published with each release ([D56](../architecture/decisions/0056-ir-documents-and-identifiers.md)).

A conformance corpus of valid and invalid documents, in [`controlplane/internal/authoring/ir/conformance/`](../../controlplane/internal/authoring/ir/conformance/), accompanies the schema. `make ir-check` confirms that every schema compiles, that every valid document passes and that every document under `invalid/schema/` fails. Documents under `invalid/subset/` break the YAML subset, which a JSON Schema validator cannot see; the compiler's tests check them. `writer/strings.json` lists strings that every writer MUST write so that a reader reads them back unchanged and the document passes the YAML subset; the writers' tests check them.

## Conformance language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to be interpreted as described in BCP 14 ([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174)) when, and only when, they appear in all capitals, as shown here.

A **reader** is any implementation that parses IR documents, such as the compiler. A **writer** is any implementation that produces them, such as the canvas and the SDK.

## Scope

The specification covers every file a project commits as IR and what a document means when it runs. It does not cover the unit specification sent to agents ([D40](../architecture/decisions/0040-protocol-between-the-control-and-data-planes.md)), the platform's API, the catalog's storage or the canvas's user interface.
