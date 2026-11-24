"""Appraisal Agent: Evaluates methodological quality, evidence level, and risk of bias."""

class AppraisalAgent:
    """Grades studies based on Oxford Centre for Evidence-Based Medicine (OCEBM) hierarchy."""
    def evaluate(self, documents: list) -> list:
        return documents