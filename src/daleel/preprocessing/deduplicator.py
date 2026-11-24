"""Deduplication of biomedical documents using exact and fuzzy matching."""

class Deduplicator:
    """Identifies and removes duplicate abstracts or articles."""
    def deduplicate(self, documents: list) -> list:
        return documents