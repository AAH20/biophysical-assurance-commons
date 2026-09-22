# Changelog

## 0.2.0

- Added a strict v2 scenario contract with purpose- and scope-bound, time-limited synthetic consent, identity, proposal, intent, safety and approval inputs.
- Split validation, immutable domain models, pure policy, evidence verification, replay accounting, bounded parsing and evidence storage into separate modules.
- Recomputed policy decisions during receipt verification and kept benchmark labels out of decision receipts.
- Added optional HMAC authentication for local bundles, staged output publication, bounded JSON parsing and duplicate-key rejection.
- Added deployment architecture, integration contracts, threat model, and failure-path tests while retaining v1 scenario compatibility.

## 0.1.0

- Initial offline synthetic handover replay and hash-chained receipts.
