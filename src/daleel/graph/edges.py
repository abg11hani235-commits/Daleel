"""Conditional routing logic and edge definitions."""
from daleel.graph.state import DaleelGraphState

def should_revise(state: DaleelGraphState) -> str:
    """Determine whether to re-retrieve/revise or finish."""
    if state.get("verification_result", {}).get("is_valid", True):
        return "end"
    if state.get("revision_count", 0) >= 2:
        return "end"
    return "revise"