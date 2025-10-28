#!/usr/bin/env python3
"""
GitHub Action script to initialize or update the vector store.
This script runs on push events and commits the vector store changes.
"""

import os
import sys
import subprocess
from pathlib import Path

from vector_store import (
    initialize_vector_store,
    update_vector_store,
    get_store_json_path,
    get_vector_store_path,
)


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


def commit_and_push_vector_store(repo_path: str, is_init: bool = False):
    """
    Commit and push the vector store changes.

    Args:
        repo_path: Path to the repository
        is_init: Whether this is an initial creation or an update
    """
    print()
    print("=" * 60)
    print("📝 Committing and Pushing Vector Store")
    print("=" * 60)
    print()

    try:
        # Configure git
        configure_git(repo_path)

        # Stage the .docucat directory (force add since it's in .gitignore)
        docucat_path = get_vector_store_path(repo_path)
        print(f"📦 Staging vector store directory: {docucat_path}")

        result = subprocess.run(
            ['git', 'add', '-f', str(docucat_path)],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"⚠ Warning: git add returned non-zero: {result.stderr}")

        # Check if there are changes to commit
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        if not status_result.stdout.strip():
            print()
            print("ℹ️  No changes to commit (vector store may not have changed).")
            return

        # Create commit message
        if is_init:
            commit_message = """chore: Initialize vector store

Initialized vector store with code and document embeddings.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
        else:
            commit_message = """chore: Update vector store

Updated vector store with latest code and document changes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        # Create the commit
        print()
        print("💾 Creating commit...")
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        print("  ✓ Commit created")

        # Push to the branch
        print()
        print("🚀 Pushing to repository...")
        subprocess.run(
            ['git', 'push'],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        print("  ✓ Changes pushed successfully")

        print()
        print("✅ Vector store has been committed and pushed!")
        print()

    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Error during git operations: {e}", file=sys.stderr)
        if e.stderr:
            print(f"   stderr: {e.stderr}", file=sys.stderr)
        print()
        print("⚠️  The vector store was updated locally but could not be pushed.", file=sys.stderr)
        print("   This might be a permissions issue or the branch might be protected.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the action."""
    print("=" * 60)
    print("DocuCat - Vector Store Init/Update")
    print("=" * 60)
    print()

    # Get repository path from environment or use current directory
    # When running as GitHub Action, TARGET_REPO_PATH is set to the target repository
    # When running locally, GITHUB_WORKSPACE or current directory is used
    repo_path = os.getenv('TARGET_REPO_PATH') or os.getenv('GITHUB_WORKSPACE') or os.getcwd()
    repo_path = str(Path(repo_path).resolve())
    print(f"📂 Repository path: {repo_path}")

    # Verify the path exists and is a git repository
    if not Path(repo_path).exists():
        print(f"❌ Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    git_dir = Path(repo_path) / '.git'
    if not git_dir.exists():
        print(f"❌ Not a git repository: {repo_path}", file=sys.stderr)
        print(f"   .git directory not found", file=sys.stderr)
        sys.exit(1)

    # Check if GEMINI_API_KEY is set
    if not os.getenv('GEMINI_API_KEY'):
        print()
        print("❌ GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("   This is required for generating embeddings.", file=sys.stderr)
        sys.exit(1)

    # Check if store.json exists
    store_json_path = get_store_json_path(repo_path)
    store_exists = store_json_path.exists()

    print(f"📁 Vector store path: {get_vector_store_path(repo_path)}")
    print(f"📄 Store metadata: {store_json_path}")
    print(f"📊 Store exists: {'Yes' if store_exists else 'No'}")
    print()

    if store_exists:
        # Update existing vector store
        print("=" * 60)
        print("🔄 Updating existing vector store...")
        print("=" * 60)
        print()

        result = update_vector_store(repo_path)

        if not result['success']:
            print()
            print(f"❌ Error updating vector store: {result['error']}", file=sys.stderr)
            if 'traceback' in result:
                print()
                print("Full error traceback:")
                print(result['traceback'])
            sys.exit(1)

        # Display update statistics
        print()
        print("✅ Vector store updated successfully!")
        print()
        print(f"📊 Update Statistics:")
        print(f"   Old SHA: {result['old_sha'][:8]}...")
        print(f"   New SHA: {result['new_sha'][:8]}...")
        print(f"   Changed files: {result['changed_files']}")
        print(f"   Processed files: {result['processed_files']}")
        print(f"   Chunks deleted: {result['chunks_deleted']}")
        print(f"   Chunks added: {result['chunks_added']}")
        print()

        # Commit and push if there were changes
        if result['changed_files'] > 0 or result['chunks_deleted'] > 0 or result['chunks_added'] > 0:
            commit_and_push_vector_store(repo_path, is_init=False)
        else:
            print("ℹ️  No changes to commit (vector store is up to date)")
            print()

    else:
        # Initialize new vector store
        print("=" * 60)
        print("🚀 Initializing new vector store...")
        print("=" * 60)
        print()

        result = initialize_vector_store(repo_path, force=False)

        if not result['success']:
            print()
            print(f"❌ Error initializing vector store: {result['error']}", file=sys.stderr)
            if 'traceback' in result:
                print()
                print("Full error traceback:")
                print(result['traceback'])
            sys.exit(1)

        # Display initialization statistics
        print()
        print("✅ Vector store initialized successfully!")
        print()
        print(f"📊 Initialization Statistics:")
        print(f"   Files scanned: {result['files_scanned']}")
        print(f"   Files processed: {result['files_processed']}")
        print(f"   Chunks stored: {result['chunks_stored']}")
        print(f"   Embedding dimension: {result['embedding_dim']}")
        print()

        # Commit and push the new vector store
        commit_and_push_vector_store(repo_path, is_init=True)

    print("=" * 60)
    print("✅ Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
