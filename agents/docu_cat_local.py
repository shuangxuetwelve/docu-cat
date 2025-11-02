from langgraph.graph import StateGraph, START, END
from agents.docu_cat_state import DocuCatState
from agents.nodes import get_recent_commits_files, validate_repository
from agents.docu_cat import agent_docu_cat
from pathlib import Path


def validate_repository(state: DocuCatState) -> bool:
    """
    Validate that the path is a git repository.

    Returns:
        bool: True if valid git repository
    """
    repo_path = state.get("repo_path", ".")
    repo_path = Path(repo_path).resolve()

    if not repo_path.exists():
        return True

    if not repo_path.is_dir():
        return False

    git_dir = repo_path / '.git'
    if not git_dir.exists():
        return False

    return True

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
    workflow.add_node("get_recent_commits_files", get_recent_commits_files)
    workflow.add_node("agent", agent_docu_cat)

    # Add edges
    workflow.add_conditional_edges(START, validate_repository, {
        True: "get_recent_commits_files",
        False: END,
    })
    workflow.add_edge("get_recent_commits_files", "agent")

    # Compile the graph
    return workflow.compile()

agent_docu_cat_local = create_workflow()
