"""Immutable, validated inputs for the v2 synthetic assurance protocol."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Consent:
    subject_ref: str
    purpose: str
    scope: str
    valid_from_ms: int
    valid_until_ms: int
    revoked_at_ms: int | None


@dataclass(frozen=True, slots=True)
class IdentityAssertion:
    subject_ref: str
    issuer_ref: str
    purpose: str
    scope: str
    verified: bool
    issued_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class Policy:
    policy_ref: str
    min_model_confidence: float
    max_identity_age_ms: int
    max_proposal_age_ms: int
    require_bci_intent: bool
    require_human_approval: bool


@dataclass(frozen=True, slots=True)
class Proposal:
    model_ref: str
    created_at_ms: int
    confidence: float


@dataclass(frozen=True, slots=True)
class TimedBoolean:
    value: bool
    issued_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class ActionRequest:
    request_id: str
    at_ms: int
    subject_ref: str
    purpose: str
    scope: str
    proposal: Proposal | None
    intent: TimedBoolean | None
    safety: TimedBoolean | None
    approval: TimedBoolean | None
    expected_allow: bool


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    environment: str
    consent: Consent | None
    identity: IdentityAssertion | None
    policy: Policy
    actions: tuple[ActionRequest, ...]
