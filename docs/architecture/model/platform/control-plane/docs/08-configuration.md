## Configuration

### Roles

The server is one binary. Each process is configured with one or more roles, and the elected one also holds `leader` ([D47]({workspace}/decisions/Platform#47)).

| Role | What a process with the role runs |
|---|---|
| `api` | The platform API and the single-page application; agent calls that reach it are refused as retryable |
| `worker` | Planning, reconciler loops, outbox and work-row handlers that can run on any replica, watching the deploy branch, and collection marking |
| `candidate` | Eligibility for leader election: leadership runs on every such process |
| `all` | Everything; the default, so that a single-machine installation runs one process |
| `leader` | Never configured: the candidate that wins the election holds it until it loses leadership, and runs the agent gateway, the scheduler, the dispatcher, run advancement and the outbox handlers that feed the leader's state; on Kubernetes it is the pod label the agent Service selects |

A process may combine roles. A deployment needs at least one process with each of `api`, `worker` and `candidate`, and several candidates for the leader to fail over. Deployment by role and high availability are part of the open edition ([D53]({workspace}/decisions/Platform#53)).

### Limits set in the platform

Tenant Admins set project quotas, fair-share weights and per-unit ceilings on pools; a Maintainer may set lower limits within a project, such as per-workflow concurrency ([D45]({workspace}/decisions/Platform#45), [D47]({workspace}/decisions/Platform#47)). They are held in the database, not in the server's configuration.

### Timings

The heartbeat, the lease, the grace period after a restart and the hard limit for attempts that have stopped renewing have defaults set in [D43]({workspace}/decisions/Platform#43), and all are configurable.

