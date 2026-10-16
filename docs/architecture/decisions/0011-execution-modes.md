# 11. Execution modes

Date: 2026-10-11
Applies to: platform, platform.agent, platform.unitRuntime

## Status

Accepted

Amended by [36. Data-engineering practice first, reproducibility by choice](0036-data-engineering-practice-first-reproducibility-by-choice.md)

## Context

**Containers rather than a single process** (D11). Conflicting dependencies (R, Python, bioinformatics binaries), isolation of untrusted code, resource control, HPC and Kubernetes portability, and pinned images all require containers. A container-free mode would mean two execution paths, an embedded metadata store and extra OS support.

## Decision

The first release has no local, container-free execution mode. All execution runs in containers, and the entry point for evaluation and small teams is a single-machine, container-based deployment of the whole platform.

- **Rationale.** A container-free mode would require an embedded metadata store alongside Postgres, per-node isolated environments for conflicting dependencies, support for additional operating systems, and a permanent obligation to keep two execution paths behaviorally identical. The single-machine deployment is required regardless and adds no cost.
- **Deferred.** Two options are recorded for later: a **local worker** that runs units as processes on a user's machine against a normal control plane, reusing the agent architecture needed for HPC backends; and a **standalone** installation requiring neither a server nor containers. Either is reconsidered if adoption data shows the container requirement is costing users.
- **Seam.** Execution remains behind the backend interface ([D12](0012-streaming-readiness.md), Seam 9), so a local backend can be added later without changing the model. If one is added, its runs are capped at Traceable, or Re-executable with a recorded lockfile, and may not publish to datasets with an enforced contract. This restriction is to be reconsidered under [D36](0036-data-engineering-practice-first-reproducibility-by-choice.md) when a local backend is taken up.
- **Images.** The platform builds images from declared dependencies, with prebuilt base images for Python, R and common scientific tools, so users rarely write Dockerfiles (CORE 1.10).

## Follow-ups

- A local worker or standalone installation, if adoption data shows the container requirement is costing users.
