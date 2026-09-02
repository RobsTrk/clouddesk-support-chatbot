import json, re
from pathlib import Path
import numpy as np
import faiss
from rag.embeddings.embedder import Embedder

def chunk_text(text, size=500, overlap=50):
    words = re.sub(r"\s+", " ", text).strip().split()
    step = max(1, size - overlap)
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step) if words[i:i + size]]

def load_doc(path):
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return path.read_text(encoding="utf-8", errors="ignore")

def ingest(source_dir, output_dir):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = []
    for path in source_dir.glob("**/*"):
        if path.suffix.lower() not in {".txt", ".md", ".pdf"}:
            continue
        relative_path = path.relative_to(source_dir)
        article = load_doc(path)
        # Articles are intentionally modest in size; preserve headings and
        # metadata inside each chunk so the answerer can cite useful context.
        for number, text in enumerate(chunk_text(article, size=220, overlap=35)):
            metadata.append({"source": str(relative_path).replace("\\", "/"), "chunk": number, "text": text})
    if not metadata:
        raise ValueError("No TXT, MD, or PDF content found")
    vectors = Embedder().encode([item["text"] for item in metadata])
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(output_dir / "support.faiss"))
    (output_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return len(metadata)
