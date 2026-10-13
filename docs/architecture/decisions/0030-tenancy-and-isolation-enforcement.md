# 30. Tenancy and isolation enforcement

Date: 2026-10-11
Applies to: platform.controlPlane, platform.database, platform.agent

## Status

Accepted

Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amended by [45. Isolation enforcement and role model](0045-isolation-enforcement-and-role-model.md)

## Context

**Isolation enforced from the first slice** (D30). A tenant identifier on every entity ([D5](0005-distribution-and-tenancy.md)) is not enough on its own; scoping retrofitted into an existing codebase is easy to miss somewhere, and a single unscoped path is a cross-tenant leak.

## Decision

Isolation of tenants and projects is enforced throughout the codebase from the first slice, including in single-tenant self-hosted installations, rather than being added with the cloud edition. The tenant identifier on every entity ([D5](0005-distribution-and-tenancy.md)) is necessary but not sufficient: every path through which an entity is read, written, cached or leased checks its scope.

- **Persistence.** Every query is scoped by tenant and project. No data access path is unscoped.
- **Interface.** Every request is authorized against the caller's roles in the project concerned.
- **Storage.** Artifact paths are prefixed by tenant and project ([D23](0023-artifact-storage-layout.md)), and credentials leased to a unit are scoped to that unit ([D21](0021-architecture-planes.md)).
- **Cache.** Lookups are scoped to the project by default and pass through the eligibility filter ([D9](0009-cache-scope.md), [D26](0026-placement-constraints.md)).
- **Agents.** Each agent's identity is bound to one tenant, and an agent leases only that tenant's work.
- **Visibility.** Entities a user cannot read are hidden by default, in the catalog, in lineage and in previews. Showing more later, such as anonymous placeholders in lineage, is additive and is settled with [S19]({workspace}/documentation#3).
- **External catalogs.** Added by [D44](0044-minimum-technology-stack.md): datasets classified restricted or above are not projected into an external Iceberg catalog unless their owner allows it, because catalogs that vend storage credentials can extend read access beyond the platform's scopes.
- **Mechanism and roles.** Settled by [D45](0045-isolation-enforcement-and-role-model.md): Postgres row-level security enforces the tenant, and a mandatory authorization layer enforces project scope, roles and clearance.
