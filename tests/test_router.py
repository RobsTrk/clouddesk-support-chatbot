from backend.services.router_service import route

def test_low_confidence_escalates():
    assert route(.1, "fine", .45)[0]

def test_high_confidence_answers():
    escalated, needs_clarification, _ = route(.9, "fine", .45)
    assert not escalated and not needs_clarification

def test_insufficient_information_escalates():
    assert route(.9, "I don't have enough information to answer that.", .45)[0]

def test_low_intent_confidence_asks_for_clarification_not_escalation():
    escalated, needs_clarification, reason = route(.9, "fine", .45, intent_confidence=.40, intent_confidence_medium=.60)
    assert not escalated
    assert needs_clarification
    assert "intent confidence" in reason.lower()

def test_high_intent_confidence_does_not_trigger_clarification():
    escalated, needs_clarification, _ = route(.9, "fine", .45, intent_confidence=.90, intent_confidence_medium=.60)
    assert not escalated and not needs_clarification

def test_high_risk_intent_skips_clarification_check_entirely():
    # Even with very low intent confidence, a security-flagged intent must
    # still escalate rather than merely asking a clarifying question.
    escalated, needs_clarification, reason = route(.9, "fine", .45, intent="account_security", intent_confidence=.10)
    assert escalated and not needs_clarification

def test_refund_always_escalates_regardless_of_retrieval_confidence():
    # Policy, not confidence: Nova is never allowed to approve/issue a
    # refund itself (see billing/payments_and_refunds.md), so this must
    # escalate even when retrieval and the drafted answer both look fine.
    escalated, needs_clarification, reason = route(.95, "grounded answer", .30, intent="refund")
    assert escalated and not needs_clarification
    assert "human approval" in reason.lower()
