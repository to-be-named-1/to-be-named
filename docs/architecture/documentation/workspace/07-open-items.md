## Open items

Questions the design anticipates but has not yet resolved. Each becomes a decision or a capability line once settled; a resolved item points to the decision that resolved it.

S1–S24 are pending migration; their authoritative text is the "Open items" section of project-design.md v0.10.

### S25 · Single-machine object storage

**Status:** Open

Self-hosted distributions bundle an S3-compatible store as the default storage target for installations without object storage of their own, so that casual users need not provide one. Any S3-compatible or cloud object storage can be configured instead ([D4]({workspace}/decisions/Platform#4)). A bundled S3-compatible store, rather than the local filesystem, keeps one storage path in every deployment: browser uploads through pre-signed URLs ([D4]({workspace}/decisions/Platform#4), [D21]({workspace}/decisions/Platform#21)), credentials scoped by the agent ([D40]({workspace}/decisions/Platform#40)) and external readability of projected tables ([D44]({workspace}/decisions/Platform#44)).

- **To settle.** The product: SeaweedFS (Apache-2.0), Garage (AGPLv3) and RustFS (Apache-2.0, version 1.0 in September 2026) are candidates; MinIO's community edition was archived upstream in February 2026. Scoped short-lived credentials on the chosen store ([D40]({workspace}/decisions/Platform#40)). License compatibility, reviewed with the license ([D5]({workspace}/decisions/Platform#5)). Moving existing datasets from the bundled store to another storage target. Consistent backup of the store together with Postgres.

*References:* [D4]({workspace}/decisions/Platform#4) · [D5]({workspace}/decisions/Platform#5) · [D21]({workspace}/decisions/Platform#21) · [D22]({workspace}/decisions/Platform#22) · [D29]({workspace}/decisions/Platform#29) · [D40]({workspace}/decisions/Platform#40) · [D44]({workspace}/decisions/Platform#44) · CORE 2.17
