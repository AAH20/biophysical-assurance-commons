"""Replay orchestration and benchmark accounting; expectations never enter policy."""

from __future__ import annotations

from .evidence import GENESIS, digest, make_receipt
from .policy import decide
from .validation import parse_scenario


def replay(raw_scenario: dict) -> tuple[dict, list[dict]]:
    scenario = parse_scenario(raw_scenario)
    scenario_hash = digest(raw_scenario)
    policy_hash = digest(raw_scenario["policy"])
    receipts: list[dict] = []
    previous = GENESIS
    false_allows = 0
    false_denies = 0
    for index, action in enumerate(scenario.actions):
        result = decide(scenario, action)
        false_allows += result["decision"] == "allow" and not action.expected_allow
        false_denies += result["decision"] == "deny" and action.expected_allow
        receipt = make_receipt(
            scenario_id=scenario.scenario_id,
            scenario_hash=scenario_hash,
            policy_hash=policy_hash,
            action_hash=digest(raw_scenario["action_requests"][index]),
            sequence=index,
            previous=previous,
            result=result,
        )
        receipts.append(receipt)
        previous = receipt["sha256"]
    report = {
        "report_version": "bpa.report.v2",
        "scenario_id": scenario.scenario_id,
        "scenario_sha256": scenario_hash,
        "policy_sha256": policy_hash,
        "receipt_count": len(receipts),
        "last_receipt_sha256": previous,
        "false_allows": false_allows,
        "false_denies": false_denies,
        "pass": false_allows == 0 and false_denies == 0,
        "limitations": "Synthetic metadata replay only; no authenticated external issuer, hardware control, clinical use, or certification.",
    }
    return report, receipts
