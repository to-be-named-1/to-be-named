## Constraints

### Principles

- **Data-engineering practice first.** Standard data-engineering practice comes first; reproducibility and the constraints it brings are opt-in. Every proposed rule is tested: if it constrains a standard practice, or adds storage or compute cost, for the sake of reproducibility, it is optional and off unless a team turns it on ([D36]({workspace}/decisions/Platform#36)).
- **Open core.** The platform stays open and fully operable for single users and small teams who self-host it. Features that concern organizations are proprietary, behind extension interfaces with open default implementations ([D5]({workspace}/decisions/Platform#5)). Proprietary elements of the model carry the `Commercial` tag, and the seams for them the `Extension point` tag.
- **Isolation everywhere.** Tenant and project isolation is enforced on every access path, including in single-tenant self-hosted installations ([D30]({workspace}/decisions/Platform#30)).

### Scope

Excluded by decision: deep learning and visual neural-network design; a native streaming runtime, with the seams for later streaming kept ([D6]({workspace}/decisions/Platform#6), [D12]({workspace}/decisions/Platform#12)); container-free local execution ([D11]({workspace}/decisions/Platform#11)); and online model serving, delegated to external serving systems ([D39]({workspace}/decisions/Platform#39)). The first development slice is set by [D29]({workspace}/decisions/Platform#29); its scope, and what follows it, are kept in the roadmap of the workspace documentation.

### Technology

The minimum technology stack is fixed ([D44]({workspace}/decisions/Platform#44)): Go for the control plane and the agent, Python for unit runtimes, PostgreSQL 17 or later as the control plane's only stateful dependency ([D47]({workspace}/decisions/Platform#47)), protobuf with ConnectRPC between every component, and a React single-page application for the interface. Section 4 lists every technology choice. Not yet chosen: the authentication and identity stack, the observability stack, and the image builder and registry.

### Organization

The repository is private. Its license is chosen before it is made public or accepts external contributions, whichever comes first ([D5]({workspace}/decisions/Platform#5), [D29]({workspace}/decisions/Platform#29)).
