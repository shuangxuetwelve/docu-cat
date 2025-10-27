#!/usr/bin/env python3
"""
DocuCat RAG (Retrieval-Augmented Generation) Tool
Command-line tool to manage vector store for semantic search.
"""

import sys
import argparse
from pathlib import Path

from vector_store import (
    initialize_vector_store,
    get_store_info,
    get_vector_store_path,
)


def main():
    """Main entry point for RAG operations."""
    parser = argparse.ArgumentParser(
        description='DocuCat RAG - Manage vector store for semantic search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize vector store in current directory
  rag --init

  # Initialize vector store in a specific repository
  rag --init /path/to/repo

  # Force recreation of existing store
  rag --force-init /path/to/repo

  # Show vector store information
  rag --info

  # Show info for specific repository
  rag --info /path/to/repo

Using uv:
  uv run python rag.py --init
  uv run python rag.py --force-init /path/to/repo
  uv run python rag.py --info
        """
    )

    parser.add_argument(
        'repo_path',
        type=str,
        nargs='?',
        default='.',
        help='Path to the target repository (default: current directory)'
    )

    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize vector store'
    )

    parser.add_argument(
        '--force-init',
        action='store_true',
        dest='force_init',
        help='Force recreation of existing vector store'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Show vector store information'
    )

    args = parser.parse_args()

    # Check that at least one action is specified
    if not any([args.init, args.force_init, args.info]):
        parser.error("Please specify an action: --init, --force-init, or --info")

    # Check that only one action is specified
    actions = sum([args.init, args.force_init, args.info])
    if actions > 1:
        parser.error("Please specify only one action at a time")

    # Convert to absolute path
    repo_path = Path(args.repo_path).resolve()

    print("=" * 60)
    print("DocuCat RAG - Vector Store Manager")
    print("=" * 60)
    print()
    print(f"📂 Repository: {repo_path}")
    print(f"📁 Vector Store: {get_vector_store_path(repo_path)}")
    print()

    if args.info:
        # Show store info
        print("📊 Getting vector store information...")
        info = get_store_info(str(repo_path))

        if info:
            print()
            print(f"✅ Vector Store Information:")
            print(f"   Path: {info['path']}")
            print(f"   Collection: {info['collection_name']}")
            print(f"   Documents: {info['num_documents']}")
            print(f"   Embedding Dimension: {info['embedding_dim']}")
            print()
            sys.exit(0)
        else:
            print()
            print(f"❌ No vector store found or error accessing store")
            print()
            sys.exit(1)

    elif args.init or args.force_init:
        # Initialize store
        print("🚀 Initializing vector store...")
        print()

        success = initialize_vector_store(str(repo_path), force=args.force_init)

        if success:
            print("=" * 60)
            sys.exit(0)
        else:
            print()
            print("=" * 60)
            sys.exit(1)


if __name__ == '__main__':
    main()
