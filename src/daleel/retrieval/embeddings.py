"""Embedding model wrappers for biomedical representations."""

class EmbeddingManager:
    """Manages dense embedding generation."""
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name

    def embed_texts(self, texts: list) -> list:
        pass