# 53. Open and proprietary features

Date: 2026-10-13
Applies to: platform, identityProvider, auditor, vendorOperator

## Status

Accepted

Amends [5. Distribution and tenancy](0005-distribution-and-tenancy.md)

## Context

[D5](0005-distribution-and-tenancy.md) made the platform open core and deferred the license and the exact line between open and paid features.

## Decision

The line between open and proprietary features follows one rule. The platform stays open and fully operable for single users and small teams who self-host it. Features that concern organizations are proprietary, behind an extension interface with an open default implementation. The open edition never falls short of [D36](0036-data-engineering-practice-first-reproducibility-by-choice.md).

- **Open:** the engine (canvas, IR, git round-tripping, scheduling, caching, datasets and lineage); the pull-based agent ([D29](0029-first-development-slice.md)); the Kubernetes and HPC backends; reproducibility tiers and verification; development mode ([D50](0050-development-mode.md)); tenant and project isolation within a tenant ([D30](0030-tenancy-and-isolation-enforcement.md)); the fixed roles of [D45](0045-isolation-enforcement-and-role-model.md); the mechanism of classification and clearance ([D44](0044-minimum-technology-stack.md), [D45](0045-isolation-enforcement-and-role-model.md), [D50](0050-development-mode.md)); sign-in with local accounts and generic OpenID Connect; an in-platform audit log that Admins can view; pushdown to Postgres.
- **Proprietary:** several tenants per control plane and the hosted control plane, and with it the hybrid, managed-with-customer-storage and fully managed topologies ([D22](0022-deployment-topologies.md)); sandboxing of untrusted containers between tenants (CORE 7.6); custom roles and attribute-based policy ([D45](0045-isolation-enforcement-and-role-model.md)); syncing teams from identity-provider groups, and SCIM provisioning; SAML single sign-on; audit export to external sinks and long audit retention; organization-wide quotas and cost attribution (CORE 7.5, CORE 4.5, [S22]({workspace}/documentation#3)); break-glass support access ([D45](0045-isolation-enforcement-and-role-model.md)); detection of personal data (DE 5.3), column and row masking (DE 5.4), erasure cascades (DE 5.5) and legal holds ([S15]({workspace}/documentation#3)); AI assistance.
- **Not gated:** high availability and deployment by role ([D47](0047-control-plane-structure.md)) stay in the open code, since leader election and its epoch are needed for correctness; support and service levels are offered commercially instead.
- **Undecided:** whether the Snowflake connector is open or proprietary.
- **Role model:** Three parts of the role model of [D45](0045-isolation-enforcement-and-role-model.md) are proprietary, since they serve organizations rather than small teams: teams, as groups of members named in role bindings, dataset ownership and approvals; role bindings on a single resource such as one workflow; and the Auditor role. The open edition keeps the fixed project roles, the tenant roles Admin and Member, service accounts, clearance and project scope. It binds roles to users and service accounts on the tenant or a project; dataset owners and approvers are users or project roles; finer separation of access uses separate projects, as [D45](0045-isolation-enforcement-and-role-model.md) already provides; and its audit log is viewable by Admins. Every place [D45](0045-isolation-enforcement-and-role-model.md) accepts a team or a binding on a single resource also accepts a user or a project role, so no decided mechanism depends on the three.
- The inventory of extension points, the split into modules and the classification of the first slice follow in a decision of their own; the license, contributor terms and the full line keep the deadline set in [D5](0005-distribution-and-tenancy.md).
