import json
import logging
import time
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from backend.core.config import settings
from backend.models.db_models import Escalation, Feedback, Interaction, Query, Response, SessionLocal
from backend.schemas.chat_schema import ChatRequest, ChatResponse, FeedbackRequest
from backend.services.intent_service import classify
from backend.services.llm_service import answer
from backend.services.retrieval_service import retrieve
from backend.services.router_service import priority_for, route

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    started = time.perf_counter()
    message = payload.message.strip()
    if not message or len(message) > settings.max_message_length:
        raise HTTPException(400, "Message is empty or too long")
    try:
        intent_result = classify(message)
        matches = retrieve(message)
    except Exception as exc:
        logger.exception("Knowledge retrieval failed")
        raise HTTPException(500, f"Knowledge index unavailable: {exc}")
    confidence = max((item["score"] for item in matches), default=0.0)
    context = "\n\n---\n\n".join(item["text"] for item in matches if item["score"] >= settings.retrieval_score_threshold)
    conversation_id = payload.conversation_id or str(uuid4())
    repeated_failure = any(phrase in message.lower() for phrase in ("still not working", "didn't work", "did not work", "tried everything"))
    try:
        draft = answer(message, context)
    except Exception as exc:
        logger.exception("Language model request failed")
        raise HTTPException(502, "Language model is temporarily unavailable")
    escalated, needs_clarification, reason = route(
        confidence, draft, settings.retrieval_score_threshold, intent_result.intent, repeated_failure,
        intent_result.confidence, settings.intent_confidence_medium,
    )
    if escalated:
        if intent_result.intent == "account_security":
            final = ("This needs human support review. For your security, please change your password and avoid "
                      "sharing verification codes while an agent reviews this report.")
        elif intent_result.intent == "refund":
            final = ("I've logged this for a specialist to review - Nova isn't able to approve or issue refunds "
                      "directly. A member of the CloudDesk team will follow up on the charge you flagged.")
        elif intent_result.intent == "service_outage":
            final = ("I've flagged this as a possible service-wide issue for the team to verify. I can't confirm "
                      "an outage myself, so an agent will follow up with a status update.")
        else:
            final = "This needs human support review. I don't have enough verified CloudDesk information to resolve this safely."
    elif needs_clarification:
        final = (
            "I want to make sure I point you to the right guidance. Could you tell me a bit more about your "
            "CloudDesk issue - for example, which area it involves (login, billing, subscriptions, integrations, "
            "API, etc.) and what you've already tried?"
        )
    else:
        final = draft
    # Always log what was actually retrieved (useful for analytics / spotting
    # retrieval failures even on escalated or clarification turns), but the
    # frontend only displays "knowledge used" when it was actually the basis
    # of the answer - see used_sources on the response.
    sources = [f'{item["source"]}#chunk{item["chunk"]}' for item in matches]
    used_sources = [] if (escalated or needs_clarification) else sources
    query_id: int | None = None
    try:
        with SessionLocal() as db:
            query = Query(user_query=message)
            db.add(query); db.flush()
            db.add(Response(query_id=query.id, answer=final, confidence=confidence, sources=json.dumps(sources), escalated=escalated))
            if escalated:
                summary = (f"Intent: {intent_result.intent} (confidence {intent_result.confidence:.2f}). "
                           f"Reason: {reason}. Customer message: {message[:280]}")
                db.add(Escalation(query_id=query.id, conversation_id=conversation_id, intent=intent_result.intent,
                                   priority=priority_for(intent_result.intent),
                                   reason=reason or "Low confidence", summary=summary))
            db.add(Interaction(query_id=query.id, conversation_id=conversation_id, intent=intent_result.intent,
                               intent_confidence=intent_result.confidence,
                               retrieval_failure=confidence < settings.retrieval_score_threshold,
                               response_time_ms=(time.perf_counter() - started) * 1000,
                               resolved_by_ai=not escalated and not needs_clarification))
            db.commit()
            query_id = query.id
    except Exception:
        logger.exception("Could not persist chat interaction")
        raise HTTPException(500, "Support service could not save this interaction")
    return ChatResponse(query_id=query_id, answer=final, confidence=confidence, escalated=escalated,
                        needs_clarification=needs_clarification, sources=used_sources,
                        conversation_id=conversation_id, intent=intent_result.intent,
                        intent_confidence=intent_result.confidence, escalation_reason=reason)

@router.post("/feedback")
def feedback(payload: FeedbackRequest):
    with SessionLocal() as db:
        if not db.get(Query, payload.query_id):
            raise HTTPException(404, "Chat interaction not found")
        existing = db.query(Feedback).filter_by(query_id=payload.query_id).first()
        if existing:
            existing.helpful, existing.comment = payload.helpful, payload.comment
        else:
            db.add(Feedback(query_id=payload.query_id, helpful=payload.helpful, comment=payload.comment))
        db.commit()
    return {"status": "recorded"}

@router.get("/metrics")
def metrics():
    with SessionLocal() as db:
        total, escalated = db.query(Query).count(), db.query(Escalation).count()
        resolved = db.query(Interaction).filter_by(resolved_by_ai=True).count()
        retrieval_failures = db.query(Interaction).filter_by(retrieval_failure=True).count()
        avg_time = db.query(func.avg(Interaction.response_time_ms)).scalar() or 0
        feedback_rows = db.query(Feedback).all()
        intent_rows = db.query(Interaction.intent, func.count(Interaction.id)).group_by(Interaction.intent).all()
    return {"total_conversations": total, "resolved_conversations": resolved, "escalated_conversations": escalated,
            "ai_resolution_rate": resolved / total if total else 0, "escalation_rate": escalated / total if total else 0,
            "average_response_time_ms": round(float(avg_time), 2),
            "customer_feedback_score": (sum(row.helpful for row in feedback_rows) / len(feedback_rows)) if feedback_rows else None,
            "knowledge_base_retrieval_failures": retrieval_failures, "intent_distribution": dict(intent_rows)}
