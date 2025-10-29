import urllib.request
import json
import subprocess
from agents.docu_cat_state import DocuCatState


def get_changed_files_from_api(token, repository, pr_number) -> list[str] | None:
    """
    Get changed files using GitHub API.

    Args:
        token: GitHub API token
        repository: Repository in format 'owner/repo'
        pr_number: Pull request number

    Returns:
        list: List of changed file paths
    """
    url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/files"

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'DocuCat-Action'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return [file['filename'] for file in data]
    except:
        return

def get_changed_files_from_git(base_sha, head_sha):
    """
    Get changed files using git diff.

    Args:
        base_sha: Base commit SHA
        head_sha: Head commit SHA

    Returns:
        list: List of changed file paths
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', base_sha, head_sha],
            capture_output=True,
            text=True,
            check=True
        )
        return [f for f in result.stdout.strip().split('\n') if f]
    except:
        return

def get_changed_files_github(state: DocuCatState):
    token = state.get("token")
    repository = state.get("repository")
    pr_number = state.get("pr_number")
    base_sha = state.get("base_sha")
    head_sha = state.get("head_sha")

    changed_files = []
    if token and repository and pr_number:
        print(f"Fetching changed files from GitHub API for PR #{pr_number}")
        changed_files = get_changed_files_from_api(token, repository, pr_number)
    elif base_sha and head_sha:
        print(f"Fetching changed files from git for base SHA {base_sha} and head SHA {head_sha}")
        changed_files = get_changed_files_from_git(base_sha, head_sha)
    else:
        return
    return {"changed_files": changed_files}