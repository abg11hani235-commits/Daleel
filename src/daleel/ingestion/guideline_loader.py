"""Loader for clinical practice guidelines (PDF, HTML, Text)."""

class GuidelineLoader:
    """Loads and standardizes clinical practice guideline documents."""
    def __init__(self, directory: str = "data/raw/guidelines"):
        self.directory = directory

    def load_all(self):
        """Load all guidelines from directory."""
        pass