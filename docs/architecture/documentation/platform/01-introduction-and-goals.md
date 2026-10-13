## Introduction and goals

The platform assembles, schedules, executes and monitors multi-stage data and computation pipelines, and states what each run can be trusted to reproduce. One substrate of scheduling, execution, datasets, artifacts, provenance and access control serves data engineering, data science and machine learning engineering. Bring-your-own-compute is the primary deployment model: execution runs on the customer's own infrastructure, while the interface and control planes are hosted by the vendor or self-hosted ([D22]({workspace}/decisions/Platform#22)).

The workspace documentation's brief describes the product and its users; this documentation describes how the platform is built.

### Requirements

What the platform must let its users do is stated as capability lines, grouped as CORE, DE, DS and MLE, in the workspace documentation. Decisions [D1]({workspace}/decisions/Platform#1) onwards record how the architecture meets them.

### Quality goals

| Goal | Meaning | Decisions |
|---|---|---|
| Correct under failure | A result becomes current only through one atomic commit by the control plane, fenced against superseded attempts. Any data-plane component may be lost at any moment. Invariants are enforced by the database, so correctness never rests on leadership being exclusive. | [D15]({workspace}/decisions/Platform#15), [D21]({workspace}/decisions/Platform#21), [D40]({workspace}/decisions/Platform#40), [D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48) |
| Isolated | Tenants are separated by row-level security in the database, and projects by a mandatory authorization layer, on every access path and in single-tenant installations too. | [D9]({workspace}/decisions/Platform#9), [D30]({workspace}/decisions/Platform#30), [D45]({workspace}/decisions/Platform#45) |
| Data stays where it lives | Bulk data never passes through the interface or control planes. Agents connect outward only, and mint credentials and resolve secrets inside the customer's environment. | [D21]({workspace}/decisions/Platform#21), [D22]({workspace}/decisions/Platform#22), [D40]({workspace}/decisions/Platform#40) |
| Practice first, reproducibility by choice | Standard data-engineering practice is never constrained for the sake of reproducibility. Provenance, read positions and pinned images are always recorded; whatever costs storage, compute or freedom of practice is opt-in. | [D7]({workspace}/decisions/Platform#7), [D36]({workspace}/decisions/Platform#36) |
| Scales to its targets | Ten thousand task runs per run and two thousand running attempts per control plane, with a ceiling of a million and fifty thousand that the design must not preclude. | [D43]({workspace}/decisions/Platform#43) |

### Stakeholders

| Person | Concern |
|---|---|
| Workflow author | Building workflows on the canvas or in git, trying them on samples and in sandboxes, and committing them |
| Operator | Running, backfilling and monitoring production work |
| Project maintainer | Project settings, environment bindings, membership and what is deployed |
| Dataset owner | Contracts, classification, retention and freshness of datasets, and releasing quarantined versions |
| Tenant administrator | Members, agent pools, connections, storage targets, quotas and weights |
| Auditor | The audit trail and metadata, without data content |
| Data consumer | Reading managed datasets with their own query engines |
| Infrastructure operator | Installing and upgrading a self-hosted platform, its agents and their backends |
| Vendor operator | Operating the hosted control plane |
