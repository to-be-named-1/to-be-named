# 5. Distribution and tenancy

Date: 2026-10-11
Applies to: platform, platform.controlPlane, platform.database, identityProvider

## Status

Accepted
Amended by [53. Open and proprietary features](0053-open-and-proprietary-features.md)

## Context

The reasoning on isolation enforced from the first slice, in [D30](0030-tenancy-and-isolation-enforcement.md), also cites this decision.

## Decision

Open core. Core features are open source. Managed cloud infrastructure, multi-tenancy, enterprise support and AI integration are paid.

- **Deferred.** The license, the full line between open and paid features beyond the rule and classification of [D53](0053-open-and-proprietary-features.md), and whether open-source users may supply their own AI provider keys are deferred. They do not shape the architecture in the early stages.
- **Structural now.** Every entity carries a tenant identifier from the outset; the open-source edition runs as a single tenant, and the cloud edition is the same core plus extensions rather than a fork. Isolation is enforced along every access path from the first slice ([D30](0030-tenancy-and-isolation-enforcement.md)).
- **Structural now.** Capabilities likely to be commercial — authentication providers, access-policy enforcement, audit sinks, AI providers — sit behind extension interfaces from the start, so the open/paid line can be drawn later without restructuring and commercial code can live in a separate module.
- **Timing.** The license must be chosen before the first public release or before external contributions are accepted, whichever comes first; relicensing afterwards requires every contributor's consent. The repository is currently private ([D29](0029-first-development-slice.md)).
- **Direction.** SDKs, the IR specification and plugin interfaces are expected to be permissively licensed whatever is chosen for the core server, since plugin authors and integrators will not build on restrictive terms. Reproducibility features, the HPC backend and basic role-based access control are open ([D53](0053-open-and-proprietary-features.md)).

## Follow-ups

- License, the full open/paid line ([D53](0053-open-and-proprietary-features.md)), and bring-your-own AI keys. The license must be chosen before the first public release or first external contribution. The licenses of dependencies are reviewed with it, including ELK's EPL-2.0 ([D44](0044-minimum-technology-stack.md)).
