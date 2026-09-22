"""Strict parsing: reject ambiguous fields, types, and unsafe fixture shapes."""

from __future__ import annotations

import math
from typing import Any

from .models import (
    ActionRequest,
    Consent,
    IdentityAssertion,
    Policy,
    Proposal,
    Scenario,
    TimedBoolean,
)

SCHEMA_VERSION = "bpa.scenario.v2"


def _object(
    value: Any, where: str, required: set[str], optional: set[str] = frozenset()
) -> dict:
    if not isinstance(value, dict):
        raise TypeError(f"{where} must be an object")
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing or extra:
        raise ValueError(
            f"{where} fields invalid: missing={sorted(missing)}, unexpected={sorted(extra)}"
        )
    return value


def _str(obj: dict, key: str, where: str) -> str:
    value = obj[key]
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(
            f"{where}.{key} must be a nonempty string of at most 256 characters"
        )
    return value


def _int(obj: dict, key: str, where: str, *, minimum: int = 0) -> int:
    value = obj[key]
    if type(value) is not int or value < minimum:
        raise ValueError(f"{where}.{key} must be an integer >= {minimum}")
    return value


def _bool(obj: dict, key: str, where: str) -> bool:
    value = obj[key]
    if type(value) is not bool:
        raise ValueError(f"{where}.{key} must be a Boolean")
    return value


def _confidence(obj: dict, key: str, where: str) -> float:
    value = obj[key]
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or not 0 <= value <= 1
    ):
        raise ValueError(f"{where}.{key} must be a finite number in [0, 1]")
    return float(value)


def _timed(value: Any, where: str) -> TimedBoolean | None:
    if value is None:
        return None
    obj = _object(value, where, {"value", "issued_at_ms", "expires_at_ms"})
    issued = _int(obj, "issued_at_ms", where)
    expires = _int(obj, "expires_at_ms", where)
    if issued >= expires:
        raise ValueError(f"{where} validity window must be increasing")
    return TimedBoolean(_bool(obj, "value", where), issued, expires)


def parse_scenario(value: Any) -> Scenario:
    root = _object(
        value,
        "scenario",
        {
            "schema_version",
            "scenario_id",
            "environment",
            "consent",
            "identity_assertion",
            "policy",
            "action_requests",
        },
        {"description"},
    )
    if root["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    scenario_id = _str(root, "scenario_id", "scenario")
    if "description" in root and not isinstance(root["description"], str):
        raise ValueError("scenario.description must be a string")
    environment = _str(root, "environment", "scenario")
    if environment != "synthetic":
        raise ValueError("v2 reference runtime accepts only environment=synthetic")

    consent = None
    if root["consent"] is not None:
        obj = _object(
            root["consent"],
            "consent",
            {
                "subject_ref",
                "purpose",
                "scope",
                "valid_from_ms",
                "valid_until_ms",
                "revoked_at_ms",
            },
        )
        start = _int(obj, "valid_from_ms", "consent")
        end = _int(obj, "valid_until_ms", "consent")
        if start >= end:
            raise ValueError("consent validity window must be increasing")
        revoked = obj["revoked_at_ms"]
        if revoked is not None:
            revoked = _int(obj, "revoked_at_ms", "consent")
        consent = Consent(
            _str(obj, "subject_ref", "consent"),
            _str(obj, "purpose", "consent"),
            _str(obj, "scope", "consent"),
            start,
            end,
            revoked,
        )

    identity = None
    if root["identity_assertion"] is not None:
        obj = _object(
            root["identity_assertion"],
            "identity_assertion",
            {
                "subject_ref",
                "issuer_ref",
                "purpose",
                "scope",
                "verified",
                "issued_at_ms",
                "expires_at_ms",
            },
        )
        issued = _int(obj, "issued_at_ms", "identity_assertion")
        expires = _int(obj, "expires_at_ms", "identity_assertion")
        if issued >= expires:
            raise ValueError("identity_assertion validity window must be increasing")
        identity = IdentityAssertion(
            _str(obj, "subject_ref", "identity_assertion"),
            _str(obj, "issuer_ref", "identity_assertion"),
            _str(obj, "purpose", "identity_assertion"),
            _str(obj, "scope", "identity_assertion"),
            _bool(obj, "verified", "identity_assertion"),
            issued,
            expires,
        )

    obj = _object(
        root["policy"],
        "policy",
        {
            "policy_ref",
            "min_model_confidence",
            "max_identity_age_ms",
            "max_proposal_age_ms",
            "require_bci_intent",
            "require_human_approval",
        },
    )
    policy = Policy(
        _str(obj, "policy_ref", "policy"),
        _confidence(obj, "min_model_confidence", "policy"),
        _int(obj, "max_identity_age_ms", "policy", minimum=1),
        _int(obj, "max_proposal_age_ms", "policy", minimum=1),
        _bool(obj, "require_bci_intent", "policy"),
        _bool(obj, "require_human_approval", "policy"),
    )

    values = root["action_requests"]
    if not isinstance(values, list) or not values:
        raise ValueError("action_requests must be a nonempty array")
    if len(values) > 10_000:
        raise ValueError("action_requests exceeds the 10,000-record safety limit")
    actions = []
    seen = set()
    previous_time = -1
    for index, item in enumerate(values):
        where = f"action_requests[{index}]"
        obj = _object(
            item,
            where,
            {
                "request_id",
                "at_ms",
                "subject_ref",
                "purpose",
                "scope",
                "proposal",
                "intent",
                "safety",
                "approval",
                "expected_allow",
            },
        )
        request_id = _str(obj, "request_id", where)
        if request_id in seen:
            raise ValueError(f"{where}.request_id duplicates an earlier request")
        seen.add(request_id)
        at_ms = _int(obj, "at_ms", where)
        if at_ms < previous_time:
            raise ValueError("action_requests must be ordered by at_ms")
        previous_time = at_ms
        proposal = None
        if obj["proposal"] is not None:
            p = _object(
                obj["proposal"],
                f"{where}.proposal",
                {"model_ref", "created_at_ms", "confidence"},
            )
            proposal = Proposal(
                _str(p, "model_ref", f"{where}.proposal"),
                _int(p, "created_at_ms", f"{where}.proposal"),
                _confidence(p, "confidence", f"{where}.proposal"),
            )
        actions.append(
            ActionRequest(
                request_id,
                at_ms,
                _str(obj, "subject_ref", where),
                _str(obj, "purpose", where),
                _str(obj, "scope", where),
                proposal,
                _timed(obj["intent"], f"{where}.intent"),
                _timed(obj["safety"], f"{where}.safety"),
                _timed(obj["approval"], f"{where}.approval"),
                _bool(obj, "expected_allow", where),
            )
        )
    return Scenario(scenario_id, environment, consent, identity, policy, tuple(actions))
