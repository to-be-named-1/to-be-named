## Brief

> **Status: working draft. Nothing in this documentation is final.**
> Every decision, design, capability statement and example recorded here reflects the state of the discussion at the time of compilation. All of it is provisional and may change as development proceeds and as implementation experience, measurements and user feedback come in. "Accepted" in the decision log means agreed for now, not fixed.

### The project in brief

A cloud-based, **open-core**, **domain-agnostic** web platform for assembling, scheduling, executing and monitoring multi-stage data and computation pipelines, with **reproducibility as a first-class, verifiable product capability**.

- **Authoring.** Pipelines are built on a visual canvas and compiled to a custom intermediate representation (IR), which is the single source of truth. Definitions round-trip to YAML in git, which is authoritative for git-connected projects; a Python SDK generating IR follows ([D41](../../decisions/0041-ir-text-form-round-trip-and-structure.md)).
- **Development.** Changes are tried on samples, or at full scale in a sandbox that shares unchanged data with production, before they are deployed ([D50](../../decisions/0050-development-mode.md)).
- **Execution.** Containerized execution units run on Kubernetes, HPC clusters (Slurm, through outbound agents), cloud batch, or a single-machine container deployment. Relational work is pushed down to the customer's warehouse where the data lives.
- **Deployment model.** Bring-your-own-compute is the primary model: execution runs on the customer's own infrastructure and the vendor hosts only the interface and control planes ([D22](../../decisions/0022-deployment-topologies.md)). Hybrid and self-hosted are the first-class topologies; fully managed serves trials and organizations that do not want to manage their own data-plane infrastructure.
- **Processing engines.** Built-in tabular nodes are defined as Ibis expressions and run on DuckDB in-process or are pushed down to Postgres or Snowflake, with Polars used only by justified exception and for code nodes; non-tabular work runs in Python or container-command runtimes and scales by fan-out ([D25](../../decisions/0025-processing-engines-and-runtimes.md), [D27](../../decisions/0027-ibis-for-relational-node-definitions.md)). The planner checks each unit's estimated working set against backend capacity rather than relying on declared dataset sizes ([D34](../../decisions/0034-capacity-and-size.md)).
- **Disciplines served.** Data engineering, data science and ML engineering, on one shared substrate (CORE).
- **First slice.** Development begins with the tabular family only, on the single-machine container deployment and Kubernetes, with Ibis on DuckDB in-process (Polars by justified exception and for code nodes), the visual canvas and git round-tripping; execution is driven by a pull-based agent in every deployment, tenant and project isolation is enforced throughout from the start, and managed datasets on object storage are readable by external engines through projected Iceberg metadata ([D29](../../decisions/0029-first-development-slice.md), [D30](../../decisions/0030-tenancy-and-isolation-enforcement.md), [D42](../../decisions/0042-catalog-persistence.md)). Warehouse pushdown, the other dataset families, HPC and cloud batch follow.
- **Technology.** Go for the control plane and the execution agent, Python for unit runtimes, Postgres 17 or later, protobuf with ConnectRPC between every component, and a React single-page application with React Flow for the interface and canvas ([D44](../../decisions/0044-minimum-technology-stack.md)). Postgres is the control plane's only stateful dependency, and hot scheduling state is held in the memory of a single active leader ([D47](../../decisions/0047-control-plane-structure.md)).
- **Excluded for now.** Deep learning and visual neural-network design; a native streaming runtime (batch first, then micro-batch, with streaming seams preserved); container-free local execution; online model serving; a platform-run Spark engine.
- **Positioning.** A visual workflow platform for data engineering, data science and MLE, with production orchestration semantics (logical intervals, backfills, fan-out, retries, fair scheduling) and verifiable reproducibility.
- **Principle.** Standard data-engineering practice comes first; reproducibility and its constraints are opt-in, never imposed ([D36](../../decisions/0036-data-engineering-practice-first-reproducibility-by-choice.md)).
- **Vision.** Large-scale analysis should be reproducible by construction. Every run carries complete provenance and a verified statement of how closely it can be reproduced.
- **Business model.** Open core. The core is open source; managed cloud, multi-tenancy, enterprise support and AI assistance are paid. The license and the exact open/paid line are deferred ([D5](../../decisions/0005-distribution-and-tenancy.md)).

### System overview

A web-based platform for assembling, scheduling, executing and monitoring multi-stage data and computation pipelines, and for establishing what each run can be trusted to reproduce.

Pipelines are composed on a visual canvas and compiled to a custom intermediate representation, which is the definitive description of the work to be done. From that representation the platform schedules and executes containerized units of work across local machines, Kubernetes clusters, HPC schedulers and cloud batch services, records complete provenance for every run, and reuses prior results wherever inputs and code are unchanged.

The platform is **domain-agnostic by design**. A single substrate — scheduling, execution, datasets, artifacts, provenance and access control — serves data engineering, data science and machine learning engineering.

**Vision.** Large-scale analysis should be reproducible by construction rather than by individual discipline. A pipeline built on this platform is a portable, versioned and shareable asset; every run carries a complete provenance record and a verifiable statement of how closely its results can be reproduced. Visual authoring lowers the barrier for practitioners who are not infrastructure specialists, while text round-tripping, custom code nodes and explicit control over parallelism, resources and execution backends keep the platform acceptable to engineers.

- **Reproducibility as a product capability.** Pinned environments and provenance are the baseline. Each run is assigned a tier, established by re-execution and comparison rather than asserted.
- **One substrate, three disciplines.** Datasets are first-class objects, which unifies ETL outputs, feature tables and scientific data under one lineage and scheduling model.
- **Visual authoring, production orchestration.** A canvas over an engine with the semantics engineers expect: logical intervals, backfills, fan-out, retries, quotas and fair scheduling.
- **Open core.** The core is open source. Managed infrastructure, multi-tenancy, enterprise support and AI assistance are commercial.

**Intended users.** Analysts and researchers who need dependable pipelines without operating the underlying infrastructure; data and platform engineers who require lineage, backfills and governance; and teams that must share, review and re-run each other's work.

**Excluded from this revision.** Deep learning and visual neural-network design; a native streaming runtime (batch first, then micro-batch, per [D6](../../decisions/0006-streaming.md), with the architectural seams for later streaming support recorded in [D12](../../decisions/0012-streaming-readiness.md)); container-free local execution ([D11](../../decisions/0011-execution-modes.md)); and online model serving, delegated to external serving systems ([D39](../../decisions/0039-online-model-serving.md), MLE 4.2). Exclusions are recorded so that they are revisited deliberately rather than by default.
