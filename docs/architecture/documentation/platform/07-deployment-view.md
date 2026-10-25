## Deployment view

The control plane never handles bulk data, so the planes can run in different places ([D21]({workspace}/decisions/Platform#21), [D22]({workspace}/decisions/Platform#22)). In every topology the same pull-based agent connects outward to the control plane and pulls work, and it mints storage credentials and resolves secrets inside the environment it runs in ([D29]({workspace}/decisions/Platform#29), [D40]({workspace}/decisions/Platform#40)).

### Topologies

Customers trade convenience for control, from fully managed to self-hosted ([D22]({workspace}/decisions/Platform#22)).

| Option | Operations | Compute | Storage | Typical customer |
|---|---|---|---|---|
| Fully managed | Vendor | Vendor | Vendor | Trials, and organizations that do not want to manage their own data-plane infrastructure |
| Managed, customer storage | Vendor | Vendor | Customer | Integration with an existing lakehouse; no lock-in |
| Hybrid | Vendor | Customer | Customer | Regulated and sovereignty-sensitive organizations |
| Self-hosted | Customer | Customer | Customer | Open-source users, air-gapped environments |

Bring-your-own-compute is the primary model: execution runs on the customer's own infrastructure and the vendor coordinates; hybrid and self-hosted are the first-class topologies ([D22]({workspace}/decisions/Platform#22)). With customer storage but vendor compute, data still passes through the vendor's machines while it is processed, so strict sovereignty requires hybrid. The three topologies with a hosted control plane belong to the proprietary edition; self-hosting, the agent and deployment by role are open ([D53]({workspace}/decisions/Platform#53)).

### Single machine

![](embed:deployment-single-machine)

The complete platform runs on one host as containers, for evaluation, development and small teams ([CORE 2.17]({workspace}/documentation#3)). One control-plane process runs every role (`all`) ([D47]({workspace}/decisions/Platform#47)). The agent launches units as containers on the same Docker engine, exactly as it launches pods elsewhere ([D29]({workspace}/decisions/Platform#29)). The bundled object storage is the default storage target of an installation without object storage of its own, and any S3-compatible or cloud object storage can be configured instead ([D4]({workspace}/decisions/Platform#4), [S25]({workspace}/documentation#7.27)). The built-in secret store holds secrets where no secret manager exists ([D40]({workspace}/decisions/Platform#40)).

### Kubernetes

![](embed:deployment-kubernetes)

The view shows a highly available installation; the minimum is one process with each of the roles `api`, `worker` and `candidate`, and two or more processes with `api` and with `candidate` keep the API and the leader available through a failure ([D47]({workspace}/decisions/Platform#47)). The control plane runs in pods by role. Pods with the `api` role sit behind a Service that selects them by their template, so a replacement pod rejoins it with the same roles. Pods with the `worker` role plan runs, run the reconciler's loops and deliver events. Several pods with the `candidate` role compete for leadership; the one that wins holds the `leader` role, labels its own pod with it, and an agent Service selects that label, so the leader needs permission to patch its own pod. An agent call that reaches another pod fails and is retried. Each pod reports readiness for the role that receives traffic through it ([D47]({workspace}/decisions/Platform#47)).

PostgreSQL 17 or later runs in the cluster or as a managed service. Leadership holds its lock on a session made directly to Postgres, not through a transaction-pooling proxy ([D44]({workspace}/decisions/Platform#44), [D47]({workspace}/decisions/Platform#47)).

The data plane runs in its own namespace, where each agent pool runs several replicas, since leases belong to the pool rather than to a replica, and launches its unit pods; an installation may run several pools ([D40]({workspace}/decisions/Platform#40)). Agents only connect outward, so they may also run in other clusters ([D22]({workspace}/decisions/Platform#22)).

### Other self-hosted deployments

Without Kubernetes, processes run by role on virtual machines. Only `api` processes are registered with the load balancer in front of the API, and a health check on the agent endpoint, which only the leader passes, routes agents to the leader; retries remain the fallback ([D47]({workspace}/decisions/Platform#47)). Agents may also drive an HPC cluster, whose units run as Slurm jobs, commonly through Apptainer, or a cloud batch service ([D22]({workspace}/decisions/Platform#22)).

### Hybrid

![](embed:deployment-hybrid)

An enterprise can adopt the hosted product without moving data out of its own cloud account or HPC cluster. This is a strong argument for regulated and data-sovereign customers, and it exists only because the control plane never touches bulk data.

The vendor hosts the interface and control planes, and the data plane and storage stay in the customer's cloud account or HPC cluster ([D22]({workspace}/decisions/Platform#22)). A hosted control plane scales by cells, each with its own database and set of tenants, and each cell routes to its roles as a self-hosted installation does ([D47]({workspace}/decisions/Platform#47)).

Agents connect outward only; no inbound connection into the customer's network is needed ([D22]({workspace}/decisions/Platform#22)). Credentials are minted, and secrets resolved, inside the customer's environment, so the hosted control plane holds neither ([D40]({workspace}/decisions/Platform#40)). Only metadata, statistics, events and pre-computed previews cross to the hosted planes; previews and samples obey the classification of their source dataset, and a customer may disable them for sensitive datasets ([D22]({workspace}/decisions/Platform#22)). Logs and metrics go to the vendor's observability service or stay in the customer's own stack, with live tailing proxied through the agent ([D22]({workspace}/decisions/Platform#22), [D40]({workspace}/decisions/Platform#40)). Image builds and the image registry may run in the customer's environment ([D22]({workspace}/decisions/Platform#22)).

Fully managed, and managed with customer storage, have the same shape, with the agents on the vendor's side, and for fully managed the storage too.
