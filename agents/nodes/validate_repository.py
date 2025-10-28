from agents.docu_cat_state import DocuCatState
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
