# 17. Dataset families and first-release scope

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime

## Status

Accepted

Amended by [29. First development slice](0029-first-development-slice.md)

## Decision

Datasets are grouped into families whose behavior on the platform is the same, rather than handled format by format. The first release supports six families; the remainder are added later through the plugin interface. Amended by [D29](0029-first-development-slice.md): the first development slice supports the tabular family only, and the other five follow through the same interface.

- **In scope.** **Tabular** — CSV/TSV, Parquet, ORC, Avro, Arrow, JSON Lines, Excel, statistical-package formats, and Iceberg, Delta and Hudi tables. **Semi-structured and records** — JSON, XML, YAML, logs, and industry record formats such as HL7 and FHIR. **Text and documents** — text corpora, JSONL datasets, and documents requiring extraction such as PDF and DOCX. **Images** — general formats, DICOM, microscopy formats and GeoTIFF, with their annotation formats. **Genomics and life sciences** — FASTQ, FASTA, BAM, SAM, CRAM, VCF, BCF, BED, GFF and related formats. **ML artifacts** — models, training shards, and embeddings and vector indexes.
- **Later.** Audio and video, scientific multidimensional arrays (HDF5, Zarr, NetCDF, FITS), geospatial, graphs, and reports and outputs, delivered through the same interface.
- **Orthogonal.** Compression and archive wrappers — gzip, zstd, bgzip, tar, zip — apply across families rather than forming a family of their own.
- **Follows.** Supporting these families requires five structural capabilities: file groups whose members travel together ([CORE 6.16]({workspace}/documentation#3)), linked items such as paired reads ([CORE 6.17]({workspace}/documentation#3)), sharded collections of many small items ([CORE 6.18]({workspace}/documentation#3)), declared splittability ([CORE 6.19]({workspace}/documentation#3)), and classification that reaches metadata embedded inside files ([DE 5.10]({workspace}/documentation#4)).
- **Models.** Models are a specialized dataset type rather than a separate registry. They share identity, versioning, lineage, publication, retention, classification and erasure with every other dataset, and add a signature, a lifecycle stage, evaluation metrics and approval state. The registry interface presents them as models; underneath they are the same aggregate, so one lineage graph runs from source data to model.
- **Extension point.** Each family is implemented through one interface covering nine responsibilities: describe (file groups and links), contract, validate and metadata, which are required; and profile, preview, compare, canonicalize and access, which are optional and degrade gracefully when absent. The platform core never interprets a format directly.
- **Placement.** Family plugins read bulk data and therefore run in the data plane, inside execution units; only their results reach the control plane. Third-party plugins are sandboxed like any other user code.
- **Release.** The interface is internal in the first release. The six built-in families are implemented against it, and it is published as a stable plugin API only once it has held up.

## Follow-ups

- Later dataset families: audio and video, multidimensional arrays, geospatial, graphs, reports. Publication of the family plugin interface as a stable API.
