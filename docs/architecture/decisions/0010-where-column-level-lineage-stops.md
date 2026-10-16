# 10. Where column-level lineage stops

Date: 2026-10-11
Applies to: platform.controlPlane, platform.webApp, workflowAuthor

## Status

Accepted

## Decision

Column-level lineage is derived for SQL and built-in declarative nodes, whose transformation logic can be parsed. Across custom code nodes lineage is task-level only, and the interface shows it as such rather than implying finer detail.

- **Declared mappings.** The author of a custom code node may declare column mappings by hand. The interface labels these as **declared** rather than **derived**, since the platform cannot verify them.
- **Direct only.** Derived lineage covers direct transformations, where an output column's values are computed from identified input columns.
