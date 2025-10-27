#!/usr/bin/env python3
"""
DocuCat RAG (Retrieval-Augmented Generation) Tool
Command-line tool to manage vector store for semantic search.

This tool supports initializing, updating, and querying the vector store.
"""

import sys
import argparse
from pathlib import Path

from vector_store import (
    initialize_vector_store,
    update_vector_store,
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

  # Update vector store with changes since last update
  rag --update

  # Update vector store for specific repository
  rag --update /path/to/repo

  # Show vector store information
  rag --info

  # Show info for specific repository
  rag --info /path/to/repo

Using uv:
  uv run python rag.py --init
  uv run python rag.py --force-init /path/to/repo
  uv run python rag.py --update
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
        '--update',
        action='store_true',
        help='Update vector store with changes since last update'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Show vector store information'
    )

    args = parser.parse_args()

    # Check that at least one action is specified
    if not any([args.init, args.force_init, args.update, args.info]):
        parser.error("Please specify an action: --init, --force-init, --update, or --info")

    # Check that only one action is specified
    actions = sum([args.init, args.force_init, args.update, args.info])
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

        result = initialize_vector_store(str(repo_path), force=args.force_init)

        if not result['success']:
            # Handle different error types
            if result['error_type'] == 'validation':
                print(f"❌ Error: {result['error']}")
            elif result['error_type'] == 'already_exists':
                print(f"⚠️  {result['error']}")
                print(f"   Use 'rag --force-init' to recreate it")
            elif result['error_type'] == 'scan_error':
                print(f"❌ Error scanning repository: {result['error']}")
            elif result['error_type'] == 'processing_error':
                print(f"❌ Error initializing vector store: {result['error']}")
                if 'traceback' in result:
                    print()
                    print("Full error traceback:")
                    print(result['traceback'])
            else:
                print(f"❌ Error: {result['error']}")

            print()
            print("=" * 60)
            sys.exit(1)

        # Success - display detailed information
        print(f"📁 Created directory")
        if result.get('store_existed'):
            print(f"🗑️  Removed existing database")
        print(f"🔌 Connected to Milvus Lite")
        print(f"📋 Created collection schema")
        print(f"🗃️  Created collection: {result['collection_name']}")
        print(f"🔍 Created index for vector search")
        print(f"✅ Collection created successfully!")
        print()

        print(f"📂 Scanned repository for supported files")
        print(f"   Found {result['files_scanned']} supported file(s)")
        print()

        if result['files_scanned'] > 0:
            print(f"📝 Processed files and created chunks")
            print(f"   Processed {result['files_processed']}/{result['files_scanned']} files")
            print()

            if result['chunks_stored'] > 0:
                print(f"💾 Inserted {result['chunks_stored']} chunks into vector store")
                print(f"   ✓ All chunks inserted successfully")
            else:
                print(f"⚠️  No chunks created (all files might be empty)")

            # Show processing errors if any
            if result.get('processing_errors'):
                print()
                print(f"⚠️  Encountered {len(result['processing_errors'])} file processing errors:")
                for file_path, error in result['processing_errors'][:5]:  # Show first 5
                    print(f"   - {file_path}: {error}")
                if len(result['processing_errors']) > 5:
                    print(f"   ... and {len(result['processing_errors']) - 5} more")

        print()
        print(f"✅ Vector store initialized and populated!")
        print()
        print(f"📊 Final Statistics:")
        print(f"   Database Path: {result['db_path']}")
        print(f"   Collection: {result['collection_name']}")
        print(f"   Files scanned: {result['files_scanned']}")
        print(f"   Files processed: {result['files_processed']}")
        print(f"   Chunks stored: {result['chunks_stored']}")
        print(f"   Embedding Dimension: {result['embedding_dim']}")
        print()
        print(f"💡 Next Steps:")
        print(f"   1. Generate actual embeddings for the chunks")
        print(f"   2. Use the store for semantic code/document search")
        print()
        print("=" * 60)
        sys.exit(0)

    elif args.update:
        # Update store
        print("🔄 Updating vector store...")
        print()

        result = update_vector_store(str(repo_path))

        if not result['success']:
            # Handle different error types
            if result['error_type'] == 'validation':
                print(f"❌ Error: {result['error']}")
            elif result['error_type'] == 'git_error':
                print(f"❌ Git error: {result['error']}")
            elif result['error_type'] == 'processing_error':
                print(f"❌ Error updating vector store: {result['error']}")
                if 'traceback' in result:
                    print()
                    print("Full error traceback:")
                    print(result['traceback'])
            else:
                print(f"❌ Error: {result['error']}")

            print()
            print("=" * 60)
            sys.exit(1)

        # Success - display detailed information
        print(f"📊 Comparing commits...")
        print(f"   Old commit: {result['old_sha'][:8]}")
        print(f"   New commit: {result['new_sha'][:8]}")
        print()

        if result['changed_files'] == 0:
            print(f"✅ {result.get('message', 'No changes detected')}")
        else:
            print(f"📂 Found {result['changed_files']} changed file(s)")
            print(f"   Processed {result['processed_files']} supported file(s)")
            print()

            print(f"🗑️  Deleted {result['chunks_deleted']} old chunk(s)")
            print(f"➕ Added {result['chunks_added']} new chunk(s)")

            # Show processing errors if any
            if result.get('processing_errors'):
                print()
                print(f"⚠️  Encountered {len(result['processing_errors'])} file processing errors:")
                for file_path, error in result['processing_errors'][:5]:  # Show first 5
                    print(f"   - {file_path}: {error}")
                if len(result['processing_errors']) > 5:
                    print(f"   ... and {len(result['processing_errors']) - 5} more")

            print()
            print(f"✅ Vector store updated successfully!")

        print()
        print(f"📊 Update Statistics:")
        print(f"   Old SHA: {result['old_sha']}")
        print(f"   New SHA: {result['new_sha']}")
        print(f"   Changed files: {result['changed_files']}")
        print(f"   Processed files: {result['processed_files']}")
        print(f"   Chunks deleted: {result['chunks_deleted']}")
        print(f"   Chunks added: {result['chunks_added']}")
        print()
        print("=" * 60)
        sys.exit(0)


if __name__ == '__main__':
    main()
