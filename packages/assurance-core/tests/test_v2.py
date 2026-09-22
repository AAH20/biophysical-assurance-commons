import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = REPO_ROOT / "packages/assurance-contracts/scenarios"
sys.path.insert(0, str(CORE_ROOT / "src"))

from biophysical_assurance.core import load_scenario, replay, verify_receipts
from biophysical_assurance.evidence import make_auth_tag, verify_auth_tag
from biophysical_assurance.parsing import loads_strict
from biophysical_assurance.result_contract import from_replay
from biophysical_assurance.storage import publish_bundle, read_receipts
from biophysical_assurance.validation import parse_scenario


class V2Tests(unittest.TestCase):
    def setUp(self):
        self.scenario = load_scenario(SCENARIOS / "expired-consent-handover.v2.json")

    def test_expiry_and_recomputed_receipts(self):
        report, receipts = replay(self.scenario)
        self.assertTrue(report["pass"])
        self.assertEqual([r["result"]["decision"] for r in receipts], ["allow", "deny"])
        self.assertEqual(receipts[1]["result"]["reasons"], ["consent_inactive"])
        self.assertNotIn("expected_allow", receipts[0]["result"])
        self.assertTrue(verify_receipts(receipts, self.scenario))
        envelope = from_replay(self.scenario, report, receipts)
        self.assertEqual(envelope["qualification"]["failed_gates"], [])
        self.assertEqual(
            envelope["evidence"]["receipt_root_sha256"], receipts[-1]["sha256"]
        )

    def test_stale_all_evidence_denied(self):
        scenario = load_scenario(SCENARIOS / "stale-evidence-handover.v2.json")
        report, receipts = replay(scenario)
        self.assertTrue(report["pass"])
        self.assertEqual(
            receipts[0]["result"]["reasons"],
            [
                "identity_stale",
                "proposal_stale",
                "intent_inactive",
                "safety_not_clear",
                "approval_inactive",
            ],
        )

    def test_absent_evidence_fails_closed(self):
        scenario = copy.deepcopy(self.scenario)
        scenario["consent"] = None
        scenario["identity_assertion"] = None
        action = scenario["action_requests"][0]
        action["proposal"] = None
        action["intent"] = None
        action["safety"] = None
        action["approval"] = None
        report, receipts = replay(scenario)
        self.assertEqual(report["false_denies"], 1)
        self.assertEqual(
            receipts[0]["result"]["reasons"],
            [
                "consent_missing",
                "identity_missing",
                "proposal_missing",
                "intent_missing",
                "safety_missing",
                "approval_missing",
            ],
        )

    def test_subject_purpose_scope_and_future_assertions(self):
        scenario = copy.deepcopy(self.scenario)
        action = scenario["action_requests"][0]
        action["subject_ref"] = "other"
        action["purpose"] = "unrelated"
        action["scope"] = "different"
        action["safety"]["issued_at_ms"] = 1050
        _, receipts = replay(scenario)
        self.assertEqual(
            receipts[0]["result"]["reasons"],
            [
                "consent_subject_mismatch",
                "consent_purpose_mismatch",
                "consent_scope_mismatch",
                "identity_subject_mismatch",
                "identity_purpose_mismatch",
                "identity_scope_mismatch",
                "safety_not_clear",
            ],
        )

    def test_unknown_fields_nan_duplicate_and_order_rejected(self):
        scenario = copy.deepcopy(self.scenario)
        scenario["action_requests"][0]["proposal"]["confidence"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            parse_scenario(scenario)
        scenario = copy.deepcopy(self.scenario)
        scenario["action_requests"][0]["secret"] = "unexpected"
        with self.assertRaisesRegex(ValueError, "unexpected"):
            parse_scenario(scenario)
        scenario = copy.deepcopy(self.scenario)
        scenario["action_requests"][1]["request_id"] = "handover-1"
        with self.assertRaisesRegex(ValueError, "duplicates"):
            parse_scenario(scenario)
        scenario = copy.deepcopy(self.scenario)
        scenario["action_requests"][1]["at_ms"] = 999
        with self.assertRaisesRegex(ValueError, "ordered"):
            parse_scenario(scenario)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            loads_strict('{"scenario_id":"first","scenario_id":"second"}')
        with self.assertRaisesRegex(ValueError, "non-finite"):
            loads_strict('{"value":NaN}')

    def test_forged_self_consistent_receipt_rejected(self):
        _, receipts = replay(self.scenario)
        forged = copy.deepcopy(receipts)
        forged[0]["result"]["decision"] = "deny"
        from biophysical_assurance.evidence import digest

        forged[0]["sha256"] = digest(
            {k: v for k, v in forged[0].items() if k != "sha256"}
        )
        forged[1]["previous_sha256"] = forged[0]["sha256"]
        forged[1]["sha256"] = digest(
            {k: v for k, v in forged[1].items() if k != "sha256"}
        )
        self.assertFalse(verify_receipts(forged, self.scenario))

    def test_authenticated_bundle_and_atomic_no_overwrite(self):
        report, receipts = replay(self.scenario)
        key = b"test-only-key-material-32-bytes-long!!"
        tag = make_auth_tag(
            scenario_sha256=report["scenario_sha256"],
            last_receipt_sha256=report["last_receipt_sha256"],
            key=key,
            key_id="test-key",
        )
        self.assertTrue(
            verify_auth_tag(
                tag,
                scenario_sha256=report["scenario_sha256"],
                last_receipt_sha256=report["last_receipt_sha256"],
                key=key,
            )
        )
        self.assertFalse(
            verify_auth_tag(
                tag,
                scenario_sha256=report["scenario_sha256"],
                last_receipt_sha256=report["last_receipt_sha256"],
                key=b"wrong-test-key-material-32-bytes!!",
            )
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bundle"
            publish_bundle(path, report, receipts, tag)
            self.assertEqual(read_receipts(path), receipts)
            self.assertEqual(json.loads((path / "report.json").read_text()), report)
            with self.assertRaises(FileExistsError):
                publish_bundle(path, report, receipts, tag)


if __name__ == "__main__":
    unittest.main()
