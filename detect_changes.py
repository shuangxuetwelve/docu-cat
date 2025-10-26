#!/usr/bin/env python3
"""
DocuCat GitHub Action - Detect and print changed files in a pull request
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error

from analyzer import identify_and_update_documents


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


def configure_git(working_dir: str = None):
    """
    Configure git user for commits.
    Uses GitHub Actions bot identity.

    Args:
        working_dir: Directory to run git commands in (defaults to current directory)
    """
    try:
        subprocess.run(
            ['git', 'config', 'user.name', 'github-actions[bot]'],
            cwd=working_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'],
            cwd=working_dir,
            check=True,
            capture_output=True
        )
        print("✓ Git user configured")
    except subprocess.CalledProcessError as e:
        print(f"Error configuring git: {e}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr.decode()}", file=sys.stderr)
        raise


def commit_and_push_changes(documents_updated: list[str], working_dir: str = None):
    """
    Create a commit with updated documents and push to the PR branch.

    Args:
        documents_updated: List of document file paths that were updated
        working_dir: Directory to run git commands in (defaults to current directory)
    """
    if not documents_updated:
        print("No documents to commit.")
        return

    print()
    print("=" * 60)
    print("📝 Committing and Pushing Changes")
    print("=" * 60)
    print()

    try:
        # Configure git
        configure_git(working_dir)

        # Stage the updated files
        print(f"📦 Staging {len(documents_updated)} updated document(s)...")
        for doc in documents_updated:
            result = subprocess.run(
                ['git', 'add', doc],
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"  ✓ Staged: {doc}")
            else:
                print(f"  ⚠ Could not stage: {doc} (might not exist or already staged)")

        # Check if there are changes to commit
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True
        )

        if not status_result.stdout.strip():
            print()
            print("ℹ️  No changes to commit (files may not have been modified).")
            return

        # Create commit message
        commit_message = """docs: Update documentation based on code changes

Updated by DocuCat AI assistant based on recent code changes.

Documents updated:
"""
        for doc in documents_updated:
            commit_message += f"  - {doc}\n"

        # Create the commit
        print()
        print("💾 Creating commit...")
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=working_dir,
            check=True,
            capture_output=True
        )
        print("  ✓ Commit created")

        # Push to the PR branch
        print()
        print("🚀 Pushing to PR branch...")
        subprocess.run(
            ['git', 'push'],
            cwd=working_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print("  ✓ Changes pushed successfully")

        print()
        print("✅ Documentation updates have been committed and pushed to the PR!")
        print()

    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Error during git operations: {e}", file=sys.stderr)
        if e.stderr:
            print(f"   stderr: {e.stderr}", file=sys.stderr)
        print()
        print("⚠️  The documentation was updated locally but could not be pushed.", file=sys.stderr)
        print("   This might be a permissions issue or the branch might be protected.", file=sys.stderr)
        # Don't exit with error - the analysis was successful
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        print()
        print("⚠️  The documentation was updated locally but could not be pushed.", file=sys.stderr)


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

    # Analyze changes and update documents with Claude Haiku 4.5 via OpenRouter
    if changed_files:
        print("=" * 60)
        print("🤖 Analyzing Changes and Updating Documents")
        print("   (Claude Haiku 4.5 via OpenRouter)")
        print("=" * 60)
        print()

        # Use GITHUB_WORKSPACE for the repository path in GitHub Actions
        # This points to the actual repository being analyzed, not the action's directory
        repo_path = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        print(f"📂 Repository path: {repo_path}")
        print()

        result = identify_and_update_documents(changed_files, repo_path)

        print("📊 Analysis:")
        print("-" * 60)
        print(result['analysis'])
        print()

        if result['no_updates_needed']:
            print("✅ No documents needed updates.")
        elif result['documents_updated']:
            print("📝 Documents Updated:")
            print("-" * 60)
            for doc in result['documents_updated']:
                print(f"  ✓ {doc}")
            print()

            # Commit and push the changes back to the PR
            commit_and_push_changes(result['documents_updated'], repo_path)
        else:
            print("ℹ️  No documents were updated.")
        print()

    print("=" * 60)


if __name__ == '__main__':
    main()
