#!/usr/bin/env python3
"""
DocuCat GitHub Action - Detect and print changed files in a pull request
"""

import os
import sys
import json
import urllib.request
import urllib.error

from analyzer import analyze_changed_files


def get_changed_files_from_api(token, repository, pr_number):
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
    except urllib.error.HTTPError as e:
        print(f"Error fetching changed files: {e.code} {e.reason}", file=sys.stderr)
        print(f"Response: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def get_changed_files_from_git(base_sha, head_sha):
    """
    Get changed files using git diff.

    Args:
        base_sha: Base commit SHA
        head_sha: Head commit SHA

    Returns:
        list: List of changed file paths
    """
    import subprocess

    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', base_sha, head_sha],
            capture_output=True,
            text=True,
            check=True
        )
        return [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the action."""
    event_name = os.getenv('GITHUB_EVENT_NAME')
    pr_number = os.getenv('PR_NUMBER')
    repository = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    base_sha = os.getenv('BASE_SHA')
    head_sha = os.getenv('HEAD_SHA')

    print("=" * 60)
    print("DocuCat - Changed Files Detection")
    print("=" * 60)

    # Check if this is a pull request event
    if event_name != 'pull_request':
        print(f"⚠️  This action is designed for pull_request events.")
        print(f"   Current event: {event_name}")
        sys.exit(0)

    if not pr_number:
        print("❌ No pull request number found.", file=sys.stderr)
        sys.exit(1)

    print(f"\n📋 Repository: {repository}")
    print(f"🔢 Pull Request: #{pr_number}")
    print(f"📍 Base SHA: {base_sha[:8]}...")
    print(f"📍 Head SHA: {head_sha[:8]}...")
    print()

    # Try to get changed files using the API
    changed_files = []

    if token and repository and pr_number:
        print("🔍 Fetching changed files from GitHub API...")
        changed_files = get_changed_files_from_api(token, repository, pr_number)
    elif base_sha and head_sha:
        print("🔍 Fetching changed files using git diff...")
        changed_files = get_changed_files_from_git(base_sha, head_sha)
    else:
        print("❌ Insufficient information to detect changed files.", file=sys.stderr)
        sys.exit(1)

    # Print the changed files
    if changed_files:
        print(f"\n✅ Found {len(changed_files)} changed file(s):\n")
        for i, file_path in enumerate(changed_files, 1):
            print(f"  {i}. {file_path}")
        print()
    else:
        print("\n📝 No changed files detected.\n")

    # Analyze changes with Claude Haiku 4.5 via OpenRouter
    if changed_files:
        print("=" * 60)
        print("🤖 Analyzing Changes with Claude Haiku 4.5 (via OpenRouter)")
        print("=" * 60)
        print()

        # Use GITHUB_WORKSPACE for the repository path in GitHub Actions
        # This points to the actual repository being analyzed, not the action's directory
        repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        print(f"📂 Repository path: {repo_path}")
        print()

        analysis = analyze_changed_files(changed_files, repo_path)
        print(analysis)
        print()

    print("=" * 60)


if __name__ == '__main__':
    main()
