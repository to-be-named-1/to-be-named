# 7. Reproducibility guarantee

Date: 2026-10-11
Applies to: platform.controlPlane, platform.webApp

## Status

Accepted

Amended by [36. Data-engineering practice first, reproducibility by choice](0036-data-engineering-practice-first-reproducibility-by-choice.md)

## Context

**Bit-identical reproducibility was rejected** (D7). It is unattainable with floating point, parallelism and library changes, and users care about the same *result*. Tolerance-based comparators and explained verdicts are the valuable product; byte hashes remain internal accelerators.

## Decision

The goal is the same output, not byte-identical files. Bit-identical reproducibility is not a user-facing goal; byte hashes remain an internal tool for fast verification and storage deduplication.

- **Tiers.** **Traceable** — a complete record of what ran and on what; re-execution is not assured. **Re-executable** — same code, inputs and environment; outputs may differ. **Reproducible** — same outputs, confirmed by comparators within recorded tolerances.
- **Ceiling.** The definition can prove a ceiling statically — network access, for example, caps a run at Re-executable — but Reproducible is reached only through a passing verification run. Custom code nodes default to Re-executable until verified.
- **Weakest link.** A run's tier is set by the weakest node on each path.
- **Decay.** A run drops to Traceable when its inputs are garbage-collected; where the reproducibility setting is on, the interface warns before this happens ([D36](0036-data-engineering-practice-first-reproducibility-by-choice.md)). Inputs of runs still in progress are protected ([D14](0014-input-version-resolution.md)).
- **Per run.** A tier belongs to a run, not a workflow. Fixing a workflow makes future runs more reproducible, never past ones.
