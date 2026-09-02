# CloudDesk Support Copilot

Nova is a local customer-support assistant for the fictional CloudDesk SaaS product. It combines a FastAPI service, Streamlit chat interface, retrieval-augmented answers, intent routing, feedback collection, and escalation tracking.

## What it does

- Answers questions using the curated CloudDesk knowledge base.
- Detects common support intents such as password resets, billing, integrations, API issues, and dashboard problems.
- Escalates safety-sensitive or low-confidence requests instead of inventing an answer.
- Records conversations, feedback, and escalation records in a local SQLite database.
- Shows support metrics including resolution, escalation, feedback, and intent distribution.

## Requirements

- Python 3.11, 3.12, or 3.13
- `pip`

An OpenAI API key is optional. Without one, Nova uses its local retrieval-based fallback for demonstrations.

## Run locally

1. Clone the repository and enter the project directory.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell, use `Copy-Item .env.example .env` instead.

5. Build or refresh the knowledge index:

   ```bash
   python scripts/run_ingestion.py
   ```

6. Start the API in one terminal:

   ```bash
   uvicorn backend.main:app --reload
   ```

7. Start the chat interface in a second terminal:

   ```bash
   streamlit run frontend/app.py
   ```

Open the interface at `http://localhost:8501`. API documentation is available at `http://localhost:8000/docs`.

## Configuration

Copy `.env.example` to `.env` to customize the application. The most useful settings are:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional key for generated answers. |
| `OPENAI_MODEL` | Model to use when an API key is present. |
| `DATABASE_URL` | SQLite database location. |
| `RETRIEVAL_SCORE_THRESHOLD` | Minimum retrieval confidence before an escalation is created. |
| `TOP_K` | Number of knowledge-base passages retrieved per request. |

## API endpoints

| Endpoint | Purpose |
| --- | --- |
| `POST /chat` | Submit a customer-support question. |
| `POST /feedback` | Mark an answer helpful or not helpful. |
| `GET /health` | Check the API status. |
| `GET /metrics` | View support-quality and routing metrics. |
| `GET /docs` | Open interactive API documentation. |

## Knowledge base

The `knowledge_base/` directory contains the support material Nova may use. Add TXT, Markdown, or PDF documents there and run the ingestion command again to update retrieval.

## Safety behavior

Nova always escalates suspected account compromise and potential service outages. It also escalates billing disputes requiring approval, repeated failed troubleshooting, and questions where the retrieved knowledge is insufficient. It reports an escalation only after saving the local record.

## Development

Run the test suite with:

```bash
pytest
```

## Project structure

```text
backend/         FastAPI routes, services, schemas, and database models
frontend/        Streamlit chat interface
knowledge_base/  CloudDesk support content
rag/             Ingestion, embeddings, and retrieval logic
scripts/         Utility scripts, including knowledge ingestion
tests/           Automated behavior tests
```
