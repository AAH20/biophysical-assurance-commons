"""Canonical receipts and verification bound to a replayable scenario."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from .policy import EVALUATOR_VERSION, decide
from .validation import parse_scenario

RECEIPT_VERSION = "bpa.receipt.v2"
GENESIS = "0" * 64


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def make_receipt(
    *,
    scenario_id: str,
    scenario_hash: str,
    policy_hash: str,
    action_hash: str,
    sequence: int,
    previous: str,
    result: dict,
) -> dict:
    body = {
        "receipt_version": RECEIPT_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "scenario_id": scenario_id,
        "scenario_sha256": scenario_hash,
        "policy_sha256": policy_hash,
        "action_sha256": action_hash,
        "sequence": sequence,
        "previous_sha256": previous,
        "result": result,
    }
    return {**body, "sha256": digest(body)}


def verify_receipts(receipts: list[dict], raw_scenario: dict) -> bool:
    """Check hashes AND recompute every decision from the supplied scenario."""
    try:
        scenario = parse_scenario(raw_scenario)
        if len(receipts) != len(scenario.actions):
            return False
        scenario_hash = digest(raw_scenario)
        policy_hash = digest(raw_scenario["policy"])
        previous = GENESIS
        for index, (receipt, action) in enumerate(zip(receipts, scenario.actions)):
            expected = make_receipt(
                scenario_id=scenario.scenario_id,
                scenario_hash=scenario_hash,
                policy_hash=policy_hash,
                action_hash=digest(raw_scenario["action_requests"][index]),
                sequence=index,
                previous=previous,
                result=decide(scenario, action),
            )
            if not isinstance(receipt, dict) or not hmac.compare_digest(
                canonical(receipt), canonical(expected)
            ):
                return False
            previous = receipt["sha256"]
        return True
    except (TypeError, ValueError, KeyError, OverflowError):
        return False


def make_auth_tag(
    *, scenario_sha256: str, last_receipt_sha256: str, key: bytes, key_id: str
) -> dict:
    """Optional symmetric authentication for a separately managed key."""
    if len(key) < 32:
        raise ValueError("authentication key must be at least 32 bytes")
    if not key_id or len(key_id) > 256:
        raise ValueError("key_id must be nonempty and at most 256 characters")
    body = {
        "version": "bpa.auth.v1",
        "algorithm": "HMAC-SHA256",
        "key_id": key_id,
        "scenario_sha256": scenario_sha256,
        "last_receipt_sha256": last_receipt_sha256,
    }
    return {**body, "tag": hmac.new(key, canonical(body), hashlib.sha256).hexdigest()}


def verify_auth_tag(
    tag: dict, *, scenario_sha256: str, last_receipt_sha256: str, key: bytes
) -> bool:
    try:
        expected = make_auth_tag(
            scenario_sha256=scenario_sha256,
            last_receipt_sha256=last_receipt_sha256,
            key=key,
            key_id=tag["key_id"],
        )
        return hmac.compare_digest(canonical(tag), canonical(expected))
    except (TypeError, ValueError, KeyError):
        return False
