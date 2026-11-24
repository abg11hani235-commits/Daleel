"""Graph state definitions for Daleel multi-agent pipeline."""
from typing import TypedDict, List, Dict, Any, Optional

class DaleelGraphState(TypedDict):
    """Global state flowing through the Daleel LangGraph workflow."""
    query: str
    pico: Optional[Dict[str, str]]
    search_plan: Optional[List[str]]
    retrieved_docs: List[Dict[str, Any]]
    appraised_docs: List[Dict[str, Any]]
    synthesized_answer: Optional[str]
    verification_result: Optional[Dict[str, Any]]
    revision_count: int