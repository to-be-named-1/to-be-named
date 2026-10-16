# 19. Stable dataset identity

Date: 2026-10-11
Applies to: platform.controlPlane

## Status

Accepted

## Context

**Fixed dataset names** (D19). Simpler than renames with aliases; the immutable ID keeps future renames possible without migration.

## Decision

Dataset names are fixed in the first release: a dataset cannot be renamed or moved to another project. Every dataset also carries an immutable internal identifier, which lineage, bindings, consumer registrations, provenance and cache keys reference, so that renaming can be introduced later without migration.

- **Structure.** Names take the form `project.path.name`, for example `analytics.curated.customers`. The project segment is the namespace and permission boundary; intermediate segments are free-form and follow the project's own conventions. Within its project a dataset may be referred to by its short name.
- **Rules.** Lowercase letters, digits and underscores, separated by dots, with a length limit. Uniqueness is case-insensitive.
- **Display title.** A mutable display title covers cosmetic changes without affecting the name used in definitions.
- **No reuse.** The name of a deleted dataset is never reused automatically; reuse requires explicit administrator confirmation. This prevents a workflow from silently reading a different dataset under a familiar name.
- **Scope.** The same rules apply to workflows. Projects carry display titles, since teams are renamed more often than datasets.
- **Later.** Renames with aliases, reference-updating tooling and transfers between projects are deferred, and can be added because identity is already separate from name.

## Follow-ups

- Renames with aliases and transfers between projects.
