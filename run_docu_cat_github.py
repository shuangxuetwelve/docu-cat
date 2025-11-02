import os
import sys
from agents import agent_docu_cat_github
from agents.utils import getResultFromState


def main():
    """Main entry point for the action."""
    pr_number = os.getenv('PR_NUMBER')
    repository = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    base_sha = os.getenv('BASE_SHA')
    head_sha = os.getenv('HEAD_SHA')

    print("=" * 60)
    print("DocuCat - GitHub Mode")
    print("=" * 60)
    print()
    print(f"📂 Repository: {repository}")
    print(f"📊 Pull Request: {pr_number}")
    print(f"📊 Base SHA: {base_sha}")
    print(f"📊 Head SHA: {head_sha}")
    print()

    initial_state = {
        "repo_path": os.getenv('GITHUB_WORKSPACE', os.getcwd()),
        "changed_files": [],
        "messages": [],
        "token": token,
        "repository": repository,
        "pr_number": pr_number,
        "base_sha": base_sha,
        "head_sha": head_sha,
    }

    try:
        state = agent_docu_cat_github.invoke(initial_state, config={"recursion_limit":50})

        # Extract results from the agent's state
        result = getResultFromState(state)
        changed_files = result.get("changed_files")
        analysis = result.get("analysis")
        documents_updated = result.get("documents_updated")

        # Print changed files
        if changed_files:
            print(f"\n✅ Found {len(changed_files)} changed file(s):\n")
            for i, file_path in enumerate(changed_files, 1):
                print(f"  {i}. {file_path}")
            print()
        else:
            print("\n📝 No changed files detected.\n")

        # Analyze and display results
        if changed_files:
            print("=" * 60)
            print("🤖 Analysis Results")
            print("   (Claude Haiku 4.5 via OpenRouter)")
            print("=" * 60)
            print()

            if analysis:
                print("📊 Analysis:")
                print("-" * 60)
                print(analysis)
                print()

                # Check for updates
                if "NO_UPDATES_NEEDED" in analysis:
                    print("✅ No documents needed updates.")
                else:
                    if documents_updated:
                        print("📝 Documents Updated:")
                        print("-" * 60)
                        for doc in documents_updated:
                            print(f"  ✓ {doc}")
                    else:
                        print("ℹ️  No documents were updated.")
                print()
        elif not changed_files:
            print("ℹ️  No changes to analyze.\n")
    except Exception as e:
        print(f"L Error running workflow: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)


if __name__ == '__main__':
    main()
