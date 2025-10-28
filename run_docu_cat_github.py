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

from agents import start_docu_cat
from configuration_expert import get_docucat_configuration
from comment_instructions_parser import parse_comment_instructions, format_instructions_for_analysis


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


def get_pr_comments(token, repository, pr_number):
    """
    Get all comments from a GitHub pull request.

    Args:
        token: GitHub API token
        repository: Repository in format 'owner/repo'
        pr_number: Pull request number

    Returns:
        list: List of comment dictionaries with 'user', 'body', and 'created_at'
    """
    url = f"https://api.github.com/repos/{repository}/issues/{pr_number}/comments"

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'DocuCat-Action'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            comments = []
            for comment in data:
                comments.append({
                    'user': comment['user']['login'],
                    'body': comment['body'],
                    'created_at': comment['created_at']
                })
            return comments
    except urllib.error.HTTPError as e:
        print(f"⚠️  Error fetching PR comments: {e.code} {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"⚠️  Error fetching PR comments: {e}", file=sys.stderr)
        return []


def post_comment_to_pr(token, repository, pr_number, comment_body):
    """
    Post a comment to a GitHub pull request.

    Args:
        token: GitHub API token
        repository: Repository in format 'owner/repo'
        pr_number: Pull request number
        comment_body: The comment text in Markdown format

    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://api.github.com/repos/{repository}/issues/{pr_number}/comments"

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'DocuCat-Action',
        'Content-Type': 'application/json'
    }

    data = json.dumps({'body': comment_body}).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            if response.status == 201:
                print("✅ Comment posted to PR successfully")
                return True
            else:
                print(f"⚠️  Unexpected response status: {response.status}")
                return False
    except urllib.error.HTTPError as e:
        print(f"❌ Error posting comment: {e.code} {e.reason}", file=sys.stderr)
        error_body = e.read().decode()
        print(f"   Response: {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error posting comment: {e}", file=sys.stderr)
        return False


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


def format_pr_comment(result: dict, config: dict, changed_files: list[str]) -> str:
    """
    Format a PR comment summarizing DocuCat's analysis and actions.

    Args:
        result: Analysis result dictionary from run_docu_cat
        config: DocuCat configuration dictionary
        changed_files: List of changed files in the PR

    Returns:
        Formatted comment in Markdown
    """
    comment = "## 🐱 DocuCat Summary\n\n"

    # Add configuration info
    comment += "**Configuration:**\n"
    comment += f"- Enabled: {'✅ Yes' if config['enabled'] else '❌ No'}\n"
    comment += f"- Create Commits: {'✅ Yes' if config['shouldCreateCommits'] else '❌ No'}\n"
    comment += "\n"

    # Add changed files summary
    comment += f"**Changed Files ({len(changed_files)}):**\n"
    for file in changed_files[:10]:  # Limit to first 10 files
        comment += f"- `{file}`\n"
    if len(changed_files) > 10:
        comment += f"- ... and {len(changed_files) - 10} more\n"
    comment += "\n"

    # Add analysis section
    if result.get('analysis'):
        comment += "### 🔍 Analysis\n\n"
        comment += result['analysis'] + "\n\n"

    # Add documentation update summary
    if result.get('no_updates_needed'):
        comment += "### ✅ No Documentation Updates Needed\n\n"
        comment += "After analyzing the code changes, DocuCat determined that no documentation updates are required.\n"
    elif result.get('documents_updated'):
        docs = result['documents_updated']
        comment += f"### 📝 Documentation Updated ({len(docs)})\n\n"
        comment += "The following documentation files were updated:\n\n"
        for doc in docs:
            comment += f"- ✅ `{doc}`\n"
        comment += "\n"

        if config['shouldCreateCommits']:
            comment += "**Status:** Changes have been committed and pushed to this PR.\n"
        else:
            comment += "**Status:** Changes were analyzed but not committed (as per configuration).\n"
    else:
        comment += "### ℹ️ Analysis Complete\n\n"
        comment += "DocuCat completed its analysis but no documentation files were updated.\n"

    # Add footer
    comment += "\n---\n"
    comment += "*🤖 This comment was automatically generated by [DocuCat](https://github.com/lu/docu-cat) using Claude Haiku 4.5*\n"

    return comment


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

    # Read DocuCat configuration from PR description
    config = get_docucat_configuration()

    # Check if DocuCat is enabled
    if not config['enabled']:
        print("⏭️  DocuCat is disabled via PR description configuration.")
        print("   Skipping analysis and documentation updates.")
        print()
        print("=" * 60)
        sys.exit(0)

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

        result = start_docu_cat(changed_files, repo_path)

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

            # Commit and push the changes back to the PR (if enabled)
            if config['shouldCreateCommits']:
                commit_and_push_changes(result['documents_updated'], repo_path)
            else:
                print("ℹ️  Commit creation is disabled via PR description configuration.")
                print("   Documents were updated locally but not committed.")
                print()
        else:
            print("ℹ️  No documents were updated.")
        print()

        # Post summary comment to PR (when running as GitHub Action)
        if token and repository and pr_number:
            print("=" * 60)
            print("💬 Posting Summary Comment to PR")
            print("=" * 60)
            print()

            comment = format_pr_comment(result, config, changed_files)
            post_comment_to_pr(token, repository, pr_number, comment)
            print()

    print("=" * 60)


if __name__ == '__main__':
    main()
