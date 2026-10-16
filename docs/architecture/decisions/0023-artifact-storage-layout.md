# 23. Artifact storage layout

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, platform.bundledObjectStorage, objectStorage

## Status

Accepted

Amended by [42. Catalog persistence](0042-catalog-persistence.md)
Amended by [44. Minimum technology stack](0044-minimum-technology-stack.md)
Amended by [51. Adoption of existing data](0051-adoption-of-existing-data.md)
Amended by [55. Commits to table-format storage targets](0055-commits-to-table-format-storage-targets.md)

## Context

**Identity-addressed rather than content-addressed storage** (D23). A content-addressed path needs the hash before the final location is known, forcing a second write of large outputs.

## Decision

Artifacts are stored at identity-addressed paths, and the artifact itself is a manifest in the catalog. Content hashes are attributes of an artifact rather than the basis of its location.

- **Paths.** Files are written directly to `artifacts/<tenant>/<project>/<path.name>--<short-id>/<partition>/<artifact-id>/…` for a dataset's artifacts, and to `artifacts/<tenant>/<project>/<artifact-id>/…` for artifacts that belong to no dataset, with the identifier assigned before writing ([D51](0051-adoption-of-existing-data.md)). Content-addressed paths would require a hash before the final location is known, and therefore a second write for large outputs, since object stores have no inexpensive rename.
- **Manifest.** Each artifact's catalog record lists its files with their byte digests and file-group roles ([D17](0017-dataset-families-and-first-release-scope.md)), its schema, statistics (byte and row counts per partition being mandatory, [D34](0034-capacity-and-size.md)) and partition values, a canonical hash where under the [D8](0008-cache-keying.md) threshold, its preview reference, the producing task run and its storage target ([D4](0004-datasets-as-first-class-objects.md)). A dataset adopted with a manifest of the platform's own may reference files outside the prefix ([D51](0051-adoption-of-existing-data.md)).
- **Immutability.** Files are never overwritten; any change produces a new artifact.
- **Deduplication.** Optional and asynchronous: where byte digests match, a later manifest may reference an earlier artifact's files and the duplicate is removed.
- **Collection.** Garbage collection marks everything referenced by a retained, cached, pinned or provenance-protected manifest, and removes the rest. Provenance protection beyond ordinary retention applies only where the reproducibility setting is on ([D36](0036-data-engineering-practice-first-reproducibility-by-choice.md)). Amended by [D44](0044-minimum-technology-stack.md): files of a projected dataset are deleted only after the Iceberg snapshots that reference them have expired.
- **Layers.** A dataset snapshot references partition versions, which reference artifact manifests, which reference files. Amended by [D42](0042-catalog-persistence.md): a snapshot selects partition versions by validity interval rather than listing them. Where the storage target is an Iceberg or Delta table, the manifest lists the files staged for it, which the table's own commit adds after the platform's ([D55](0055-commits-to-table-format-storage-targets.md)).
