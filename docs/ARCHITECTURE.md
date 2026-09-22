# Architecture and trust boundaries

The only implemented runtime is offline synthetic replay. The expanded architecture is a roadmap with explicit boundaries so a future device adapter cannot silently turn a model proposal into an actuator command.

```mermaid
sequenceDiagram
    autonumber
    participant Sensor as Consented sensor or replay
    participant Enclave as Local data enclave
    participant Model as CV, BCI, or VLA model
    participant GRC as Governance gate
    participant Safety as Independent safety gate
    participant Human as Human supervisor
    participant Robot as Bounded actuator
    participant Record as Evidence recorder
    Sensor->>Enclave: Input and provenance
    Enclave->>Enclave: Validate consent, purpose, and retention
    Enclave->>Model: Minimum necessary representation
    Model-->>GRC: Proposal, uncertainty, model identity
    GRC->>GRC: Check consent, scope, identity freshness
    GRC-->>Safety: Authorized candidate or denial
    Safety->>Safety: Check interlocks and hazard envelope
    Safety-->>Human: Escalate if required
    Human-->>Robot: Time-limited approval if all gates pass
    Robot-->>Record: Action outcome or no-action event
    GRC-->>Record: Policy decision and reasons
    Record->>Record: Chain receipt to previous hash
```

**No direct actuation:** the model produces a proposal. A separately controlled safety gate and a bounded actuator gateway are required for lab work. If an input is missing, stale, unverifiable, or outside purpose/scope, deny and record the reason. The current CLI does not control actuators.

```mermaid
flowchart TB
    subgraph Public[Public, reproducible layer]
        SC[Versioned schemas]
        FX[Synthetic fixtures]
        PE[Reference policy evaluator]
        EV[Receipt verifier]
        BM[Benchmark definitions]
    end
    subgraph Restricted[Restricted deployment boundary]
        RAW[Raw faces, neural signals, tissue data]
        KEYS[Identity and encryption keys]
        CONS[Subject consent registry]
        OPS[Customer operations and topology]
    end
    subgraph Exports[Controlled exports]
        ASSERT[Short-lived assertions]
        AGG[Aggregated metrics]
        HASH[Anchored evidence digest]
    end
    RAW --> ASSERT
    KEYS --> ASSERT
    CONS --> ASSERT
    OPS --> AGG
    ASSERT --> PE
    PE --> EV
    EV --> HASH
    BM --> AGG
```

The public layer can receive a pseudonymous subject reference and a short-lived Boolean verification assertion. It must not receive raw biometric or neural data. A production assertion needs provenance, issuer authentication, replay protection, purpose binding, and an expiry. This prototype models only the last three concepts at a coarse level and is not a production IAM system.

## Evidence lifecycle

```mermaid
flowchart LR
    M[Versioned scenario manifest] --> V[Validate]
    V --> X[Deterministic replay]
    X --> D[Allow or deny with reasons]
    D --> R[Hash-chained receipts]
    R --> Q[Verify against scenario digest]
    Q --> P[Report and limitations]
    P --> A[Optional external anchor]
```

`sha256` in a receipt is computed from canonical JSON of all other receipt fields. `previous_sha256` links the prior receipt. The verifier recomputes the chain and checks it against the scenario supplied by the caller. Without an independently retained root or signed external anchor, an attacker who can replace every file can rewrite both evidence and report. No trust claim should go beyond that boundary.

## Interoperability choices

- **Clinical and neural data:** prefer BIDS or NWB metadata at the boundary; subject-level consent and governance are deployment obligations. No clinical decision support is planned for the public prototype.
- **Vision:** evaluate model outputs under shift and low-light/occlusion; retain imagery only under explicit data controls.
- **Biometrics:** default to local 1:1 verification assertions. A 1:N watchlist is a distinct, higher-risk evaluation with its own lawful basis and error metrics; it is not implemented here.
- **Digital twins:** record asset versions, sensor assumptions, simulated perturbations, and measured sim-to-real gaps. Simulation success is not field safety.
- **Evidence lake:** only sanitized receipts or approved aggregates enter a shared Iceberg/EvalLake table. Restricted raw data stays in the controlled enclave.
