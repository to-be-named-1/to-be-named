# 36. Data-engineering practice first, reproducibility by choice

Date: 2026-10-11
Applies to: platform, platform.controlPlane, platform.webApp

## Status

Accepted

Amends [7. Reproducibility guarantee](0007-reproducibility-guarantee.md)
Amends [11. Execution modes](0011-execution-modes.md)

## Context

**Data-engineering practice first** (D36). Reproducibility is the differentiator, but most organizations do not need it, and imposing its constraints would push them away. Whatever costs storage, compute or freedom of practice for its sake is opt-in.

The reasoning on projection on by default, in [D44](0044-minimum-technology-stack.md), also cites this decision.

## Decision

Standard data-engineering practice comes first; reproducibility and the constraints it brings are opt-in. The platform never stops a team from working the way data engineers normally work in order to protect a reproducibility guarantee the team has not asked for. Most organizations do not need reproducibility tiers, and a platform that imposes their costs drives users away.

- **Always on.** What costs little and serves ordinary engineering as well: provenance and lineage, recorded read positions and source versions, pinned image digests, and the computed tier, available as information and never blocking.
- **Opt-in.** Anything that costs storage, compute or freedom of practice for the sake of reproducibility: copying sources ([D35](0035-ephemeral-extraction.md)), protecting inputs from retention beyond what ordinary retention keeps, verification runs, warnings before tier decay, and any rule that refuses a plan, a publication or a design because it would lower a tier.
- **Test.** Every proposed rule is checked: does it constrain a standard practice, or add storage or compute cost, for the sake of reproducibility? If so, it is optional and off unless the team turns it on.
- **Reproducibility setting.** One setting per project, with per-workflow override, turns the opt-in behaviors on together: protection of inputs beyond ordinary retention, warnings before decay, and the verification policy ([S2]({workspace}/documentation#7.2)). It is off by default.
- **Retention.** Ordinary retention governs; runs decay to Traceable as their inputs expire ([D7](0007-reproducibility-guarantee.md)). Preserving inputs referenced by provenance beyond retention happens only where the reproducibility setting is on. Protection of the inputs of runs still in progress ([D14](0014-input-version-resolution.md)) is operational and always applies.
- **Decay warnings.** Shown only where the reproducibility setting is on.
- **Guard rails.** Rules that protect correctness rather than reproducibility, such as leakage prevention ([DS 2.8]({workspace}/documentation#5)) and temporal splits ([DS 3.1]({workspace}/documentation#5)), are kept as warnings an author can override rather than refusals.
- **Local execution.** The restriction [D11](0011-execution-modes.md) places on publishing from a future local backend is reconsidered under this principle when such a backend is taken up.
