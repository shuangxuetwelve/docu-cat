from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Optional


class DocuCatConfig(TypedDict):
    """DocuCat configuration extracted from PR description."""
    enabled: bool
    shouldCreateCommits: bool

class DocuCatState(TypedDict):
    """State for the DocuCat workflow."""
    changed_files: list[str]
    repo_path: str
    commit_count: int
    messages: Annotated[list, add_messages]
    config: Optional[DocuCatConfig]
    token: Optional[str]
    repository: Optional[str]
    pr_number: Optional[int]
    base_sha: Optional[str]
    head_sha: Optional[str]
