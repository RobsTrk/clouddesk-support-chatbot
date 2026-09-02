from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

class Settings:
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'copilot.db'}")
    index_dir = Path(os.getenv("INDEX_DIR", str(ROOT / "data" / "index")))
    # RETRIEVAL_SCORE_THRESHOLD is the preferred name; the older setting is
    # retained so existing .env files keep working.
    retrieval_score_threshold = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", os.getenv("SIMILARITY_THRESHOLD", "0.30")))
    intent_confidence_high = float(os.getenv("INTENT_CONFIDENCE_HIGH", "0.85"))
    intent_confidence_medium = float(os.getenv("INTENT_CONFIDENCE_MEDIUM", "0.60"))
    top_k = int(os.getenv("TOP_K", "4"))
    max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm_timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

settings = Settings()
