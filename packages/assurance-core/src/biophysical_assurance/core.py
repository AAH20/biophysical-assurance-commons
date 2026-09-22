"""Compatibility facade: v1 fixtures remain runnable; v2 is the hardened protocol."""

from __future__ import annotations

import hmac
from pathlib import Path

from . import legacy
from .evidence import verify_receipts as verify_v2_receipts
from .parsing import read_json
from .runner import replay as replay_v2
from .validation import parse_scenario


def validate(scenario: dict) -> dict:
    if not isinstance(scenario, dict):
        raise TypeError("scenario must be an object")
    if scenario.get("schema_version") == "bpa.scenario.v1":
        return legacy.validate(scenario)
    parse_scenario(scenario)
    return scenario


def replay(scenario: dict) -> tuple[dict, list[dict]]:
    validate(scenario)
    return (
        legacy.replay(scenario)
        if scenario["schema_version"] == "bpa.scenario.v1"
        else replay_v2(scenario)
    )


def verify_receipts(receipts: list[dict], scenario: dict | None = None) -> bool:
    if scenario is None:
        return False  # A scenario-independent chain check cannot verify decision semantics.
    validate(scenario)
    if scenario["schema_version"] == "bpa.scenario.v1":
        expected = legacy.replay(scenario)[1]
        return len(receipts) == len(expected) and all(
            isinstance(actual, dict)
            and hmac.compare_digest(
                legacy.canonical(actual), legacy.canonical(reference)
            )
            for actual, reference in zip(receipts, expected)
        )
    return verify_v2_receipts(receipts, scenario)


def load_scenario(path: str | Path) -> dict:
    return validate(read_json(path))
