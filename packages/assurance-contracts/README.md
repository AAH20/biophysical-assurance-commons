# Assurance contracts

This package contains the versioned public JSON Schemas and synthetic fixtures used by the Python reference evaluator. `scenario.v2.schema.json` is the current contract; v1 remains for compatibility. Fixtures are illustrative regression cases, not statistical benchmark populations or evidence from physical devices.

`assurance-result.v1.schema.json` defines the cross-repository summary contract for this monorepo, Egypt Digital Trust Map, and Identity Fabric Benchmarks. It separates a synthetic reference regression from a measured provider run, carries the exact pack digest and evidence root, and never treats a missing measurement as zero risk. The complete source report remains the canonical detailed artifact.

The runtime parser additionally enforces cross-field conditions that JSON Schema alone cannot express conveniently: increasing validity windows, ordered and unique action requests, finite confidence values, and synthetic-only execution. Changes to a published contract require a new version; a fixture should pin the version it uses.
