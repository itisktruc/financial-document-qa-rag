from app.retrieval.hybrid_search import _load_bm25_corpus
ids, texts, lookup = _load_bm25_corpus()
print("bm25 corpus size:", len(texts))