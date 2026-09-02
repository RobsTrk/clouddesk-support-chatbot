# Autonomous Customer Support Copilot

Nova is the CloudDesk Customer Support Copilot. This local FastAPI + Streamlit prototype uses RAG over a fictional CloudDesk knowledge base, confidence-aware intent routing, SQLite interaction logs, feedback, and persistent escalation records.

## Quick start

1. Use Python 3.11–3.13, create a virtual environment, and run `python -m pip install -r requirements.txt`. Python 3.14 is not yet a safe choice for all ML dependencies in this project.
2. Copy `.env.example` to `.env`. An `OPENAI_API_KEY` is optional; without one, a local extractive fallback supports demos.
3. Build the knowledge index with `python scripts/run_ingestion.py`.
4. Start the API with `uvicorn backend.main:app --reload`.
5. In another terminal run `streamlit run frontend/app.py`.

Use `/docs` for API documentation, `/health` for status, and `/metrics` for real interaction counts. Add TXT, Markdown, or PDF material to `knowledge_base/` and rerun ingestion whenever it changes. `OPENAI_API_KEY` is optional: without it, Nova returns only retrieved guidance and will not invent an answer.

## Safety behavior

Suspected account compromise and possible service outages are always escalated. Billing disputes, refund requests requiring approval, repeated failed troubleshooting, and low-quality retrieval are also escalated. An escalation is only reported after its SQLite record is saved.

## Feedback and metrics

The interface sends Helpful / Not helpful feedback to `/feedback`. `/metrics` reports total and resolved conversations, escalations, response-time average, retrieval failures, feedback score, and intent distribution from stored interactions. Feedback is for support-quality review; it does not trigger automatic model retraining.

## Safety and escalation

The generation prompt permits answers only from retrieved context and treats instructions embedded in documents as untrusted. Low retrieval similarity or an insufficient-information response creates a pending escalation. The query, response, confidence, and sources are persisted in SQLite.
