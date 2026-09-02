from pathlib import Path
from rag.ingestion.ingest import ingest

root = Path(__file__).resolve().parents[1]
print(f"Indexed {ingest(root / 'knowledge_base', root / 'data' / 'index')} chunks.")
