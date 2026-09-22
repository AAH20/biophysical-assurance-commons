# Candidate integration map

These are **proposed interfaces**, not installed or validated adapters. Each real integration needs a contract test, security review, version pin, failure-mode study, and provenance/consent review. Existing repository claims are not inherited by this benchmark.

The normalized fields, acceptance tests and data boundaries are specified in [docs/INTEGRATIONS.md](../docs/INTEGRATIONS.md).

| Project | Candidate role | Minimum export | Boundary condition |
|---|---|---|---|
| [GRC Claw](https://github.com/AAH20/GRC_Claw) | Policy/evidence control plane | Versioned allow/deny decision and reason code | No implicit override of independent safety gate |
| [Physical AI Governor](https://github.com/AAH20/physical-ai-governor) | Physical action policy | Bounded proposal and policy result | Research prototype until lab validation |
| CyborgBench (candidate local project) | Benchmark fixture source | Manifest, seed, labels, provenance | Separate benchmark claims from verified results |
| [Identity Fabric Benchmarks](https://github.com/AAH20/identity-fabric-benchmarks) | Identity assertion tests | Short-lived assertion and assurance level | Raw biometric templates stay local |
| EvalLake (candidate local project) | Evidence aggregation | Sanitized receipt, benchmark metadata | Do not ingest raw protected signals by default |
| AI Governance Evidence Graph (candidate local project) | Cross-system evidence links | Content digest and controlled provenance edge | Graph membership does not prove source truth |
| Robot Black Box | Event-recorder interface | Action outcome and decision digest | External project; no runtime connector yet |
| NVIDIA Isaac GR00T | VLA proposal source | Model/version, action proposal, confidence or uncertainty | No direct actuator permission |
| Obsidian / Cognee / LangGraph | Context and workflow candidates | Cited, scoped policy context | Retrieved text cannot change policy authority |

For a real adapter, expose a stable `proposal` or `assertion` payload, never a raw unrestricted device command. Sign or authenticate issuers, bind assertions to subject/purpose/scope/time, and define expiry and revocation. Contract tests should include missing fields, forged issuer, stale timestamps, model uncertainty, network partition, and mismatched subject.
