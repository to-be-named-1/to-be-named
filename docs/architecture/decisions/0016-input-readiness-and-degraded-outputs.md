# 16. Input readiness and degraded outputs

Date: 2026-10-11
Applies to: platform.controlPlane, workflowAuthor

## Status

Accepted

## Decision

Each consumer declares, per input, what happens when that input is stale, failed or missing. Outputs built on inputs that were not ready are marked degraded, and the marking cascades downstream with its reason.

- **Policies.** **Wait** until the input is ready, up to a timeout; **proceed** on the last valid version; **skip** the interval and reconcile later; or **fail** immediately and alert. An input may also be declared optional, in which case the run proceeds without it.
- **Defaults.** Scheduled runs wait with a timeout derived from the freshness expectation of the dataset they produce, then fail and alert. Manual and interactive runs proceed on the last valid version with a warning. Both defaults are configurable per workflow and per input.
- **Waiting.** A waiting run is a scheduler state re-evaluated by the reconciliation loop and holds no compute. Input versions are resolved only once all required inputs are ready, so the snapshot of [D14](0014-input-version-resolution.md) is taken after the wait rather than before it.
- **Quarantine.** Quarantined versions are never read, whatever the policy, unless an override releases them ([D31](0031-execution-state-model.md)).
- **Degradation.** An output built on a stale, failed or absent input is published as degraded, with the reason stated — which input, which version was used, and which was expected. The marking cascades to every downstream dataset built from it, carrying the originating cause so that a consumer several steps away sees the root reason rather than only its immediate input. The marking clears when the output is rebuilt from ready inputs.
- **Provenance.** The policy applied, the time spent waiting and the versions ultimately read are recorded in the run's provenance.
