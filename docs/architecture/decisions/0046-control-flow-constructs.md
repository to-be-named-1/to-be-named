# 46. Control-flow constructs

Date: 2026-10-11
Applies to: platform.webApp, platform.controlPlane, platform.unitRuntime

## Status

Accepted

Amends [2. Graph model](0002-graph-model.md)
Amends [31. Execution state model](0031-execution-state-model.md)
Amends [33. Automatic fusion](0033-automatic-fusion.md)
Amends [41. IR text form, round-trip and structure](0041-ir-text-form-round-trip-and-structure.md)

## Context

**Two levels of iteration** (D46). Running epochs or boosting rounds as graph iterations would pay a container start and a round trip through storage for every step of work that libraries already stop early. Graph loops are kept for steps worth scheduling, caching and retrying on their own, and in-unit execution covers loops whose rounds are cheap.

**Loops are always bounded** (D46). What is asked for as an unbounded loop is convergence, waiting or indefinite processing, and each has a better home: a bounded loop with an explicit outcome at its limit, triggers and readiness policies that hold no compute, or the long-lived execution of [D12](0012-streaming-readiness.md). A loop that might never end would hide the worst case of the plan and could hold capacity, write leases and protected inputs indefinitely.

**Column selectors rather than column loops** (D46). Column loops exist in node-at-a-time tools because nodes are configured for one column at a time. The engines here apply one expression across many columns in a single pass, keeping output schemas and column lineage derived at authoring time.

## Decision

The control-flow constructs the IR offers beyond those of [D2](0002-graph-model.md) and [D41](0041-ir-text-form-round-trip-and-structure.md), how loops may run, and what is deliberately left out.

- **Two levels of iteration.** Iteration inside a library — epochs, boosting rounds, solver steps, and early stopping such as Keras's `EarlyStopping` with `min_delta` and `patience` or XGBoost's `early_stopping_rounds` — stays inside a node, which reports its results through value outputs ([D41](0041-ir-text-form-round-trip-and-structure.md)) and resumes from its checkpoint slot ([D31](0031-execution-state-model.md)). A loop in the graph is for iterations that are steps of their own: expensive, separately cached or retried, or containing other nodes.
- **Carried state.** A loop frame may declare carried ports and values, each with an initial value and an output or expression giving its next value; each iteration receives what the previous one produced. This covers recursive loops, iterative algorithms and convergence across rounds, and makes adaptive search (DS 3.6) a pattern: a sampler node whose state is carried, with a map over its proposals in each round.
- **Loop scope.** Expressions in a loop's termination rule and carried values may reference `loop.index`, `loop.carried.<name>` and the current iteration's value outputs, extending the scope of [D41](0041-ir-text-form-round-trip-and-structure.md), so that a rule such as "stop when the improvement over the best so far has stayed below a margin for a given number of rounds" can be written.
- **Bounded loops and the limit.** Every loop keeps a maximum number of iterations ([D2](0002-graph-model.md)), which may be large and set by a parameter. Reaching it is an outcome chosen by the author: the loop fails, or it succeeds marked as not converged and exposes a `converged` value to downstream conditions. It is never silent.
- **Branch joins.** A merge node, or a port mode, takes the one input that was not skipped among alternative branches. The validator checks statically that the branches of an `if` or a `switch` are mutually exclusive; a join of a result and its failure fallback, built with run rules ([D41](0041-ir-text-form-round-trip-and-structure.md)), is resolved at run time.
- **Switch.** An n-way `switch` selects one branch by a CEL expression, with a default branch.
- **Loop execution mode.** From the first release a loop runs either unrolled, each iteration a task run with its own caching, retries and scheduling ([D2](0002-graph-model.md), [D31](0031-execution-state-model.md)), or inside one unit, where the body and its iterations share one container and state such as a model stays in memory. An in-unit loop is cached as one unit, records its number of iterations and the final value of its termination rule, and on retry resumes from the last completed iteration through its checkpoint slot ([D31](0031-execution-state-model.md)). It requires a body that could be fused ([D33](0033-automatic-fusion.md)).
- **Column selectors.** The node-type contract has a column-selector parameter type — by name, pattern, type or a combination — expanded against the input schema at authoring time, so that built-in nodes act on many columns in one expression, as Ibis selectors and DuckDB's `COLUMNS` allow. Output schemas stay derived ([D41](0041-ir-text-form-round-trip-and-structure.md)) and column lineage stays derived ([D10](0010-where-column-level-lineage-stops.md)).
- **Limits.** Pruning trials while they run, which needs concurrent trials to share intermediate scores (such as Optuna's `report` and `should_prune` with a median or Hyperband pruner), is not expressible between isolated units; a code node running the whole study is the documented route. Training that spans several machines is a matter of the unit model ([D32](0032-execution-unit-structure.md)), not of control flow, and is followed up with the execution backends (MLE 2.1).
- **Amends.** [D2](0002-graph-model.md): switch, branch joins, carried state and in-unit loops join the structured constructs, and an in-unit loop's iterations run within one task run. [D31](0031-execution-state-model.md): an in-unit loop records its iterations within one task run and resumes through the checkpoint slot. [D33](0033-automatic-fusion.md): a loop run inside one unit is an exception to the rule that no control flow sits between fused nodes. [D41](0041-ir-text-form-round-trip-and-structure.md): the expression scope gains `loop`, and the canvas gains switch and merge nodes.

## Rejected alternatives

- Unbounded loops. Convergence belongs in a bounded loop, waiting in triggers and readiness policies that hold no compute ([D16](0016-input-readiness-and-degraded-outputs.md), CORE 3.2), and indefinite processing in the long-lived execution of [D6](0006-streaming.md) and [D12](0012-streaming-readiness.md). An unbounded loop would hide the worst case of the plan ([D8](0008-cache-keying.md), [D34](0034-capacity-and-size.md)), could hold capacity, partition write leases and protected inputs indefinitely ([D14](0014-input-version-resolution.md), [D43](0043-scheduling-and-capacity.md)), would reintroduce at the level of the graph the non-termination that CEL removes ([D41](0041-ir-text-form-round-trip-and-structure.md)), and would grow the run trace without bound ([S5]({workspace}/documentation#3)).
- A dedicated column loop. A loop over columns would cost a unit per column and read the data once per column, would make output schemas dynamic and column lineage resolvable only after the run, and would lose type checking of column names; column selectors do the same in one pass. A map over a list of column names remains available where each column genuinely needs its own unit, such as one model per target.

## Follow-ups

- The exact syntax of carried state, the loop scope, branch joins and the switch, with the IR specification; a graph construct for pruning concurrent trials, if the code-node route proves insufficient.
