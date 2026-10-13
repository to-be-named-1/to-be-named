# 52. Agent identity by message signatures

Date: 2026-10-13
Applies to: platform.agent, platform.controlPlane

## Status

Accepted

Amends [40. Protocol between the control and data planes](0040-protocol-between-the-control-and-data-planes.md)
Amends [44. Minimum technology stack](0044-minimum-technology-stack.md)

## Context

[D44](0044-minimum-technology-stack.md) made the enrolled key the agent's identity, proven by mutual TLS by default, with HTTP Message Signatures (RFC 9421) as the alternative where a network inspects TLS, implemented when hybrid deployment is taken up. Proxies that inspect TLS cannot carry client certificates, and gateways that terminate TLS in front of a hosted control plane need passthrough or their own handling of client certificates. Two proofs make two paths, the second exercised only in some deployments, and mutual TLS needs a certificate authority that issues and rotates client certificates.

## Decision

In every deployment, the agent signs every request and the control plane signs every response with HTTP Message Signatures (RFC 9421), using Ed25519; message bodies are covered through Content-Digest (RFC 9530), and a response signature also covers the request it answers. Enrollment registers the agent's public key, bound to its tenant and pool, and the agent pins the control plane's signing key ([D44](0044-minimum-technology-stack.md)); keys are rotated and revoked in place of certificates. TLS still carries every connection, for confidentiality; mutual TLS and client certificates are not used. Replays are handled as [D44](0044-minimum-technology-stack.md) provides: idempotency, per-attempt sequence numbers and server-issued nonces, never wall-clock time.

## Consequences

- Signing is built in the first slice, not when hybrid deployment is taken up.
- Unsigned requests reach the application before they are rejected, so agent endpoints are rate-limited before signatures are verified.

## Rejected alternatives

- Mutual TLS by default, with signed messages where a network inspects TLS: two proofs, a client certificate authority to operate, and no passage through gateways that terminate TLS.
- An enrolled key that signs requests for short-lived access tokens, with signed unit specifications: a token readable by an inspecting proxy can be replayed during its lifetime, and messages from the agent are not protected end to end.

## Follow-ups

- A spike comparing implementations of RFC 9421 in Go, and signing as a transport and handler wrapper around ConnectRPC.
