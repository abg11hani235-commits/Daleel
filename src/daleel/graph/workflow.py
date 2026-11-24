"""Compilation of the Daleel multi-agent state graph."""
from langgraph.graph import StateGraph, END
from daleel.graph.state import DaleelGraphState
from daleel.graph.nodes import plan_node, search_node, appraisal_node, synthesis_node, verifier_node
from daleel.graph.edges import should_revise

def build_daleel_workflow():
    """Builds and compiles the Daleel LangGraph workflow."""
    workflow = StateGraph(DaleelGraphState)

    workflow.add_node("planner", plan_node)
    workflow.add_node("searcher", search_node)
    workflow.add_node("appraiser", appraisal_node)
    workflow.add_node("synthesizer", synthesis_node)
    workflow.add_node("verifier", verifier_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "searcher")
    workflow.add_edge("searcher", "appraiser")
    workflow.add_edge("appraiser", "synthesizer")
    workflow.add_edge("synthesizer", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        should_revise,
        {
            "revise": "searcher",
            "end": END
        }
    )

    return workflow.compile()