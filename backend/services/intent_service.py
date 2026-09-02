"""Transparent intent routing for the offline-capable prototype.

Rules are deliberately kept in one place so support teams can tune or replace
them with a trained classifier without changing the API contract.
"""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float

INTENT_RULES: dict[str, tuple[str, ...]] = {
    "account_security": ("someone accessed", "unknown device", "suspicious login", "unauthorized access", "account compromised", "hacked"),
    "password_reset": ("reset password", "forgot password", "password reset", "change my password"),
    "account_login": ("cannot log in", "can't log in", "unable to log in", "login failed", "sign in"),
    "failed_payment": ("payment failed", "card declined", "payment declined", "charge failed"),
    "refund": ("refund", "money back", "duplicate charge", "charged twice"),
    "cancellation": ("cancel subscription", "close my account", "cancel my plan"),
    "upgrade": ("upgrade", "higher plan", "change plan"),
    "subscription": ("subscription", "plan", "renewal"),
    "billing": ("invoice", "billing", "receipt", "charged"),
    "service_outage": ("outage", "service down", "everyone", "all users", "not loading"),
    "integration": ("integration", "slack", "google", "webhook", "connect"),
    "api": ("api", "endpoint", "api key", "403", "401", "rate limit"),
    "technical_issue": ("error", "bug", "broken", "not working", "dashboard"),
    "feature_request": ("feature request", "please add", "would be great if"),
}

# An HTTP status code is an unambiguous, highly diagnostic technical signal.
# Without this, a message like "why does your webhook return a 403 error?"
# ties 1-1 between "integration" (on "webhook") and "api" (on "403"), and
# plain dict-iteration order silently decides the winner - which happened to
# mislabel API errors as integration issues for analytics/routing purposes.
_HTTP_STATUS_RE = re.compile(r"\b[45]\d{2}\b")

def classify(message: str) -> IntentResult:
    text = message.lower()
    # Allow harmless filler words ("forgot *my* password") while still
    # requiring every meaningful term in a routing rule.
    matches = [(intent, sum(phrase in text or all(word in text for word in phrase.split()) for phrase in phrases)) for intent, phrases in INTENT_RULES.items()]
    best_count = max(count for _, count in matches)
    if not best_count:
        # A short or vague question should lead to a useful clarification
        # instead of being asserted as a known support category. A longer,
        # well-formed question that simply doesn't match a specific rule
        # (e.g. "What features does CloudDesk offer?") is a different
        # situation - it deserves a normal, retrieval-backed answer attempt,
        # not a clarifying question, so its confidence clears
        # INTENT_CONFIDENCE_MEDIUM while a genuinely vague one does not.
        return IntentResult("general_question", 0.45 if len(text.split()) < 5 else 0.65)
    tied = [intent for intent, count in matches if count == best_count]
    if len(tied) > 1 and "api" in tied and _HTTP_STATUS_RE.search(text):
        intent = "api"
    else:
        intent = tied[0]
    return IntentResult(intent, min(0.95, 0.75 + best_count * 0.1))
