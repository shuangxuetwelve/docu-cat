from langgraph.graph import StateGraph, START, END
from agents.docu_cat_state import DocuCatState
from agents.nodes import commit_and_push_changes, get_changed_files_github, read_pr_configuration
from agents.docu_cat_2 import agent_docu_cat


def should_run_docu_cat(state: DocuCatState) -> bool:
    """
    Determine if DocuCat should be run based on the configuration.
    """
    return state.get("config", {}).get("enabled", False)

def should_run_docu_cat_agent(state: DocuCatState) -> bool:
    """
    Determine if DocuCat agent should be run based on the configuration.
    """
    return len(state.get("changed_files", [])) > 0

def should_commit_and_push_changes(state: DocuCatState) -> bool:
    """
    Determine if commit and push changes should be run based on the configuration.
    """
    return state.get("config", {}).get("shouldCreateCommits", False)

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
    workflow.add_node("agent", agent_docu_cat)
    workflow.add_node("commit_and_push_changes", commit_and_push_changes)
    
    # Add edges
    workflow.add_edge(START, "read_pr_configuration")
    workflow.add_conditional_edges("read_pr_configuration", should_run_docu_cat, {
        True: "get_changed_files_github",
        False: END,
    })
    workflow.add_conditional_edges("get_changed_files_github", should_run_docu_cat_agent, {
        True: "agent",
        False: END,
    })
    workflow.add_conditional_edges("agent", should_commit_and_push_changes, {
        True: "commit_and_push_changes",
        False: END,
    })
    workflow.add_edge("commit_and_push_changes", END)

    # Compile the graph
    return workflow.compile()

agent_docu_cat_github = create_workflow()
