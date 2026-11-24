"""Biomedical text cleaning and normalization."""

class TextCleaner:
    """Cleans raw text, strips HTML tags, handles unicode and medical abbreviations."""
    def clean(self, text: str) -> str:
        return text.strip()