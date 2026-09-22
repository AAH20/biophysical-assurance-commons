"""Build the shared, deterministic result envelope for synthetic replay."""

from __future__ import annotations

from . import __version__
from .evidence import digest

RESULT_VERSION = "bpa.assurance-result.v1"
REPOSITORY = "AAH20/biophysical-assurance-commons"


def from_replay(scenario: dict, report: dict, receipts: list[dict]) -> dict:
    failed = [
        receipt["result"]["request_id"]
        for receipt, action in zip(receipts, scenario["action_requests"])
        if (receipt["result"]["decision"] == "allow") != action["expected_allow"]
    ]
    return {
        "schema_version": RESULT_VERSION,
        "result_id": f"{scenario['scenario_id']}:{report['scenario_sha256'][:16]}",
        "producer": {
            "repository": REPOSITORY,
            "component": "assurance-core",
            "version": __version__,
        },
        "run": {"kind": "synthetic-reference", "environment": "synthetic"},
        "subject": {
            "pack_id": scenario["scenario_id"],
            "pack_version": scenario["schema_version"],
            "pack_sha256": report["scenario_sha256"],
        },
        "qualification": {
            "qualified": report["pass"],
            "failed_gates": failed,
            "score": None,
            "score_basis": "not-scored",
        },
        "evidence": {
            "artifact_sha256": digest(report),
            "receipt_root_sha256": report["last_receipt_sha256"],
            "verification": "local-replay",
        },
        "limitations": [report["limitations"]],
    }
