## Quality requirements

The quality goals are stated in the [introduction](01-introduction-and-goals.md); this section records how the platform behaves when a plane fails.

### Failure independence

| Outage | Effect |
|---|---|
| Control plane | Running units continue and buffer their commit requests until it returns. No new work is dispatched and no result becomes current. |
| Data-plane node | Its leases expire and affected units are retried elsewhere. Fencing rejects any late commit from the lost attempts. |
| Observability | Runs continue unaffected. Logs and metrics are buffered or partially lost; no decision depends on them. |
| Interface | Scheduled work continues; people cannot start, change or inspect work until it returns. |
