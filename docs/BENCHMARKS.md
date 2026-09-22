# Evaluation contract and staged bottlenecks

Every result must state fixture version, test population and exclusions, environment, model version, policy version, denominator, confidence interval when sampling, and whether the data are synthetic, simulated, consented lab, or field. A blank cell is **unqualified**, never zero risk.

| Component | Primary measures | Critical failure | Early bottleneck | Later bottleneck |
|---|---|---|---|---|
| Consent and purpose | Unauthorized allow count / unauthorized attempts; revocation-to-denial latency | Any unauthorized action | Correct event ordering | Cross-system propagation and clock integrity |
| Identity assertion | 1:1 FMR and FNMR at fixed threshold; assertion age; subgroup confidence intervals | Stale or mismatched assertion accepted | No representative consented cohort | Demographic shift, presentation attacks, issuer trust |
| Vision / YOLO | Per-class precision/recall, calibration, latency, energy, shift delta | Unsafe object/state miss | Dataset rights and labels | Edge reliability and long-tail environments |
| BCI intent | Unintended activation / exposure time; missed intentional commands; calibration drift | Uncommanded actuation | Subject variability | Long-term signal drift and nonstationarity |
| Wetware research | Viability, batch variance, reproducibility, chain-of-custody completeness | Missing consent/provenance or uncontrolled experiment | Standardized metadata | Replication across labs and batches |
| VLA / robot | Task success, unsafe actions / attempts, interruption latency, recovery, energy | Action outside safety envelope | Sim coverage | Sim-to-real and hardware wear |
| Digital twin | Scenario coverage, fidelity by variable, measured reality gap | Unsupported field-safety inference | Versioning and sensors | Continuous calibration |
| Evidence | Valid-chain fraction; field completeness; external-anchor lag | Missing or contradictory evidence | Canonical schemas | Multi-party custody and retention |

**Decision rule:** a run is qualified only if every mandatory governance and safety gate passes. Report model quality separately. Never average a safety violation away with perception accuracy. The v0.1 `pass` flag is a fixture-level regression result only: it compares decisions to explicit expectations, with no statistical claim.

## Measurable phases

| Phase | Evidence tier | Exit criterion | What it does not establish |
|---|---|---|---|
| 0 | Synthetic unit replay | Deterministic expected decisions; tamper detection | Real model or hardware behavior |
| 1 | Public simulation | Seeded scenario families and perturbations; coverage map | Human safety |
| 2 | Constrained lab | Supervised trials, calibrated sensors, independent interlocks, incident log | Unsupervised deployment |
| 3 | Limited pilot | Pre-registered metrics, site-specific hazard analysis, data agreements | Universal generalization |
| 4 | Scaled operations | Continuous monitoring, drift alerts, audit sampling, incident response | Certification without applicable independent assessment |

## Benchmark hygiene

For biometric evaluation, publish 1:1 and 1:N measures separately. In 1:1, false match rate (FMR) is false matches divided by impostor comparisons; false non-match rate (FNMR) is false non-matches divided by genuine comparisons, each at a stated threshold. In 1:N, use false positive identification rate (FPIR) and false negative identification rate (FNIR) with gallery size and search protocol. Aggregates should be broken out by relevant cohorts where lawful and statistically meaningful, and small-cell data must be protected.

For BCI, count unintended commands per exposure hour and per opportunity, with both denominators disclosed. Keep train/test separation by subject, session, and time. For robotics, record attempted actions, unsafe proposals, blocked unsafe proposals, executed unsafe actions, and intervention latency; a blocked unsafe proposal is a governance success but still a model failure. For wetware, do not rank against silicon systems by one scalar; repeatability, tissue viability, protocol metadata, and ethics review are separate requirements.

No universal numerical threshold is asserted here. Thresholds should come from the use case's hazard analysis, legal duties, and a pre-registered test plan before benchmark execution.
