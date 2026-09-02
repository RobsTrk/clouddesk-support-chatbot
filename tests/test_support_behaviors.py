import pytest

from backend.services.intent_service import classify
from backend.services.llm_service import answer
from backend.services.router_service import route

@pytest.mark.parametrize(("message", "intent"), [
    ("I forgot my password", "password_reset"),
    ("I cannot log in to my workspace", "account_login"),
    ("Where is my invoice?", "billing"),
    ("My card payment was declined", "failed_payment"),
    ("I was charged twice and need a refund", "refund"),
    ("How do I upgrade my plan?", "upgrade"),
    ("Please cancel my subscription", "cancellation"),
    ("The dashboard is not working", "technical_issue"),
    ("Why does the API return 403?", "api"),
    ("How do I connect Slack?", "integration"),
    ("Why does your webhook return a 403 error?", "api"),  # regression: was mislabeled "integration" on a 1-1 tie
])
def test_support_intents(message, intent):
    assert classify(message).intent == intent

def test_suspicious_login_is_high_priority_escalation():
    result = classify("I think someone accessed my CloudDesk account. I received a login notification from a device I don't recognize.")
    escalated, needs_clarification, reason = route(.95, "grounded answer", .30, result.intent)
    assert result.intent == "account_security"
    assert escalated and not needs_clarification and "Security" in reason

def test_unknown_question_does_not_hallucinate_without_context():
    assert answer("What is the moon made of?", "") == "I don't have enough information to answer that."

def test_repeated_failed_troubleshooting_escalates():
    assert route(.9, "grounded answer", .30, "technical_issue", repeated_failure=True)[0]

def test_ambiguous_question_has_lower_intent_confidence():
    result = classify("help please")
    assert result.intent == "general_question"
    assert result.confidence < .60

def test_ambiguous_question_asks_for_clarification_even_if_retrieval_scores_high():
    # Regression test: a vague message can still get a spuriously high
    # retrieval score (e.g. matching one generic word in a KB article).
    # The system must not present that as a confident answer - it should
    # ask a clarifying question instead of guessing.
    result = classify("help please")
    escalated, needs_clarification, reason = route(
        max_similarity=0.90, answer="some grounded-looking answer", threshold=.30,
        intent=result.intent, intent_confidence=result.confidence, intent_confidence_medium=.60,
    )
    assert not escalated
    assert needs_clarification
