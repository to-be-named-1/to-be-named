## Data science (DS)

Exploratory and experimental work, delivered largely as a curated palette over established libraries. The value added is that an experiment becomes a reproducible, shareable artifact rather than an untracked notebook. Node granularity — one node per estimator or one node per script — is settled by [D1]({workspace}/decisions/Platform#1).

### 1 · Load & understand

- **DS 1.1** — Load tabular, text, image, time-series, and geospatial data from files, databases, and object storage.
- **DS 1.2** — Infer a schema, enforce it, and coerce types with a record of what was coerced.
- **DS 1.3** — Profile a dataset: distributions, cardinality, missingness, correlations, candidate keys.
- **DS 1.4** — Work against a sample of a large dataset while designing, then run the same graph at full scale. `[shapes the core]`
  - *Note:* Sample-then-scale is the primary interaction loop of the builder, and must be a platform affordance rather than hand-wired by the user. Sample runs may use an uncommitted draft, whose IR is recorded with the run ([D45]({workspace}/decisions/Platform#45)). Decided ([D50]({workspace}/decisions/Platform#50)): sample runs sample at the selection boundary by referential subsetting and write only run-scoped artifacts, and runs from the canvas may use warm session units; full-scale development runs commit to a sandbox.

### 2 · Prepare

- **DS 2.1** — Clean data: missing values, outliers, duplicates, type repair, text normalization.
- **DS 2.2** — Reshape: join, aggregate, pivot, explode, window, resample. `[cross-discipline]`
- **DS 2.3** — Encode and scale features as transforms that are fitted on training data only and applied everywhere else.
- **DS 2.4** — Engineer features: derived columns, interactions, binning, date parts, aggregations, text and image featurization.
- **DS 2.5** — Select features by filter, wrapper, and embedded methods.
- **DS 2.6** — Reduce dimensionality — PCA, UMAP, t-SNE — for modeling and for visualization.
- **DS 2.7** — Address class imbalance through resampling, synthetic minority sampling, or class weighting.
- **DS 2.8** — Prevent leakage structurally: the platform warns when a graph fits a transform on data the split says it should not see. `[shapes the core]`
  - *Note:* A material differentiator over notebook-based work, possible because the graph makes data flow explicit. It requires the IR to model split semantics rather than ports alone. The platform warns rather than refuses, and the author may override ([D36]({workspace}/decisions/Platform#36)).

### 3 · Experiment

- **DS 3.1** — Split data by random, stratified, grouped, and temporal strategies.
  - *Note:* The platform warns when a split other than a temporal one is used on time-indexed data, and the author may override ([D36]({workspace}/decisions/Platform#36)). Undetected random cross-validation on a time series is the most common invalidating error in applied work.
- **DS 3.2** — Cross-validate, including nested CV for honest tuning and forward-chaining CV for time series.
- **DS 3.3** — Train traditional supervised models: linear and regularized, tree ensembles, gradient boosting, SVM, kNN, naive Bayes.
- **DS 3.4** — Run unsupervised work: clustering, anomaly detection, association rules, topic models.
- **DS 3.5** — Build time-series models: lag and rolling features, decomposition, classical and ML forecasters, horizon evaluation.
- **DS 3.6** — Tune hyperparameters by grid, random, Bayesian, and successive-halving search, with early stopping of unpromising trials. `[shapes the core]`
  - *Note:* Search over a subgraph is [CORE 2.3](03-capabilities-core.md) fan-out with an added feedback loop: the sampler requires results from completed trials to propose subsequent ones, which a static DAG cannot express. Decided ([D46]({workspace}/decisions/Platform#46)): a loop whose carried state is the sampler's, with a map over its proposals in each round; pruning trials while they run is done inside a code node running the whole study.
- **DS 3.7** — Combine models by voting, bagging, boosting, and stacking.
- **DS 3.8** — Load a pretrained model and use it as a node, as a featurizer or as a predictor.

### 4 · Evaluate & explain

- **DS 4.1** — Compute metric suites appropriate to the task type, with confusion matrices, ROC and PR curves, and calibration plots.
- **DS 4.2** — Compare every model against a naive baseline by default.
- **DS 4.3** — Select a decision threshold against a cost matrix rather than accepting 0.5.
- **DS 4.4** — Analyze errors and residuals, and evaluate performance on slices of the data rather than only in aggregate.
- **DS 4.5** — Explain a model: permutation importance, SHAP, partial dependence and ICE, surrogate models, counterfactuals.
- **DS 4.6** — Audit fairness across protected attributes with standard group metrics.
- **DS 4.7** — Compare runs side by side — parameters, metrics, and artifacts — and quantify whether a difference is meaningful. `[cross-discipline]`

### 5 · Communicate

- **DS 5.1** — Produce visualizations from any node: distributions, relationships, time series, geospatial, model diagnostics.
- **DS 5.2** — Assemble a run's outputs into a report or dashboard that refreshes when the workflow re-runs.
- **DS 5.3** — Interoperate with notebooks: import a notebook as a pipeline, export a pipeline as one, or open a notebook against a node's output.
  - *Note:* The principal adoption path. Existing notebook practice continues in parallel, so the platform must interoperate with it and provide a defined route to promote a notebook into a pipeline.
- **DS 5.4** — Export figures, tables, and result sets in publication-ready formats.
