#!/usr/bin/env python3
"""
DocuCat Vector Store Initialization
Command-line tool to initialize Milvus Lite vector store for a repository.
"""

import sys
import argparse
from pathlib import Path

from vector_store import (
    initialize_vector_store,
    check_vector_store,
    get_store_info,
    get_vector_store_path,
)


def main():
    """Main entry point for vector store initialization."""
    parser = argparse.ArgumentParser(
        description='Initialize Milvus Lite vector store for DocuCat',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize vector store in current directory
  python init_vector_store.py .

  # Initialize vector store in a specific repository
  python init_vector_store.py /path/to/repo

  # Force recreation of existing store
  python init_vector_store.py /path/to/repo --force

  # Check if vector store exists
  python init_vector_store.py /path/to/repo --check

  # Show vector store information
  python init_vector_store.py /path/to/repo --info

Using uv:
  uv run python init_vector_store.py .
  uv run python init_vector_store.py /path/to/repo --force
        """
    )

    parser.add_argument(
        'repo_path',
        type=str,
        help='Path to the target repository'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recreation of existing vector store'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if vector store exists'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Show vector store information'
    )

    args = parser.parse_args()

    # Convert to absolute path
    repo_path = Path(args.repo_path).resolve()

    print("=" * 60)
    print("DocuCat Vector Store Manager")
    print("=" * 60)
    print()
    print(f"📂 Repository: {repo_path}")
    print(f"📁 Vector Store: {get_vector_store_path(repo_path)}")
    print()

    if args.check:
        # Check if store exists
        print("🔍 Checking vector store...")
        exists = check_vector_store(str(repo_path))

        if exists:
            print(f"✅ Vector store exists and is valid")
            sys.exit(0)
        else:
            print(f"❌ No vector store found or store is invalid")
            sys.exit(1)

    elif args.info:
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

    else:
        # Initialize store
        print("🚀 Initializing vector store...")
        print()

        success = initialize_vector_store(str(repo_path), force=args.force)

        if success:
            print("=" * 60)
            sys.exit(0)
        else:
            print()
            print("=" * 60)
            sys.exit(1)


if __name__ == '__main__':
    main()
