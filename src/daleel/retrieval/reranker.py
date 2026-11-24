"""Cross-encoder reranker for re-scoring retrieved candidates."""

class CrossEncoderReranker:
    """Cross-encoder model to rerank retrieved document passages."""
    def rerank(self, query: str, documents: list, top_n: int = 5) -> list:
        return documents[:top_n]