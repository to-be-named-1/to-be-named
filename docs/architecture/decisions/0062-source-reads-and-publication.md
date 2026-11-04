# 62. Source reads and publication

Date: 2026-11-04
Applies to: platform.webApp, platform.controlPlane, platform.database, platform.unitRuntime, platform.derivationUnit, platform.probeUnit

## Status

Accepted

Amends [18. Format types, plugin implementations and bindings](0018-format-types-plugin-implementations-and-bindings.md)
Amends [49. Source probes](0049-source-probes.md)
Amends [57. Node-type contract](0057-node-type-contract.md)

## Context

[D57](0057-node-type-contract.md) lets a plan's builder run only in derivation units, which hold no data, credentials or network, and requires every leaf of a plan to be one of its inputs or a constant. It left open how a plan reads a source, where the source's schema comes from, and what a node that writes a dataset is. A builder that opens a source itself reaches storage while it builds, and the leaf of its plan is a table registered in one session under a generated name, which no other process can run and no cache can share. A node that writes into a dataset's location itself bypasses the staging, commit and fencing of [D15](0015-atomic-publication.md). A location written as a string in a parameter is one the control plane never sees, so no credential scope covers it ([D40](0040-protocol-between-the-control-and-data-planes.md)) and no environment binds it ([D41](0041-ir-text-form-round-trip-and-structure.md)).

## Decision

How plans read sources, where the schemas of sources come from, what the inputs and constants of a compiled plan are, what publishing a node's output is, and how nodes name locations.

- **Sources are opened by the runtime.** The unit runtime opens each source a unit reads through its connector and registers it under the name the compiled plan gives that input, so that the plan only ever holds an input with a schema and no data ([D32](0032-execution-unit-structure.md)). Node code never opens a source to obtain a plan's input.
- **Connectors.** A connector to a source system implements a reader interface: `probe`, returning the source's version or position where it has one ([D49](0049-source-probes.md)); `schema`, returning its schema from metadata without reading rows; and `open`, making its data available to a unit under a given name. Probe and execution units call them; derivation units never do. Deliveries to target systems are nodes with side effects ([D4](0004-datasets-as-first-class-objects.md), [D57](0057-node-type-contract.md)).
- **Sources in workflows.** A workflow reads a dataset, managed or external, by binding a node's input port to the dataset or to its declaration, and the canvas draws datasets as references in the graph. Connectors are not node types in the palette. The syntax is part of the workflow documents (design agenda).
- **Schemas of managed datasets.** A managed dataset's schema is the one the catalog recorded for the resolved version ([D42](0042-catalog-persistence.md)).
- **Registration of external datasets.** An external dataset is registered by its declaration ([D41](0041-ir-text-form-round-trip-and-structure.md)). Registration starts a schema probe in the data plane, and the observed schema is recorded in the catalog for each environment binding of the declaration's location, since environments may bind it to different data. Derivation and the canvas read the recorded schema. A declaration may state a schema, which is then the dataset's contract; an action copies an observed schema into the declaration, where it is reviewed like any other change.
- **Schemas at run start.** The probe that fixes a source's version at run start also returns its schema ([D49](0049-source-probes.md)). A schema that differs from the recorded one is handled by the declaration's schema mode: an observed schema is recorded anew, and the plans that read it are built again, since input schemas are part of their cache key ([D57](0057-node-type-contract.md)); a declared schema stops the run before anything is read, stating the difference. The modes are specified with the dataset declarations (design agenda).
- **Inputs of compiled plans.** The derivation request names the inputs of a compiled plan by their position within its segment, and node code never chooses them. The unit specification maps each name to the input bound to it. Plans built from the same node types, schemas and parameter values in different workflows are therefore the same plan and share their cache entries.
- **Constants.** A constant in a plan is one that travels inside the compiled plan: a literal of an Ibis or SQL plan, or a frame held inside a serialized Polars plan. A table that a builder creates in memory compiles into a reference to a table registered in the builder's own session, so a plan holding one is rejected.
- **Publication.** A node's output is published by binding it to a dataset ([CORE 6.8]({workspace}/documentation#3), [D13](0013-partitioning-intervals-and-dataset-ownership.md)). The unit runtime stages the output in the attempt's location as Parquet, with its row count ([D23](0023-artifact-storage-layout.md), [D44](0044-minimum-technology-stack.md)), and the platform commits it ([D15](0015-atomic-publication.md)), followed by the publication unit's commit where the storage target has its own ([D55](0055-commits-to-table-format-storage-targets.md)). No node type writes a managed dataset. Whether a run appends to a dataset or replaces its partitions follows from the dataset's partitioning and the run's interval ([D13](0013-partitioning-intervals-and-dataset-ownership.md), [D20](0020-backfill-commits-and-scheduling.md)), never from a node's parameters.
- **Locations.** Nodes take no parameter naming the storage location of data the platform reads or publishes: datasets and their declarations carry locations, bound per environment ([D41](0041-ir-text-form-round-trip-and-structure.md)). A node that reaches an external system names it by a `binding` parameter ([D57](0057-node-type-contract.md)). A string parameter may still hold a value relative to a bound location, such as a pattern of file names.
- **Amends.** [D18](0018-format-types-plugin-implementations-and-bindings.md): connectors to source systems are a kind of plugin of their own, with a reader interface, and deliveries to target systems are node plugins with side effects. [D49](0049-source-probes.md): probes also return schemas, and registering an external dataset starts one. [D57](0057-node-type-contract.md): the leaves of a compiled plan are its inputs, named by the derivation request, or constants that travel with it.

## Consequences

- Reading a dataset needs no node code; the palette holds the nodes that transform data or deliver it.
- Every read and write goes through a dataset or a binding, so the control plane can scope credentials, bind environments and record lineage for each.
- An external dataset is registered before a workflow can read it, and its registration waits for a probe in the data plane.
- A change to an external source's schema is found at run start, at the cost of one metadata read per source.

## Rejected alternatives

- Builders opening sources. Derivation would need credentials and network, and plans would read tables registered in one session under generated names.
- Derivation reading the metadata of files for their schemas. Footers are metadata, but reading them needs credentials and a route to storage, which derivation units do not have.
- An extraction node materializing each source first. Ephemeral reads could no longer be fused into the plans that follow them ([D35](0035-ephemeral-extraction.md)).
- Connector node types in the palette. A node would repeat the declaration's location, storage choice, change detection and schema, and two nodes could read one source differently.
- Names of a plan's inputs derived from node keys. Identical nodes in different workflows would compile into different plans and miss each other's cache entries.
- Shipping in-memory tables with compiled plans. Derivation results would carry data, where lookup data belongs in a dataset or in parameters.
- A node type that writes datasets. It would overwrite files that staging never overwrites, and commit outside the platform's commit.
- Locations as strings in parameters. The control plane could not scope credentials for a path it never sees, environments could not bind it, and its reads would have neither a dataset's identity nor a probed version.
- Recording observed schemas in the declaration. Every registration and every observed change would be a commit that the platform writes.

## Follow-ups

- The syntax of binding ports to datasets, with the workflow documents (design agenda).
- Schema modes and declared schemas, with the dataset declarations (design agenda).
