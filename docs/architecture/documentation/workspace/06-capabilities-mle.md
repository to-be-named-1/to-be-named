## Machine learning engineering (MLE)

Moving a model from experiment to a scheduled, trusted, replaceable and reversible production asset. This is the point at which the platform becomes a lifecycle system rather than a pipeline tool, and the area where scope is most likely to overrun.

### 1 · Features & training data

- **MLE 1.1** — Define a feature once and use the same definition for training and for inference.
  - *Note:* Training/serving skew is the most common production failure mode in machine learning. A single definition compiled to both paths addresses it.
- **MLE 1.2** — Retrieve features as of a point in time, so training rows never contain information from after the label event. `[shapes the core]`
  - *Note:* Requires event time and knowledge time. Decided ([D38]({workspace}/decisions/Platform#38)): met by event-time metadata and by publication history or a row-level ingestion timestamp, with a point-in-time join node; no change to the dataset model.
- **MLE 1.3** — Snapshot and version a training dataset so a model's training data can be reconstructed exactly. `[cross-discipline]`

### 2 · Training at scale

- **MLE 2.1** — Run large parallel sweeps and distributed training jobs under project resource caps.
  - *Note:* Sweeps are maps, or loops with carried state for adaptive search ([D46]({workspace}/decisions/Platform#46)). Training that spans several machines needs units of several containers or a customer-operated cluster, followed up with the execution backends.
- **MLE 2.2** — Request, queue for, and share GPUs, including fractional or time-shared allocation. `[shapes the core]`
  - *Note:* GPU scarcity makes queueing policy visible to users in a way that CPU scheduling does not. Directly related to [CORE 3.6](03-capabilities-core.md). GPU is a dimension of fair share from the start; fractional sharing is left to the backend ([D43]({workspace}/decisions/Platform#43)).
- **MLE 2.3** — Checkpoint a long-running task and resume it after interruption rather than restarting. `[shapes the core]`
  - *Note:* A task with internal resumable state is inconsistent with the stateless-retry model. Decided ([D31]({workspace}/decisions/Platform#31)): rather than a distinct task kind, every task run has an optional checkpoint slot, scoped to the task run and fenced, which the next attempt receives.
- **MLE 2.4** — Tolerate preemptible and spot capacity, resuming automatically after reclamation.
  - *Note:* Resumption uses the task run's checkpoint slot ([D31]({workspace}/decisions/Platform#31)).

### 3 · Tracking & registry

- **MLE 3.1** — Track every training run: parameters, metrics over time, artifacts, code version, dataset version, environment. `[cross-discipline]`
  - *Note:* Largely derived from [CORE 5.2](03-capabilities-core.md) where provenance is implemented correctly; to be confirmed rather than implemented twice.
- **MLE 3.2** — Register a model version with lineage back to the exact data, code, and run that produced it, and move it through lifecycle stages.
  - *Note:* Models are a specialized dataset type, so registration is publication and model lineage is dataset lineage ([D17]({workspace}/decisions/Platform#17)).
- **MLE 3.3** — Generate a model card from the run — intended use, training data, evaluation, fairness results, limitations.
- **MLE 3.4** — Require approval, and passing evaluation gates, before a model version can be promoted. `[shapes the core]`
  - *Note:* A workflow that pauses for human input is a distinct, long-lived execution state resumed externally. Decided ([D31]({workspace}/decisions/Platform#31)): an approval node's task run is suspended without a lease and resumed through the API; gated publication uses the same state. A gated commit leaves its attempt held until approval ([D48]({workspace}/decisions/Platform#48)).
- **MLE 3.5** — Package a model for deployment: framework-native, ONNX, or a self-contained container image.

### 4 · Inference & release

- **MLE 4.1** — Run batch and scheduled scoring pipelines using a registered model version.
- **MLE 4.2** — Deploy a model as a low-latency online endpoint with autoscaling. `[shapes the core]` `[deferred]`
  - *Note:* A long-lived service is not a workflow task, and supporting one extends the product into a serving platform as well as an orchestrator. Decided ([D39]({workspace}/decisions/Platform#39)): out of scope; models are served by external serving systems.
- **MLE 4.3** — Compare a candidate against the incumbent in shadow, canary, or champion–challenger mode.
- **MLE 4.4** — Roll back to a previous model version without rerunning training.

### 5 · Monitoring & lifecycle

- **MLE 5.1** — Log inference inputs and predictions for later analysis, subject to retention and privacy policy.
- **MLE 5.2** — Detect input drift, prediction drift, and concept drift against the training distribution. `[cross-discipline]`
- **MLE 5.3** — Measure live performance once ground-truth labels arrive, however delayed.
  - *Note:* Labels commonly arrive weeks after the prediction, requiring the same bitemporal joining as MLE 1.2.
- **MLE 5.4** — Trigger retraining on a schedule, on drift, or on performance decay.
- **MLE 5.5** — Run the full retrain → evaluate → gate → promote loop without manual steps, where policy allows it.
- **MLE 5.6** — Alert on model incidents, trace them back to a data or code change, and roll back.

### 6 · Engineering practice

- **MLE 6.1** — Lint a workflow, unit-test custom nodes, and run the pipeline against sample data in CI on every change. `[cross-discipline]`
  - *Note:* CI starts sample runs, normally on fixture datasets, and full-scale development runs as a service account within its clearance ([D50]({workspace}/decisions/Platform#50)).
- **MLE 6.2** — Promote a workflow across development, staging, and production with environment-specific configuration and connections. `[shapes the core]`
  - *Note:* Environment promotion requires the definition to be separable from its bindings, which is a further constraint on the IR. Decided ([D41]({workspace}/decisions/Platform#41)): definitions use logical names, mapped by a bindings file per environment. A sandbox is not an environment; development runs use a non-production environment's bindings, with reads falling back to production ([D50]({workspace}/decisions/Platform#50)).
- **MLE 6.3** — Specify a task's environment reproducibly through a dependency lockfile resolved to an image digest. `[cross-discipline]`
