# 58. Behavior follows properties

Date: 2026-10-26
Applies to: platform

## Status

Accepted

Amends [7. Reproducibility guarantee](0007-reproducibility-guarantee.md)
Amends [17. Dataset families and first-release scope](0017-dataset-families-and-first-release-scope.md)
Amends [32. Execution unit structure](0032-execution-unit-structure.md)
Amends [41. IR text form, round-trip and structure](0041-ir-text-form-round-trip-and-structure.md)
Amends [49. Source probes](0049-source-probes.md)

## Context

[D57](0057-node-type-contract.md) made built-in node types, plugins and code nodes follow one path: a built-in node type is a node type the platform publishes. Several earlier decisions still set rules by where something comes from: a reproducibility default for custom code nodes ([D7](0007-reproducibility-guarantee.md)), column lineage only for SQL and built-in declarative nodes ([D10](0010-where-column-level-lineage-stops.md)), sandboxing for third-party plugins ([D17](0017-dataset-families-and-first-release-scope.md)), engines that users may not choose for built-in nodes ([D25](0025-processing-engines-and-runtimes.md)), the condition on which a code node shares a unit with built-in nodes ([D32](0032-execution-unit-structure.md)), native probes for built-in source kinds ([D49](0049-source-probes.md)), and a read-only canvas for workflows from the SDK ([D41](0041-ir-text-form-round-trip-and-structure.md)).

Rules keyed on origin cannot be enforced where fusion places the platform's code and an author's code in one process: part of a process cannot be isolated, or vouched for, differently from the rest. Every capability reserved to the platform's own node types is one that authors' code and plugins cannot have, although the palette grows through plugins. Behavior that depends on where something comes from also multiplies the cases that must be built, tested and explained.

## Decision

The behavior of anything in the platform follows from its properties, never from where it comes from.

- **Properties, not origin.** Behavior depends on what a thing declares, what the platform derives from it, what is measured of it, or what a policy grants it. Whether the platform, a plugin's publisher or an author wrote it is not a property.
- **Trust as a property.** Where trust legitimately differs, it enters as an explicit property applied alike to everything that has it, such as a signature on an image, a publisher an installation allows, or the isolation policy of a pool. The platform's own images meet such a rule by having the property, not by being the platform's.
- **One kind at a time.** The rule compares things of one kind. The platform's own services, the control plane, the agent and the maintenance units, are not nodes and are not held to the rules for nodes.
- **Stated asymmetries.** A rule that treats two things of one kind differently names the property that differs, where the rule is recorded.
- **Each capability keyed on what it needs.** No single category gates every capability:
  - pushdown, fusion into one query and eligibility for an engine need a plan ([D57](0057-node-type-contract.md));
  - an output schema before the run needs a plan, which derives it, or an annotation ([D41](0041-ir-text-form-round-trip-and-structure.md));
  - the memory class is derived where it can be, and otherwise defaulted, hinted or measured ([D34](0034-capacity-and-size.md));
  - column lineage needs a representation the platform can analyze, and otherwise is declared or task-level ([D59](0059-column-lineage.md));
  - Reproducible needs a passing verification, within the ceiling that static properties prove ([D7](0007-reproducibility-guarantee.md));
  - isolation follows the policy of the pool and tenant, the same for all code in one unit;
  - nodes share a unit when one image serves them all ([D32](0032-execution-unit-structure.md));
  - the engine is chosen by the planner, or by an override among the engines a node is eligible for ([D57](0057-node-type-contract.md));
  - a document is read-only on the canvas when it is marked as generated, whatever generated it ([D41](0041-ir-text-form-round-trip-and-structure.md)).
- **Asymmetries kept.** Each follows from a property: development runs fall back to production bindings for reads their environment does not define, but execute side effects only where their own environment binds the target, by what a node does ([D50](0050-development-mode.md)); a draft may raise governed protection but never lower it, by the direction of the change ([D45](0045-isolation-enforcement-and-role-model.md)); adopted files are referenced read-only and never deleted unless their retention is handed over, by who owns them ([D51](0051-adoption-of-existing-data.md)); a storage target with its own commit is published by a further commit after the platform's, by the kind of target ([D15](0015-atomic-publication.md), [D55](0055-commits-to-table-format-storage-targets.md)); a node is renamed through a hint while workflows and datasets keep fixed names, by what carries their identity ([D19](0019-stable-dataset-identity.md), [D56](0056-ir-documents-and-identifiers.md)); and names without a qualifier are reserved to the platform's node types and format types, by who assigns names, so that publishers' names cannot collide with them, while nothing behaves differently because of it ([D56](0056-ir-documents-and-identifiers.md), [D57](0057-node-type-contract.md)).
- **Amends.** [D7](0007-reproducibility-guarantee.md): every node is at most Re-executable until a verification passes. [D17](0017-dataset-families-and-first-release-scope.md): family plugins are isolated as all code in units is. [D32](0032-execution-unit-structure.md): nodes share a unit when one image serves them all, whoever wrote them. [D41](0041-ir-text-form-round-trip-and-structure.md): a document marked as generated is read-only on the canvas, whatever generated it. [D49](0049-source-probes.md): faster probes, if needed, serve every source kind alike, in place of native probes for built-in kinds.

## Consequences

- A proposed rule is checked by naming the property its behavior depends on; a rule that can name only an origin is rewritten or rejected.
- The platform's node types receive no capability that a plugin or an author's code with the same properties lacks.

## Rejected alternatives

- Applying the rule case by case without recording it. Each decision would have to restate it, and departures would go unnoticed.
- Trust by origin. It cannot be enforced inside a fused unit, and would prevent fusing code of different origins.

## Follow-ups

- How a document is marked as generated, with the writers' canonical form (design agenda).
- Isolation policies of pools and tenants, with the sandboxing of untrusted containers ([CORE 7.6]({workspace}/documentation#3), design agenda).
