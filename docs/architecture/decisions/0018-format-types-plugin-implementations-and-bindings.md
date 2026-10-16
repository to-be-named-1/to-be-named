# 18. Format types, plugin implementations and bindings

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime, tenantAdmin

## Status

Accepted

Amended by [49. Source probes](0049-source-probes.md)

## Decision

A data format is a **type** defined once by the platform; plugins are **implementations** of a type. Every dataset is bound to exactly one pinned implementation. Several implementations and versions of a type may coexist in the architecture, but by policy a project uses one per type unless an administrator allows more.

- **Plugin kinds.** Two kinds of plugin exist, both of which may come from third parties: **dataset-family plugins**, which describe what data is, and **node plugins**, which describe what is done to it. Connectors to source and target systems are node plugins.
- **Type.** A namespaced identifier with a specification version, such as `genomics/bam` v1, reusing established vocabularies such as the EDAM format ontology where they exist. The type owns three things: the **contract schema** (what a contract for this format may state), the **reader protocol** nodes program against, and a **conformance suite** of files that must validate, files that must fail, and pairs a comparator must judge equivalent or different.
- **Manifest.** A plugin declares its identity and version, the type and type version it implements, its pinned runtime image, the file-group layout of one item (roles and filename patterns), any linked items, and which optional capabilities it provides — including splittability.
- **Functions.** A plugin implements `validate` and `metadata`, which are required, and optionally `profile`, `preview`, `compare`, `canonicalize`, `open` (a reader conforming to the type's protocol) and `splits`. A plugin providing only the required functions is fully usable; absent capabilities degrade to file listings, byte-level comparison, input-addressed caching and whole-file processing.
- **Boundaries.** A plugin receives items and returns structured results. It does not define contract schemas or reader protocols, access the catalog or other datasets, manage storage, credentials or commits, or render interface elements; previews are returned as structured data of a fixed kind and drawn by the platform.
- **Nodes.** Node ports declare types, never plugins. A node therefore works with any dataset of the declared type regardless of which implementation validated it.
- **Binding.** Each dataset is bound to one implementation at an exact version, recorded on every dataset version. Changing the implementation is an explicit migration that revalidates the dataset. A dataset shared with another project is read using its own binding, whose pinned image remains available.
- **Policy.** Administrators set the allowed implementations per type at organization or project level, defaulting to exactly one. New datasets bind automatically to the approved implementation, so ordinary users are never asked to choose. Additional implementations may be allowed for vendor transitions or partner-supplied data.
- **Conformance.** A plugin must pass the type's conformance suite to claim the type. The suite bounds how far implementations may disagree about validity and equivalence; they may still differ in performance, preview quality and additional statistics.
- **Upgrades.** Upgrading a binding to a newer plugin version is explicit but inexpensive: a bulk action revalidates the selected datasets and reports any whose outcome would change before the switch is committed.
- **Later.** Taking presentation capabilities (preview, profile) from a different implementation than the semantic ones (contract, validation, comparison, hashing) is excluded from the first release.
- **Probes.** Amended by [D49](0049-source-probes.md): a connector, as a node plugin, may implement an optional `probe` function that returns a source's current version or position without reading its data.

## Follow-ups

- Taking presentation and semantic capabilities from different plugin implementations.
