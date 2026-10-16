# 9. Cache scope

Date: 2026-10-11
Applies to: platform.controlPlane

## Status

Accepted

Amended by [45. Isolation enforcement and role model](0045-isolation-enforcement-and-role-model.md)
Amended by [50. Development mode](0050-development-mode.md)

## Context

**Tenant = the whole organization** (D9). Projects are the permission scope and cache boundary. Cross-tenant cache sharing is never allowed, because a cache hit leaks the fact that a computation happened and its result.

The reasoning on clearance separate from roles, in [D45](0045-isolation-enforcement-and-role-model.md), also cites this decision.

## Decision

A tenant is the unit of hard isolation and billing — for an enterprise, the whole organization. Within a tenant, work is organized into projects, which are the default permission scope; users and teams hold roles per project. Cached results are reused within a project by default, may be reused across projects of the same tenant by opt-in, and are never reused across tenants.

- **Hierarchy.** Tenant (organization) → projects or workspaces → users and teams. Sharing datasets and workflows between members and teams is the normal case, governed by project permissions ([S20]({workspace}/documentation#3)). A self-hosted open-source installation is effectively a single tenant.
- **Permission check.** A project may reuse a cached output produced elsewhere in the tenant only if it could read every input that produced it and is cleared for the output's classification. A cache hit otherwise reveals that a computation took place and discloses its result. Amended by [D45](0045-isolation-enforcement-and-role-model.md): clearance is a level held on each membership.
- **Public data.** Outputs derived solely from explicitly public reference data, such as a published reference genome index, may be shared more widely.
- **Later.** Hard isolation boundaries inside a tenant — for a regulated division, subsidiary or separate legal entity — are not required in the first release, but the model must not preclude them.
- **Development runs.** Amended by [D50](0050-development-mode.md): for a development run started by a principal, the eligibility check also applies that principal's clearance.

## Follow-ups

- Hard isolation boundaries inside a tenant must remain possible.
