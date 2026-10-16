## Components

![](embed:components-control-plane-execution)

![](embed:components-control-plane-requests)

The server's components are grouped by the bounded contexts of [D47]({workspace}/decisions/Platform#47). Each context owns a schema in the control-plane database and a Go package tree; other contexts use its Go interface and never read its tables. Three components belong to no context. The first view shows how a run gets from its trigger to the commit of its outputs, and the second how people and automation reach the platform; the authorization layer, the dataset catalog and the run driver appear in both. The database is left out of both views: the [database documentation]({workspace}/documentation/Platform/Control-plane%20database#3) lists which components reach each schema.

The actions of each component are listed by the role that performs them. A replica with any one of a component's roles performs that role's actions ([D47]({workspace}/decisions/Platform#47)). The role `candidate` lets a process compete for leadership, and the candidate that wins holds the role `leader` until it loses leadership, so actions under `leader` run on one process at a time; the components tagged Leader only have no other role.

### Identity and tenancy

| Component | Responsibility | Actions by role |
|---|---|---|
| Identity and membership | Manages tenants, principals, memberships and clearance, service accounts, projects, and tenant resources with their grants. | **api:** commands and queries on tenants, principals, memberships and clearance, service accounts, projects, resources and their grants to projects |
| Authorization layer | Authorizes every API method and every run against roles, project scope and clearance; the policy behind it is an extension point. | **api:** authorizes every API method before its handler runs<br>**worker:** checks a run's access while the planner binds resources: under its project identity, or the starter's clearance for a development run |
| Audit | Records the audit trail of user and administrative actions; export to external sinks is an extension point. | **api:** records user and administrative actions, and serves the audit log to Admins<br>**worker:** records acts the platform performs for users, such as deploying commits from the deploy branch |

### Authoring

| Component | Responsibility | Actions by role |
|---|---|---|
| Definitions and drafts | Manages workflow and dataset definitions, drafts, platform-held versions and environment bindings. | **api:** drafts, explicit commits, platform-held versions and environment bindings<br>**worker:** records the versions found on the deploy branch |
| Compiler | Parses, migrates and type-checks each definition version, flattens composites, checks control flow, intervals and single producers, and computes semantic fingerprints. | **api:** compiles versions committed through the API<br>**worker:** compiles versions found on the deploy branch |
| Git synchronization | Pushes authors' commits to the git host and watches the deploy branch. | **api:** pushes authors' commits, with the author recorded as author and the platform as committer<br>**worker:** watches the deploy branch |
| Deployment | Deploys committed definitions as an act of the platform, checking governed fields. | **api:** deploys on request, and approves commits that change governed fields<br>**worker:** deploys each new commit on the deploy branch, holding back one that changes a governed field without the permission |

### Plugin registry

| Component | Responsibility | Actions by role |
|---|---|---|
| Plugin registry | Manages format types and their implementations, node types, the implementations each project allows, and images. | **api:** manages format types, implementations, node types, allowed implementations and images<br>**worker:** answers the compiler's and the planner's lookups |

### Catalog

| Component | Responsibility | Actions by role |
|---|---|---|
| Dataset catalog | Manages datasets and their versions: answers queries, resolves the versions a run reads, enforces the single producer and the order of versions, and makes outputs current in the commit transaction. | **api:** dataset queries, and owner acts such as releasing a quarantined version<br>**worker:** resolves the versions a run reads, at run start<br>**leader:** makes outputs current in the dispatcher's commit transaction |
| Cache index | Finds reusable outputs by input-addressed key, through the eligibility filter. | **worker:** computes expected reuse for the planner, and makes the authoritative lookup for a run's first task runs<br>**leader:** makes the authoritative lookup for task runs created as runs advance |
| Projection and publication scheduling | Schedules, in version order, the table work that follows a commit: Iceberg projections for external engines, and commits to storage targets that have their own commit. | **worker:** handles commit events, and schedules projections for projected datasets and publications for datasets stored as tables with their own commit ([D55]({workspace}/decisions/Platform#55)) |
| Collection marking | Marks what retained, cached, pinned or protected manifests reference, so that agents can delete the rest. | **worker:** marks referenced artifacts in its work-row loop, for agents' maintenance tasks to delete the rest |
| Probe scheduling | Batches source probes per pool and keeps each external source's last probed position. | **worker:** takes a run's probe requests and batches them per pool<br>**leader:** hands batches to the dispatcher, keeps the returned positions and wakes the waiting run |
| Adoption | Brings existing tables and files under the platform: path-pattern mappings, baselines and switchover. | **api:** owner acts: path-pattern mappings, baselines and switchover<br>**worker:** follows layout checks, baseline scans and observation as work rows |

### Planning

| Component | Responsibility | Actions by role |
|---|---|---|
| Planner | Turns a run's resolved inputs into a plan: bindings, placement, estimates, repartitioning, fusion into units, sizing, pools and expected reuse. | **worker:** plans each run once, after its inputs are resolved |

### Orchestration

| Component | Responsibility | Actions by role |
|---|---|---|
| Run driver | Resolves a run's inputs, creates task runs as the run reaches them, decides retries, suspends and resumes, and ends the run. | **api:** commands on runs: cancel, pause, resume and approvals<br>**worker:** run start: resolves inputs, has the run planned, and records the run, its plan and its first task runs<br>**leader:** advancement after agents' reports: creates task runs, decides retries and ends runs; holds attempt rows for the dispatcher |
| Reconciler | Runs the level-triggered loops for schedules and triggers, runs waiting for inputs, materialization requests, backfills and backstop sweeps. | **worker:** claims due work rows for schedules and triggers, runs waiting for inputs, materialization requests, backfills and backstop sweeps |

### Dispatch

| Component | Responsibility | Actions by role |
|---|---|---|
| Scheduler | Orders and admits ready work per capacity domain: fair share, quotas, write leases and preemption. | **leader:** orders and admits ready work per capacity domain, takes write leases and preempts lower classes where a pool allows it |
| Dispatcher | Creates attempts and their unit specifications, offers work, holds lease renewals in memory, signals cancellation, and checks fencing tokens and write leases on commit requests. | **leader:** drives the live lifecycle of attempts, offers probes and maintenance tasks, and handles commit requests |
| Agent gateway | Receives agents' calls and long-polls, checks their message signatures against the keys enrolled with the dispatcher, and signs responses. | **leader:** receives agents' calls and long-polls, verifies their signatures and signs responses |

### Provenance

| Component | Responsibility | Actions by role |
|---|---|---|
| Provenance read model | Serves lineage, reproducibility tiers, verification and comparator verdicts, read from the catalog and orchestration. | **api:** serves lineage, reproducibility tiers, verification and comparator verdicts<br>**worker:** updates the read model from catalog and orchestration events |

### Outside the contexts

| Component | Responsibility | Actions by role |
|---|---|---|
| API layer | Serves the ConnectRPC API to the web application, the CLI and CI, and serves the single-page application; authentication is an extension point. | **api:** serves the API and the single-page application, and authenticates callers |
| Outbox and work-row delivery | Delivers outbox rows to their handlers and runs work rows, with claims, retries and dead letters. | **worker:** delivers outbox rows whose handlers can run on any replica, such as projection and publication scheduling and reconciler wake-ups, and runs work rows<br>**leader:** delivers the rows that feed the leader's in-memory state: approvals and releases that make suspended task runs ready, commands such as cancel and pause for running attempts, task runs made ready on other replicas, and changes to quotas and fair-share weights ([D43]({workspace}/decisions/Platform#43), [D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48))<br>Each handler declares the role that runs it, so only the leader claims rows for leader handlers. |
| Leadership | Elects the leader with a session-level advisory lock and fences leader-only writes by epoch. | **candidate:** competes for the advisory lock<br>**leader:** increments the epoch, waits out the old leader's transactions, starts and stops the leader loops and opens the agent port; drops the role when its session ends |

### Attempt lifecycle

A task run and its attempts form one aggregate, owned by orchestration: at most one live attempt, dense attempt numbers, and commits only from the current attempt. The fencing token is the task run and the attempt number ([D47]({workspace}/decisions/Platform#47), [D48]({workspace}/decisions/Platform#48)). Every attempt row is written, and every fencing token checked, through the run driver's interface; the dispatcher never writes orchestration's tables, and the run driver never talks to agents.

- **The dispatcher drives the live attempt.** It creates the attempt and its unit specification, persisted before the attempt is offered; offers it; accepts the claim; holds lease renewals in memory; names attempts to stop in each renewal response; signals cancellation and preemption; records state-bearing messages; and handles commit requests ([D40]({workspace}/decisions/Platform#40), [D48]({workspace}/decisions/Platform#48)).
- **The run driver decides what follows.** When an attempt ends, it retries the task run by failure class and retry budget, or advances the run ([D31]({workspace}/decisions/Platform#31), [D47]({workspace}/decisions/Platform#47)).

### Transactions across contexts

A transaction crosses contexts only in the three cases [D47]({workspace}/decisions/Platform#47) names: the data commit, including publication groups; the batch from one agent message; and run start, which records the run, its plan and its first task runs. The component that opens the transaction passes it through the other contexts' Go interfaces and commits it. Each context writes only its own tables, and the producer of an event writes its outbox rows in the same transaction ([D48]({workspace}/decisions/Platform#48)). Locks are taken in one order — the epoch check, task-run rows, write-lease rows, dataset head rows, then the outbox insert — so these transactions cannot deadlock, and a late commit is serialized against the retry that supersedes it ([D47]({workspace}/decisions/Platform#47)).
