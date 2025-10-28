import subprocess
from agents.docu_cat_state import DocuCatState

def get_recent_commits_files(state: DocuCatState) -> list[str]:
    """
    Get changed files from the last N commits.

    Args:
        repo_path: Path to the git repository
        commit_count: Number of recent commits to analyze

    Returns:
        list: List of unique changed file paths
    """

    commit_count = state.get("commit_count", 1)
    repo_path = state.get("repo_path", ".")

    try:
        # Get the commit range (last N commits)
        result = subprocess.run(
            ['git', 'log', f'-{commit_count}', '--name-only', '--pretty=format:'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse output and get unique files
        files = set()
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line:  # Skip empty lines
                files.add(line)

        return {"changed_files": list(files)}
        
    except Exception as e:
        raise Exception(f"Error getting recent commits files: {e}")
