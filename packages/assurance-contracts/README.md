# Assurance contracts

This package contains the versioned public JSON Schemas and synthetic fixtures used by the Python reference evaluator. `scenario.v2.schema.json` is the current contract; v1 remains for compatibility. Fixtures are illustrative regression cases, not statistical benchmark populations or evidence from physical devices.

The runtime parser additionally enforces cross-field conditions that JSON Schema alone cannot express conveniently: increasing validity windows, ordered and unique action requests, finite confidence values, and synthetic-only execution. Changes to a published contract require a new version; a fixture should pin the version it uses.
