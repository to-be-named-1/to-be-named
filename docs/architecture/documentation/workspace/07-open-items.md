## Open items

Questions the design anticipates but has not yet resolved. Each becomes a decision or a capability line once settled; a resolved item points to the decision that resolved it.

S1–S24 are pending migration; their authoritative text is the "Open items" section of project-design.md v0.10.

### S25 · Single-machine object storage

**Status:** Open

Self-hosted distributions bundle an S3-compatible store as the default storage target for installations without object storage of their own, so that casual users need not provide one. Any S3-compatible or cloud object storage can be configured instead ([D4](../../decisions/0004-datasets-as-first-class-objects.md)). A bundled S3-compatible store, rather than the local filesystem, keeps one storage path in every deployment: browser uploads through pre-signed URLs ([D4](../../decisions/0004-datasets-as-first-class-objects.md), [D21](../../decisions/0021-architecture-planes.md)), credentials scoped by the agent ([D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md)) and external readability of projected tables ([D44](../../decisions/0044-minimum-technology-stack.md)).

- **To settle.** The product: SeaweedFS (Apache-2.0), Garage (AGPLv3) and RustFS (Apache-2.0, version 1.0 in September 2026) are candidates; MinIO's community edition was archived upstream in February 2026. Scoped short-lived credentials on the chosen store ([D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md)). Licence compatibility, reviewed with the licence ([D5](../../decisions/0005-distribution-and-tenancy.md)). Moving existing datasets from the bundled store to another storage target. Consistent backup of the store together with Postgres.

*References:* [D4](../../decisions/0004-datasets-as-first-class-objects.md) · [D5](../../decisions/0005-distribution-and-tenancy.md) · [D21](../../decisions/0021-architecture-planes.md) · [D22](../../decisions/0022-deployment-topologies.md) · [D29](../../decisions/0029-first-development-slice.md) · [D40](../../decisions/0040-protocol-between-the-control-and-data-planes.md) · [D44](../../decisions/0044-minimum-technology-stack.md) · CORE 2.17
