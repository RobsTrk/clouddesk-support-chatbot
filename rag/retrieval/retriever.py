import json
import re
from collections import Counter
from pathlib import Path
import faiss
from rag.embeddings.embedder import Embedder

# Common English function words carry no topical signal but appear in nearly
# every support article (and every customer message). Without filtering them,
# lexical overlap is dominated by words like "the"/"is"/"not" rather than the
# content words that actually distinguish one KB article from another, which
# lets unrelated or off-topic questions score a false-positive match. This
# list is intentionally small and dependency-free (no NLTK/spaCy download).
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "and", "or", "not", "no", "do",
    "does", "did", "my", "your", "our", "their", "his", "her", "its",
    "i", "you", "it", "this", "that", "these", "those", "with", "from",
    "as", "if", "then", "so", "but", "can", "have", "has", "had", "will",
    "would", "should", "could", "how", "what", "why", "when", "where",
    "who", "please", "just", "about", "into", "up", "down", "out", "me",
    "am", "im",
}

def _singularize(word: str) -> str:
    """Crude, dependency-free plural normalizer (not a full stemmer). Good
    enough for support vocabulary like invoice/invoices, plan/plans,
    integration/integrations - without pulling in NLTK/spaCy just for this.
    """
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    # True "-es" plurals only follow specific consonant sounds (box/boxes,
    # watch/watches, class/classes, buzz/buzzes). Any other "s" ending -
    # including words like "invoice" -> "invoices" that already end in a
    # silent e - is formed by adding a bare "s", so only that "s" is
    # stripped rather than "es" (which would wrongly turn "invoices" into
    # "invoic" instead of "invoice").
    if len(word) > 4 and word.endswith(("xes", "ches", "shes", "sses", "zzes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word

# Support conversations frequently write a compound word two different ways
# ("login" vs "log in"), which tokenize completely differently ("login" is
# one token; "log in" splits into "log" + a stopword "in") and would
# otherwise never overlap. This is intentionally tiny - just the handful of
# pairs that actually show up in this KB - not a general synonym engine.
SYNONYMS = {"login": "log", "logout": "log", "signin": "sign"}

def _canonical(word: str) -> str:
    return SYNONYMS.get(word, _singularize(word))

def _term_counts(text: str) -> Counter:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    # Filter stopwords BEFORE stemming, not after: stemming "does" produces
    # "doe" (an irregular verb, not a real plural), which would no longer
    # match an unstemmed "does" entry in STOPWORDS and leak through as a
    # bogus high-signal content word. Stopwords must be caught in their
    # original surface form first.
    content_words = [w for w in words if w not in STOPWORDS]
    normalized = [_canonical(w) for w in (content_words or words)]
    return Counter(normalized)

class Retriever:
    def __init__(self, index_dir):
        folder = Path(index_dir)
        self.index = faiss.read_index(str(folder / "support.faiss"))
        self.metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        self.embedder = Embedder()

    def search(self, query, k=4):
        # Dense matching works well when the sentence-transformer model is
        # available.  A lexical signal keeps retrieval dependable in the
        # documented offline fallback, where hash embeddings are approximate.
        query_counts = _term_counts(query)
        query_terms = set(query_counts)
        vector_scores, indexes = self.index.search(self.embedder.encode([query]), min(max(k * 3, k), len(self.metadata)))
        dense = {int(i): max(0.0, float(score)) for score, i in zip(vector_scores[0], indexes[0]) if i >= 0}
        ranked = []
        for index, item in enumerate(self.metadata):
            doc_counts = _term_counts(item["text"])
            doc_terms = set(doc_counts)
            # Primary lexical signal stays binary (a single on-topic mention
            # is real evidence, and this default was already well-calibrated
            # against RETRIEVAL_SCORE_THRESHOLD - discounting it caused
            # correctly-matched articles to fall below threshold). A small,
            # separate repetition bonus only nudges ties: an article that
            # repeats a query's content word several times (its actual
            # subject) outranks one that mentions it once in passing,
            # without depressing every other score.
            lexical = len(query_terms & doc_terms) / max(len(query_terms), 1)
            overlap_terms = query_terms & doc_terms
            repetition_bonus = 0.02 * sum(min(doc_counts.get(t, 0), 5) for t in overlap_terms) / max(len(query_terms), 1)
            score = 0.65 * lexical + 0.35 * dense.get(index, 0.0) + repetition_bonus
            ranked.append((score, index))
        return [{**self.metadata[index], "score": round(score, 4)} for score, index in sorted(ranked, reverse=True)[:k]]
