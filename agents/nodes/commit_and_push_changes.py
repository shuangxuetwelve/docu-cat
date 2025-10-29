import subprocess
import sys
from agents.docu_cat_state import DocuCatState


def configure_git(working_dir: str = None):
    """
    Configure git user for commits.
    Uses GitHub Actions bot identity.

    Args:
        working_dir: Directory to run git commands in (defaults to current directory)
    """
    try:
        subprocess.run(
            ['git', 'config', 'user.name', 'DocuCat'],
            cwd=working_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.email', 'docu-cat@users.noreply.github.com'],
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

def commit_and_push_changes(state: DocuCatState):
    """
    Create a commit with updated documents and push to the PR branch.

    Args:
        documents_updated: List of document file paths that were updated
        working_dir: Directory to run git commands in (defaults to current directory)
    """
    repo_path = state.get("repo_path")
    documents_updated = state.get("documents_updated")
    if not documents_updated:
        return

    try:
        # Configure git
        configure_git(repo_path)

        # Stage the updated files
        print(f"📦 Staging {len(documents_updated)} updated document(s)...")
        for doc in documents_updated:
            result = subprocess.run(
                ['git', 'add', doc],
                cwd=repo_path,
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
            cwd=repo_path,
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
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        print("  ✓ Commit created")

        # Push to the PR branch
        print()
        print("🚀 Pushing to PR branch...")
        subprocess.run(
            ['git', 'push'],
            cwd=repo_path,
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
        return
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        print()
        print("⚠️  The documentation was updated locally but could not be pushed.", file=sys.stderr)
        return
        