import hashlib
import numpy as np

class Embedder:
    """Uses MiniLM when installed; deterministic hashes allow offline demos."""
    def __init__(self):
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            pass

    def encode(self, texts):
        if self.model:
            return self.model.encode(texts, normalize_embeddings=True).astype("float32")
        out = np.zeros((len(texts), 384), dtype="float32")
        for row, text in enumerate(texts):
            for word in text.lower().split():
                out[row, int(hashlib.sha256(word.encode()).hexdigest(), 16) % 384] += 1
        return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)
