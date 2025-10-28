#!/usr/bin/env python3
"""
DocuCat - Local execution entry point

Analyzes recent commits in a repository and detects changed files.
"""

import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents import start_docu_cat


def get_recent_commits_files(repo_path: Path, commit_count: int) -> list[str]:
    """
    Get changed files from the last N commits.

    Args:
        repo_path: Path to the git repository
        commit_count: Number of recent commits to analyze

    Returns:
        list: List of unique changed file paths
    """
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

        return sorted(files)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running git log: {e}", file=sys.stderr)
        print(f"   stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def validate_repository(repo_path: Path) -> bool:
    """
    Validate that the path is a git repository.

    Args:
        repo_path: Path to validate

    Returns:
        bool: True if valid git repository
    """
    if not repo_path.exists():
        print(f"❌ Path does not exist: {repo_path}", file=sys.stderr)
        return False

    if not repo_path.is_dir():
        print(f"❌ Path is not a directory: {repo_path}", file=sys.stderr)
        return False

    git_dir = repo_path / '.git'
    if not git_dir.exists():
        print(f"❌ Not a git repository: {repo_path}", file=sys.stderr)
        print("   (no .git directory found)", file=sys.stderr)
        return False

    return True


def main():
    """Main entry point for local DocuCat execution."""
    parser = argparse.ArgumentParser(
        description='DocuCat - Analyze recent commits and detect changed files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze last 5 commits in current directory
  docu-cat --count 5

  # Analyze last 10 commits in a specific repository
  docu-cat --path /path/to/repo --count 10

  # Analyze last commit in another repository
  docu-cat -p ../other-repo -c 1
        """
    )

    parser.add_argument(
        '-p', '--path',
        type=str,
        default='.',
        help='Path to the repository (default: current directory)'
    )

    parser.add_argument(
        '-c', '--count',
        type=int,
        default=1,
        help='Number of recent commits to analyze (default: 1)'
    )

    args = parser.parse_args()

    # Convert to absolute path
    repo_path = Path(args.path).resolve()

    print("=" * 60)
    print("DocuCat - Local Mode")
    print("=" * 60)
    print()
    print(f"📂 Repository: {repo_path}")
    print(f"📊 Analyzing last {args.count} commit(s)")
    print()

    # Validate repository
    if not validate_repository(repo_path):
        sys.exit(1)

    # Get changed files from recent commits
    print("🔍 Fetching changed files from git history...")
    changed_files = get_recent_commits_files(repo_path, args.count)

    # Print results
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

        result = start_docu_cat(changed_files, str(repo_path))

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
        else:
            print("ℹ️  No documents were updated.")
        print()

    print("=" * 60)


if __name__ == '__main__':
    main()
