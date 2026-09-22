# Threat model: synthetic runtime and proposed deployment

## Assets and adversaries

Protected assets include authorization decisions, consent state, identity assertions, policy versions, evidence integrity, actuator availability, and sensitive biometrics/neural/biological data. Relevant adversaries include a compromised model service, a malicious or mistaken operator, a forged assertion issuer, a tenant-crossing client, an attacker who edits evidence files, and a supplier or integrator who introduces an unsafe adapter. This model does not presume any particular government or organization is an adversary.

## Trust boundaries

1. Raw human or biological data remains in a controlled enclave. A public benchmark consumes synthetic or minimized metadata.
2. Model output is untrusted proposal data. Prompt, retrieval and sensor content have no policy authority.
3. Identity and consent assertions are separate from model confidence. A confident proposal cannot override revoked consent.
4. The physical safety controller is independent of governance policy; both must allow before an actuator gateway can act.
5. A hash chain proves internal consistency relative to a trusted scenario and retained root. A hostile host can rewrite all local files; use an external anchor and issuer authentication in a deployment.

## Attack-to-control map

| Attack or fault | Reference behavior | Deployment control still needed |
|---|---|---|
| Expired or revoked consent | Deny | Signed or authenticated live consent source, revocation propagation bound |
| Stale identity or approval | Deny | Issuer authentication, nonce, trusted time and key rotation |
| Model confidence laundering | Confidence never substitutes for consent/safety | Model provenance, calibration and independent hazard testing |
| RAG prompt injection into policy | No RAG authority in current runtime | Read-only retrieval, citations, fixed policy authority hierarchy |
| Modified receipt | Recomputed policy and hash chain reject inconsistent edit | External anchor and append-only protected store |
| Whole-bundle replacement | Not detectable by local hash alone | HMAC or signature with separately held key, remote anchor |
| Denial-of-service via huge JSON | Bounded scenario/evidence file sizes and action count | API rate limits, quotas, timeouts and backpressure |
| Sensor, gateway or outbox outage | Not integrated | Independent stop, fail-closed gateway, durable retry and incident procedure |
| Cross-tenant identity collision | Not integrated | Tenant-qualified identifiers and separate keys/storage |
| Compromised super-admin | Not integrated | Split duties, approvals, break-glass logging and hardware-rooted key custody |

The current repository should not accept actual personal data, biometric templates, neural recordings, wetware specimens, operational surveillance feeds, weapons-control inputs, or vehicle command channels. Those require separate review and controlled infrastructure. Public fixtures must remain synthetic.
