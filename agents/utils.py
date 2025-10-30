from typing import TypedDict
from langchain_core.messages import AIMessage
from agents.docu_cat_state import DocuCatState


class DocuCatResult(TypedDict):
    """Result from the agents' states."""
    changed_files: list[str]
    analysis: str
    documents_updated: list[str]
    no_updates_needed: bool

def getResultFromState(state: DocuCatState) -> DocuCatResult:
    """
    Get the result from the state.

    Args:
        state: DocuCat state

    Returns:
        Result from the state
    """
    changed_files = state.get("changed_files")
    analysis = ""
    documents_updated = []
    no_updates_needed = False
    messages = state.get("messages", [])

    # Find the final AI response
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            analysis = message.content
            break


    # Check if agent indicated no updates needed
    if "NO_UPDATES_NEEDED" in analysis:
        no_updates_needed = True

    # Find all write_file tool calls to determine which documents were updated
    for message in messages:
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.get("name") == "write_file":
                    filepath = tool_call.get("args", {}).get("filepath")
                    if filepath and filepath not in documents_updated:
                        documents_updated.append(filepath)
    
    return {
        "changed_files": changed_files,
        "analysis": analysis if analysis else "No analysis available",
        "documents_updated": documents_updated,
        "no_updates_needed": no_updates_needed
    }
