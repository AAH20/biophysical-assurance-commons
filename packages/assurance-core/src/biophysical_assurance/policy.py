"""Pure policy decision function. It cannot command a device or mutate evidence."""

from __future__ import annotations

from .models import ActionRequest, Scenario, TimedBoolean

EVALUATOR_VERSION = "bpa.evaluator.v2.0"


def _current(value: TimedBoolean | None, at_ms: int) -> bool:
    return value is not None and value.issued_at_ms <= at_ms < value.expires_at_ms


def decide(scenario: Scenario, action: ActionRequest) -> dict:
    """Return an ordered reason list; any failed gate denies the action."""
    t = action.at_ms
    reasons: list[str] = []
    consent = scenario.consent
    if consent is None:
        reasons.append("consent_missing")
    else:
        if action.subject_ref != consent.subject_ref:
            reasons.append("consent_subject_mismatch")
        if action.purpose != consent.purpose:
            reasons.append("consent_purpose_mismatch")
        if action.scope != consent.scope:
            reasons.append("consent_scope_mismatch")
        if not consent.valid_from_ms <= t < consent.valid_until_ms or (
            consent.revoked_at_ms is not None and t >= consent.revoked_at_ms
        ):
            reasons.append("consent_inactive")

    identity = scenario.identity
    if identity is None:
        reasons.append("identity_missing")
    else:
        if action.subject_ref != identity.subject_ref:
            reasons.append("identity_subject_mismatch")
        if action.purpose != identity.purpose:
            reasons.append("identity_purpose_mismatch")
        if action.scope != identity.scope:
            reasons.append("identity_scope_mismatch")
        if not identity.verified:
            reasons.append("identity_unverified")
        if (
            not identity.issued_at_ms <= t < identity.expires_at_ms
            or t - identity.issued_at_ms > scenario.policy.max_identity_age_ms
        ):
            reasons.append("identity_stale")

    proposal = action.proposal
    if proposal is None:
        reasons.append("proposal_missing")
    else:
        if not 0 <= t - proposal.created_at_ms <= scenario.policy.max_proposal_age_ms:
            reasons.append("proposal_stale")
        if proposal.confidence < scenario.policy.min_model_confidence:
            reasons.append("model_uncertain")

    if scenario.policy.require_bci_intent:
        if action.intent is None:
            reasons.append("intent_missing")
        elif not action.intent.value or not _current(action.intent, t):
            reasons.append("intent_inactive")

    if action.safety is None:
        reasons.append("safety_missing")
    elif not action.safety.value or not _current(action.safety, t):
        reasons.append("safety_not_clear")

    if scenario.policy.require_human_approval:
        if action.approval is None:
            reasons.append("approval_missing")
        elif not action.approval.value or not _current(action.approval, t):
            reasons.append("approval_inactive")

    return {
        "request_id": action.request_id,
        "at_ms": t,
        "decision": "deny" if reasons else "allow",
        "reasons": reasons,
    }
