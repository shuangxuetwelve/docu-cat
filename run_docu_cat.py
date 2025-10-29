#!/usr/bin/env python3
"""
DocuCat - Local execution entry point (Version 2)

Analyzes recent commits in a repository and detects changed files using LangGraph workflow.
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents.docu_cat_local import agent_docu_cat_local
from langchain_core.messages import AIMessage


def main():
    """Main entry point for local DocuCat execution using LangGraph workflow."""
    parser = argparse.ArgumentParser(
        description='DocuCat - Analyze recent commits and detect changed files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze last 5 commits in current directory
  docu-cat2 --count 5

  # Analyze last 10 commits in a specific repository
  docu-cat2 --path /path/to/repo --count 10

  # Analyze last commit in another repository
  docu-cat2 -p ../other-repo -c 1
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
    print("DocuCat - Local Mode (Version 2)")
    print("=" * 60)
    print()
    print(f"📂 Repository: {repo_path}")
    print(f"📊 Analyzing last {args.count} commit(s)")
    print()

    # Create initial state for the workflow
    initial_state = {
        "repo_path": str(repo_path),
        "commit_count": args.count,
        "changed_files": [],
        "messages": [],
    }

    try:
        # Run the LangGraph workflow
        print("=" * 60)
        print("Running DocuCat workflow...")
        print("=" * 60)
        print()
        result = agent_docu_cat_local.invoke(initial_state)

        # Extract results from the workflow
        changed_files = result.get("changed_files", [])
        messages = result.get("messages", [])

        # Print changed files
        if changed_files:
            print(f"\n✅ Found {len(changed_files)} changed file(s):\n")
            for i, file_path in enumerate(changed_files, 1):
                print(f"  {i}. {file_path}")
            print()
        else:
            print("\n📝 No changed files detected.\n")

        # Analyze and display results
        if changed_files and messages:
            print("=" * 60)
            print("🤖 Analysis Results")
            print("   (Claude Haiku 4.5 via OpenRouter)")
            print("=" * 60)
            print()

            # Find the final AI response
            analysis = ""
            for message in reversed(messages):
                if isinstance(message, AIMessage) and message.content:
                    analysis = message.content
                    break

            if analysis:
                print("📊 Analysis:")
                print("-" * 60)
                print(analysis)
                print()

                # Check for updates
                if "NO_UPDATES_NEEDED" in analysis:
                    print("✅ No documents needed updates.")
                else:
                    # Find all write_file tool calls to determine which documents were updated
                    documents_updated = []
                    for message in messages:
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tool_call in message.tool_calls:
                                if tool_call.get("name") == "write_file":
                                    filepath = tool_call.get("args", {}).get("filepath")
                                    if filepath and filepath not in documents_updated:
                                        documents_updated.append(filepath)

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
