from langgraph.graph import StateGraph, START, END
from agents.docu_cat_state import DocuCatState
from agents.nodes import get_changed_files_github, read_pr_configuration
from agents.docu_cat_2 import agent_docu_cat


def should_run_docu_cat(state: DocuCatState) -> bool:
    """
    Determine if DocuCat should be run based on the configuration.
    """
    return state.get("config", {}).get("enabled", False)

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
    workflow.add_node("get_changed_files_github", get_changed_files_github)
    # workflow.add_node("agent", agent_docu_cat)

    # Add edges
    workflow.add_edge(START, "read_pr_configuration")
    workflow.add_conditional_edges("read_pr_configuration", should_run_docu_cat, {
        True: "get_changed_files_github",
        False: END,
    })
    workflow.add_edge("get_changed_files_github", END)

    # Compile the graph
    return workflow.compile()

agent_docu_cat_github = create_workflow()
