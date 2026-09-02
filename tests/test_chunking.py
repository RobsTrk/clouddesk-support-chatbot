from rag.ingestion.ingest import chunk_text

def test_chunking_overlap():
    chunks = chunk_text(" ".join(map(str, range(12))), size=5, overlap=2)
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]
