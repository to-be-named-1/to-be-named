## Constraints

### Principles

- **Data-engineering practice first.** Standard data-engineering practice comes first; reproducibility and the constraints it brings are opt-in. Every proposed rule is tested: if it constrains a standard practice, or adds storage or compute cost, for the sake of reproducibility, it is optional and off unless a team turns it on ([D36](../../decisions/0036-data-engineering-practice-first-reproducibility-by-choice.md)).
- **Open core.** The platform stays open and fully operable for single users and small teams who self-host it. Features that concern organisations are proprietary, behind extension interfaces with open default implementations ([D5](../../decisions/0005-distribution-and-tenancy.md)). Proprietary elements of the model carry the `Commercial` tag, and the seams for them the `Extension point` tag.
- **Isolation everywhere.** Tenant and project isolation is enforced on every access path, including in single-tenant self-hosted installations ([D30](../../decisions/0030-tenancy-and-isolation-enforcement.md)).

### Scope

Excluded by decision: deep learning and visual neural-network design; a native streaming runtime, with the seams for later streaming kept ([D6](../../decisions/0006-streaming.md), [D12](../../decisions/0012-streaming-readiness.md)); container-free local execution ([D11](../../decisions/0011-execution-modes.md)); and online model serving, delegated to external serving systems ([D39](../../decisions/0039-online-model-serving.md)). The first development slice is set by [D29](../../decisions/0029-first-development-slice.md); its scope, and what follows it, are kept in the roadmap of the workspace documentation.

### Technology

The minimum technology stack is fixed ([D44](../../decisions/0044-minimum-technology-stack.md)): Go for the control plane and the agent, Python for unit runtimes, PostgreSQL 17 or later as the control plane's only stateful dependency ([D47](../../decisions/0047-control-plane-structure.md)), protobuf with ConnectRPC between every component, and a React single-page application for the interface. Section 4 lists every technology choice. Not yet chosen: the authentication and identity stack, the observability stack, and the image builder and registry.

### Organisation

The repository is private. Its licence is chosen before it is made public or accepts external contributions, whichever comes first ([D5](../../decisions/0005-distribution-and-tenancy.md), [D29](../../decisions/0029-first-development-slice.md)).
