# 8. Cache keying

Date: 2026-10-11
Applies to: platform.controlPlane, platform.unitRuntime

## Status

Accepted

Amended by [47. Control-plane structure](0047-control-plane-structure.md)

## Context

**Hybrid cache key** (D8). Input-addressed keys give a plan before the run; content-addressed keys give early cutoff. Canonical hashing costs a re-read, hence the 1 GB default threshold; byte digests are free because they are streamed during the write.

**Cache keys chained through nodes** (D8, amended). Keys chained through units depend on how nodes happen to be grouped, and automatic fusion moves unit boundaries whenever the policy, a pinned boundary or a resource ceiling changes, which would cause misses without any change in computation. Keys of intermediates are computed at plan time and never stored, so fusion's savings in storage and I/O are kept.

As first recorded, keys were chained through units, from each unit's semantic fields and the keys of its upstream units.

## Decision

Hybrid. Every node gets an **input-addressed** key, built from its own semantic fields plus the keys of the nodes feeding it, so the full plan of what will rerun is known before the run starts. Artifacts small enough to hash cheaply also get a canonical **content hash** when written; where every stored input a node depends on carries one, it gets a second, content-addressed key. Only outputs stored at unit boundaries are looked up and stored under their keys: a unit is skipped if every one of its stored outputs is found under either key, and on a miss its outputs are stored under both.

- **Node-level chaining.** Keys of intermediates inside a unit are computed at plan time and discarded, never stored or looked up, so fusion's savings are unaffected, and the key of a stored output does not change when automatic fusion regroups nodes ([D33](0033-automatic-fusion.md)).
- **Follows.** Early cutoff where it is cheap: an upstream unit that reran but produced identical output no longer forces expensive downstream work to repeat.
- **Follows.** A lookup is a lookup, not a check — caching trusts that a unit is a function of its key. Confirming that a rerun matches is the job of verification runs (CORE 5.7).
- **Byte digests.** A byte-level digest is computed for every file as it is written, at negligible cost because it is streamed alongside the write. No threshold applies.
- **Threshold.** Canonical content hashing — which may require re-reading and sorting — applies by default to artifacts up to **1 GB**. This is an initial default to be tuned from measurements during development, and configurable per project.
- **Overrides.** A node or dataset may opt in to canonical hashing above the threshold where downstream work is expensive enough to justify it, or opt out below it.
- **Expected reuse.** Amended by [D47](0047-control-plane-structure.md): what will rerun is shown before the run as expected reuse, computed from the keys known at run start. The lookup made when each task run is created is authoritative, since keys that depend on value outputs or content hashes exist only then and a cached output may expire or appear in between.

## Follow-ups

- Tune the 1 GB canonical-hashing threshold from measurements.
