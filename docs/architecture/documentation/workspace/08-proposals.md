## Proposals

Proposals raised and not yet confirmed; a confirmed proposal becomes a decision or an amendment to one.

### Two-level warehouse connection policy (amends D28)

[D28]({workspace}/decisions/Platform#28) states that a connection without compute rights makes pushdown unavailable and the planner extracts instead. In Snowflake, however, reading data at all runs a query on a compute cluster, so a connection with no compute rights cannot be extracted from either. Proposed correction: two levels.
- **Read:** only the queries needed to extract (column selection and row filters), on the named compute cluster.
- **Pushdown:** any transformation the planner pushes down.

Read would be the minimum for any connection the platform uses. Not verified: whether tables stored in Iceberg format can be read directly from their files without Snowflake compute.

### Details recorded in D28 to review

- When a pinned plan can no longer be honored, the run stops before execution until the author accepts a new plan. The alternative is falling back to the new plan with a warning.
- How a credit budget is enforced is attached to [S22](07-open-items.md#7.22) and not yet defined.
- Unit grouping under a pinned plan: compared with the pinned plan and reported, but not enforced, since regrouping changes no cache keys ([D8]({workspace}/decisions/Platform#8), [D33]({workspace}/decisions/Platform#33)). Agreed as the direction; recorded in [D28]({workspace}/decisions/Platform#28) when its review is taken up.

### Repartition key (D25, CORE 2.26)

The planner takes the key from the grouping a node declares. The alternative is that authors place repartition steps themselves.

The first two concern warehouses and are settled when warehouse pushdown is taken up.
