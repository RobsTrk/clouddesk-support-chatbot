INSUFFICIENT = ("don't have enough information", "do not have enough information", "insufficient information")
SECURITY_INTENTS = {"account_security", "security_issue"}
HIGH_RISK_INTENTS = SECURITY_INTENTS | {"service_outage"}
# CloudDesk policy (see billing/payments_and_refunds.md): Nova is never
# authorised to approve or issue a refund itself, regardless of how
# confident the retrieval match is. This must be a deliberate policy check,
# not an accidental side-effect of a borderline retrieval score - a refund
# request that happens to score just above RETRIEVAL_SCORE_THRESHOLD must
# still go to a human.
POLICY_ESCALATION_INTENTS = {"refund"}

def priority_for(intent: str) -> str:
    """Triage priority for the human-review queue. Kept separate from the
    escalate/clarify decision itself since it's presentational metadata for
    agents, not something that changes Nova's behaviour."""
    if intent in HIGH_RISK_INTENTS:
        return "high"
    if intent in POLICY_ESCALATION_INTENTS or intent in {"failed_payment", "billing"}:
        return "medium"
    return "normal"

def route(max_similarity: float, answer: str, threshold: float, intent: str = "general_question",
          repeated_failure: bool = False, intent_confidence: float = 1.0,
          intent_confidence_medium: float = 0.60) -> tuple[bool, bool, str | None]:
    """Return (escalated, needs_clarification, reason).

    escalated: a human-review record should be created (see Escalation model).
    needs_clarification: the message is too ambiguous to answer confidently,
        but does NOT need a human yet - Nova should ask a follow-up question
        instead of presenting a possibly-wrong retrieved answer as fact.
    Only one of escalated / needs_clarification is ever True at once.
    """
    if intent in HIGH_RISK_INTENTS:
        return True, False, "Security-sensitive report" if intent in SECURITY_INTENTS else "Possible service-wide outage"
    if intent in POLICY_ESCALATION_INTENTS:
        return True, False, "Refunds require human approval before being issued"
    if repeated_failure:
        return True, False, "Customer reported repeated unsuccessful troubleshooting"
    if max_similarity < threshold:
        return True, False, f"Low retrieval similarity ({max_similarity:.2f})"
    if any(phrase in answer.lower() for phrase in INSUFFICIENT):
        return True, False, "Model reported insufficient context"
    # Retrieval looked confident enough to answer, but the intent classifier
    # itself was unsure what the customer is actually asking about (e.g. a
    # short, vague message). Trusting a single retrieved article in that case
    # risks answering a different question than the one being asked, so ask
    # for clarification instead of presenting it as a confident match.
    if intent_confidence < intent_confidence_medium:
        return False, True, f"Low intent confidence ({intent_confidence:.2f}); message is ambiguous"
    return False, False, None
