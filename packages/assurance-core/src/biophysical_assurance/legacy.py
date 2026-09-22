"""Deterministic policy replay and hash-chained evidence receipts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "bpa.scenario.v1"
RECEIPT_VERSION = "bpa.receipt.v1"
GENESIS = "0" * 64
REASONS = (
    "consent_inactive",
    "purpose_mismatch",
    "scope_mismatch",
    "identity_unverified",
    "identity_expired",
    "bci_intent_missing",
    "model_uncertain",
    "safety_not_clear",
    "human_approval_missing",
)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _require(obj: dict, key: str, typ: type, where: str) -> Any:
    if key not in obj or type(obj[key]) is not typ:
        raise ValueError(f"{where}.{key} must be {typ.__name__}")
    return obj[key]


def validate(scenario: Any) -> dict:
    if not isinstance(scenario, dict):
        raise TypeError("scenario must be an object")
    if scenario.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    _require(scenario, "scenario_id", str, "scenario")
    consent = _require(scenario, "consent", dict, "scenario")
    for key in ("subject_ref", "purpose", "scope"):
        _require(consent, key, str, "consent")
    start = _require(consent, "valid_from_ms", int, "consent")
    end = _require(consent, "valid_until_ms", int, "consent")
    if start >= end:
        raise ValueError("consent validity window must be increasing")
    revoked = consent.get("revoked_at_ms")
    if revoked is not None and type(revoked) is not int:
        raise ValueError("consent.revoked_at_ms must be integer or null")
    identity = _require(scenario, "identity_assertion", dict, "scenario")
    if (
        _require(identity, "subject_ref", str, "identity_assertion")
        != consent["subject_ref"]
    ):
        raise ValueError("identity and consent subjects differ")
    _require(identity, "verified", bool, "identity_assertion")
    _require(identity, "expires_at_ms", int, "identity_assertion")
    policy = _require(scenario, "policy", dict, "scenario")
    minimum = policy.get("min_model_confidence")
    if type(minimum) not in (int, float) or not 0 <= minimum <= 1:
        raise ValueError("policy.min_model_confidence must be in [0,1]")
    for key in ("require_bci_intent", "require_human_approval"):
        _require(policy, key, bool, "policy")
    actions = _require(scenario, "action_requests", list, "scenario")
    if not actions:
        raise ValueError("scenario.action_requests must not be empty")
    seen = set()
    for index, action in enumerate(actions):
        where = f"action_requests[{index}]"
        if not isinstance(action, dict):
            raise TypeError(f"{where} must be object")
        identifier = _require(action, "request_id", str, where)
        if not identifier or identifier in seen:
            raise ValueError(f"{where}.request_id must be unique and nonempty")
        seen.add(identifier)
        for key in ("at_ms",):
            _require(action, key, int, where)
        for key in ("purpose", "scope"):
            _require(action, key, str, where)
        for key in (
            "bci_intent_present",
            "safety_clear",
            "human_approved",
            "expected_allow",
        ):
            _require(action, key, bool, where)
        confidence = action.get("model_confidence")
        if type(confidence) not in (int, float) or not 0 <= confidence <= 1:
            raise ValueError(f"{where}.model_confidence must be in [0,1]")
    return scenario


def decide(scenario: dict, action: dict) -> dict:
    consent = scenario["consent"]
    identity = scenario["identity_assertion"]
    policy = scenario["policy"]
    t = action["at_ms"]
    reasons = []
    if not (consent["valid_from_ms"] <= t < consent["valid_until_ms"]) or (
        consent.get("revoked_at_ms") is not None and t >= consent["revoked_at_ms"]
    ):
        reasons.append("consent_inactive")
    if action["purpose"] != consent["purpose"]:
        reasons.append("purpose_mismatch")
    if action["scope"] != consent["scope"]:
        reasons.append("scope_mismatch")
    if not identity["verified"]:
        reasons.append("identity_unverified")
    if t >= identity["expires_at_ms"]:
        reasons.append("identity_expired")
    if policy["require_bci_intent"] and not action["bci_intent_present"]:
        reasons.append("bci_intent_missing")
    if action["model_confidence"] < policy["min_model_confidence"]:
        reasons.append("model_uncertain")
    if not action["safety_clear"]:
        reasons.append("safety_not_clear")
    if policy["require_human_approval"] and not action["human_approved"]:
        reasons.append("human_approval_missing")
    return {
        "request_id": action["request_id"],
        "at_ms": t,
        "decision": "allow" if not reasons else "deny",
        "reasons": reasons,
        "expected_allow": action["expected_allow"],
    }


def replay(scenario: dict) -> tuple[dict, list[dict]]:
    validate(scenario)
    scenario_hash = digest(scenario)
    previous = GENESIS
    receipts = []
    for index, action in enumerate(scenario["action_requests"]):
        result = decide(scenario, action)
        content = {
            "receipt_version": RECEIPT_VERSION,
            "scenario_id": scenario["scenario_id"],
            "scenario_sha256": scenario_hash,
            "sequence": index,
            "previous_sha256": previous,
            "result": result,
        }
        receipt = {**content, "sha256": digest(content)}
        receipts.append(receipt)
        previous = receipt["sha256"]
    false_allows = sum(
        r["result"]["decision"] == "allow" and not r["result"]["expected_allow"]
        for r in receipts
    )
    false_denies = sum(
        r["result"]["decision"] == "deny" and r["result"]["expected_allow"]
        for r in receipts
    )
    report = {
        "report_version": "bpa.report.v1",
        "scenario_id": scenario["scenario_id"],
        "scenario_sha256": scenario_hash,
        "receipt_count": len(receipts),
        "last_receipt_sha256": previous,
        "false_allows": false_allows,
        "false_denies": false_denies,
        "pass": false_allows == 0 and false_denies == 0,
        "limitations": "Synthetic replay only; no live devices, identity system, clinical use, or certification.",
    }
    return report, receipts


def verify_receipts(receipts: list[dict], scenario: dict | None = None) -> bool:
    previous = GENESIS
    scenario_hash = digest(validate(scenario)) if scenario is not None else None
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            return False
        content = {k: v for k, v in receipt.items() if k != "sha256"}
        if (
            receipt.get("receipt_version") != RECEIPT_VERSION
            or receipt.get("sequence") != index
        ):
            return False
        if receipt.get("previous_sha256") != previous or receipt.get(
            "sha256"
        ) != digest(content):
            return False
        if (
            scenario_hash is not None
            and receipt.get("scenario_sha256") != scenario_hash
        ):
            return False
        previous = receipt["sha256"]
    return bool(receipts)


def load_scenario(path: str | Path) -> dict:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
