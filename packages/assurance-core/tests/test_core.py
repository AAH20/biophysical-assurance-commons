import copy
import json
import sys
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = REPO_ROOT / "packages/assurance-contracts/scenarios"
sys.path.insert(0, str(CORE_ROOT / "src"))

from biophysical_assurance.core import load_scenario, replay, validate, verify_receipts


class ReplayTests(unittest.TestCase):
    def test_expired_consent_denies_high_confidence_action(self):
        scenario = load_scenario(SCENARIOS / "expired-consent-handover.json")
        report, receipts = replay(scenario)
        self.assertTrue(report["pass"])
        self.assertEqual([r["result"]["decision"] for r in receipts], ["allow", "deny"])
        self.assertEqual(receipts[1]["result"]["reasons"], ["consent_inactive"])
        self.assertTrue(verify_receipts(receipts, scenario))

    def test_revocation_takes_precedence(self):
        scenario = load_scenario(SCENARIOS / "revoked-consent-handover.json")
        report, receipts = replay(scenario)
        self.assertTrue(report["pass"])
        self.assertEqual(receipts[1]["result"]["reasons"], ["consent_inactive"])

    def test_missing_safety_and_human_approval_fail_closed(self):
        scenario = load_scenario(SCENARIOS / "expired-consent-handover.json")
        scenario["action_requests"][0]["safety_clear"] = False
        scenario["action_requests"][0]["human_approved"] = False
        report, receipts = replay(scenario)
        self.assertFalse(report["pass"])
        self.assertEqual(report["false_denies"], 1)
        self.assertEqual(
            receipts[0]["result"]["reasons"],
            ["safety_not_clear", "human_approval_missing"],
        )

    def test_receipt_tampering_is_detected(self):
        scenario = load_scenario(SCENARIOS / "expired-consent-handover.json")
        _, receipts = replay(scenario)
        tampered = copy.deepcopy(receipts)
        tampered[0]["result"]["decision"] = "deny"
        self.assertFalse(verify_receipts(tampered, scenario))
        self.assertFalse(
            verify_receipts(receipts, {**scenario, "scenario_id": "different"})
        )

    def test_replay_is_deterministic(self):
        scenario = load_scenario(SCENARIOS / "expired-consent-handover.json")
        self.assertEqual(replay(scenario), replay(json.loads(json.dumps(scenario))))

    def test_subject_mismatch_and_duplicate_request_rejected(self):
        scenario = load_scenario(SCENARIOS / "expired-consent-handover.json")
        scenario["identity_assertion"]["subject_ref"] = "other"
        with self.assertRaisesRegex(ValueError, "subjects differ"):
            validate(scenario)
        scenario["identity_assertion"]["subject_ref"] = scenario["consent"][
            "subject_ref"
        ]
        scenario["action_requests"][1]["request_id"] = scenario["action_requests"][0][
            "request_id"
        ]
        with self.assertRaisesRegex(ValueError, "unique"):
            validate(scenario)


if __name__ == "__main__":
    unittest.main()
