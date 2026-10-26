# 10. Where column-level lineage stops

Date: 2026-10-11
Applies to: platform.controlPlane, platform.webApp, workflowAuthor

## Status

Accepted

Amended by [59. Column lineage](0059-column-lineage.md)

## Decision

Column-level lineage is derived wherever the work of a node has a representation the platform can analyze, and is otherwise declared or task-level ([D59](0059-column-lineage.md)). Where it is task-level, the interface shows it as such rather than implying finer detail.

- **Declared mappings.** Column mappings may be declared by hand for any node, on its type, in its code or on the node itself ([D59](0059-column-lineage.md)). The interface labels these as **declared** rather than **derived**, since the platform cannot verify them.
- **Direct only.** Derived lineage covers direct transformations, where an output column's values are computed from identified input columns.
