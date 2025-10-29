from langgraph.graph import StateGraph, START, END
from agents.docu_cat_state import DocuCatState
from agents.nodes import read_pr_configuration, validate_repository
from agents.docu_cat_2 import agent_docu_cat


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for running DocuCat locally.

    Args:
    Returns:
        Compiled StateGraph workflow
    """
    # Create the graph
    workflow = StateGraph(DocuCatState)

    # Add nodes
    workflow.add_node("read_pr_configuration", read_pr_configuration)

    # Add edges
    workflow.add_edge(START, "read_pr_configuration")
    workflow.add_edge("read_pr_configuration", END)

    # Compile the graph
    return workflow.compile()

agent_docu_cat_github = create_workflow()
