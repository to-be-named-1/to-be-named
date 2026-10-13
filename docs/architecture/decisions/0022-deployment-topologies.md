# 22. Deployment topologies

Date: 2026-10-11
Applies to: platform, platform.agent, kubernetes, hpcScheduler, cloudBatch, containerRegistry, credentialIssuer, customerObservability, infrastructureOperator, vendorOperator

## Status

Accepted

Amended by [29. First development slice](0029-first-development-slice.md)
Amended by [40. Protocol between the control and data planes](0040-protocol-between-the-control-and-data-planes.md)

## Context

**Four deployment topologies** (D22). Customer storage addresses integration and lock-in; hybrid addresses sovereignty; self-hosting suits open-source and air-gapped users. Bring-your-own-compute is now the primary model.

**Bring-your-own-compute** (D22). The plane separation ([D21](0021-architecture-planes.md)) already allowed it; making it primary aligns with regulated customers. It requires customers to provide container compute, not only a warehouse, and it shifts commercial value away from managed infrastructure (see [D5](0005-distribution-and-tenancy.md)).

## Decision

Four options are supported, ordered by how much the customer controls: **fully managed** (vendor operations, compute and storage); **managed with customer storage** (vendor operations and compute, writing to the customer's storage); **hybrid** (interface and control planes hosted by the vendor, data plane and storage in the customer's own cloud account or HPC cluster); and **self-hosted** (the customer operates everything, on one machine or a cluster).

- **Distinction.** With customer storage but vendor compute, data still passes through the vendor's machines during processing. This addresses integration, cost and lock-in, but strict sovereignty requires the hybrid option.
- **Outbound only.** Data-plane execution agents connect outward to the control plane and pull work. No inbound connectivity into a customer network is ever required. The control-to-data protocol must therefore work across networks, tolerate latency and interruption, and be pull-based. Amended by [D29](0029-first-development-slice.md): the same pull-based agent is used in every topology, including self-hosted and single-machine deployments.
- **Credentials.** In the hybrid topology, credentials for customer storage are minted inside the customer's environment by the agent. The hosted control plane never holds them. Amended by [D40](0040-protocol-between-the-control-and-data-planes.md): this applies in every deployment, not only hybrid, together with secrets, which the agent resolves from references.
- **What crosses.** Only metadata, statistics, events and pre-computed previews cross to the hosted planes. Previews and samples obey the classification of their source dataset, and a customer may disable them for sensitive datasets.
- **Telemetry.** A customer may keep logs and metrics within its own environment, with live tailing proxied through the agent, because logs may contain sensitive content.
- **Primary model.** Bring-your-own-compute is the primary model: execution runs on the customer's own infrastructure and the vendor coordinates. Hybrid and self-hosted are the first-class topologies. Fully managed serves trials and organizations that do not want to manage their own data-plane infrastructure, and managed with customer storage is retained unchanged.
- **Compute.** A bring-your-own-compute deployment provides a container-capable backend: Kubernetes, cloud batch or an HPC cluster. A warehouse alone runs only pushdown work; in-process nodes on DuckDB or Polars, Python code nodes and command-line tools require container compute. A warehouse-native container service may later serve as a backend for customers whose only compute is a warehouse.
- **Images.** Image builds and the image registry may run in the customer's environment, and images are referenced by digest wherever they are stored (CORE 1.10, CORE 5.1). HPC clusters commonly run images through Apptainer rather than Docker.

## Follow-ups

- A warehouse-native container service as a backend for customers whose only compute is a warehouse.
