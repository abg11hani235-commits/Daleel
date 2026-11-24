"""Planner Agent: Decomposes clinical queries into PICO questions and search strategies."""

class PlannerAgent:
    """Analyzes user medical inquiry and produces structured search plans (PICO framework)."""
    def plan(self, user_query: str) -> dict:
        return {"subqueries": [user_query], "pico": {}}