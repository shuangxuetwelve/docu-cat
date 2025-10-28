from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated


class DocuCatState(TypedDict):
    """State for the DocuCat workflow."""
    changed_files: list[str]
    repo_path: str
    commit_count: int
    messages: Annotated[list, add_messages]
