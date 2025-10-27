#!/usr/bin/env python3
"""
Vector Store Module for DocuCat
Handles initialization and management of Milvus Lite vector database.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)


# Default collection name for code and document embeddings
DEFAULT_COLLECTION_NAME = "docu_cat_embeddings"

# Embedding dimension for sentence-transformers/all-MiniLM-L6-v2
# This is a lightweight model good for code and documentation
EMBEDDING_DIM = 384


def get_vector_store_path(repo_path: str) -> Path:
    """
    Get the path to the vector store directory.

    Args:
        repo_path: Path to the repository

    Returns:
        Path: Path to the .docucat directory
    """
    repo_path = Path(repo_path).resolve()
    return repo_path / ".docucat"


def get_milvus_db_path(repo_path: str) -> Path:
    """
    Get the path to the Milvus database file.

    Args:
        repo_path: Path to the repository

    Returns:
        Path: Path to the Milvus database file
    """
    return get_vector_store_path(repo_path) / "milvus.db"


def initialize_vector_store(repo_path: str, force: bool = False) -> bool:
    """
    Initialize an empty Milvus Lite vector store.

    Args:
        repo_path: Path to the target repository
        force: If True, recreate the store even if it exists

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        repo_path = Path(repo_path).resolve()

        # Validate repository path
        if not repo_path.exists():
            print(f"❌ Error: Repository path does not exist: {repo_path}", file=sys.stderr)
            return False

        if not repo_path.is_dir():
            print(f"❌ Error: Path is not a directory: {repo_path}", file=sys.stderr)
            return False

        # Create .docucat directory
        docucat_dir = get_vector_store_path(repo_path)
        milvus_db_path = get_milvus_db_path(repo_path)

        # Check if store already exists
        if milvus_db_path.exists() and not force:
            print(f"⚠️  Vector store already exists at: {docucat_dir}")
            print(f"   Use --force to recreate it")
            return False

        # Create directory if it doesn't exist
        docucat_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {docucat_dir}")

        # If force is True and DB exists, remove it
        if force and milvus_db_path.exists():
            print(f"🗑️  Removing existing database...")
            # Need to disconnect first if connected
            try:
                connections.disconnect("default")
            except:
                pass
            # Remove the database file
            milvus_db_path.unlink()

        # Connect to Milvus Lite
        print(f"🔌 Connecting to Milvus Lite...")
        connections.connect(
            alias="default",
            uri=str(milvus_db_path)
        )

        # Drop collection if it exists (for force mode)
        if force and utility.has_collection(DEFAULT_COLLECTION_NAME):
            print(f"🗑️  Dropping existing collection: {DEFAULT_COLLECTION_NAME}")
            utility.drop_collection(DEFAULT_COLLECTION_NAME)

        # Create collection schema
        print(f"📋 Creating collection schema...")
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="Primary key"
            ),
            FieldSchema(
                name="file_path",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="Path to the file relative to repository root"
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="Content of the code or document chunk"
            ),
            FieldSchema(
                name="file_type",
                dtype=DataType.VARCHAR,
                max_length=50,
                description="Type of file (e.g., 'python', 'markdown', 'javascript')"
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=EMBEDDING_DIM,
                description="Embedding vector for semantic search"
            ),
        ]

        schema = CollectionSchema(
            fields=fields,
            description="DocuCat code and document embeddings",
            enable_dynamic_field=True
        )

        # Create collection
        print(f"🗃️  Creating collection: {DEFAULT_COLLECTION_NAME}")
        collection = Collection(
            name=DEFAULT_COLLECTION_NAME,
            schema=schema,
            using="default"
        )

        # Create index for vector field
        print(f"🔍 Creating index for vector search...")
        index_params = {
            "index_type": "FLAT",  # Simple exact search, good for small datasets
            "metric_type": "L2",   # L2 distance
            "params": {}
        }

        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        print(f"✅ Vector store initialized successfully!")
        print()
        print(f"📊 Collection Details:")
        print(f"   Name: {DEFAULT_COLLECTION_NAME}")
        print(f"   Embedding Dimension: {EMBEDDING_DIM}")
        print(f"   Database Path: {milvus_db_path}")
        print()
        print(f"💡 Next Steps:")
        print(f"   1. Run embedding generation to populate the store")
        print(f"   2. Use the store for semantic code/document search")
        print()

        # Disconnect
        connections.disconnect("default")

        return True

    except Exception as e:
        print(f"❌ Error initializing vector store: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def check_vector_store(repo_path: str) -> bool:
    """
    Check if a vector store exists and is valid.

    Args:
        repo_path: Path to the repository

    Returns:
        bool: True if store exists and is valid, False otherwise
    """
    try:
        milvus_db_path = get_milvus_db_path(repo_path)

        if not milvus_db_path.exists():
            return False

        # Try to connect and check collection
        connections.connect(
            alias="default",
            uri=str(milvus_db_path)
        )

        has_collection = utility.has_collection(DEFAULT_COLLECTION_NAME)

        connections.disconnect("default")

        return has_collection

    except Exception as e:
        print(f"⚠️  Error checking vector store: {e}", file=sys.stderr)
        return False


def get_store_info(repo_path: str) -> Optional[dict]:
    """
    Get information about the vector store.

    Args:
        repo_path: Path to the repository

    Returns:
        dict: Store information or None if store doesn't exist
    """
    try:
        if not check_vector_store(repo_path):
            return None

        milvus_db_path = get_milvus_db_path(repo_path)

        # Connect to store
        connections.connect(
            alias="default",
            uri=str(milvus_db_path)
        )

        # Get collection
        collection = Collection(DEFAULT_COLLECTION_NAME)

        # Get stats
        collection.load()
        num_entities = collection.num_entities

        info = {
            "path": str(milvus_db_path),
            "collection_name": DEFAULT_COLLECTION_NAME,
            "num_documents": num_entities,
            "embedding_dim": EMBEDDING_DIM,
        }

        connections.disconnect("default")

        return info

    except Exception as e:
        print(f"⚠️  Error getting store info: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    """Command-line interface for vector store operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize Milvus Lite vector store for DocuCat"
    )
    parser.add_argument(
        "repo_path",
        help="Path to the target repository"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of existing vector store"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if vector store exists"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show vector store information"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DocuCat Vector Store Manager")
    print("=" * 60)
    print()

    if args.check:
        # Check if store exists
        exists = check_vector_store(args.repo_path)
        if exists:
            print(f"✅ Vector store exists at: {get_vector_store_path(args.repo_path)}")
            sys.exit(0)
        else:
            print(f"❌ No vector store found at: {get_vector_store_path(args.repo_path)}")
            sys.exit(1)

    elif args.info:
        # Show store info
        info = get_store_info(args.repo_path)
        if info:
            print(f"📊 Vector Store Information:")
            print(f"   Path: {info['path']}")
            print(f"   Collection: {info['collection_name']}")
            print(f"   Documents: {info['num_documents']}")
            print(f"   Embedding Dimension: {info['embedding_dim']}")
            sys.exit(0)
        else:
            print(f"❌ No vector store found or error accessing store")
            sys.exit(1)

    else:
        # Initialize store
        success = initialize_vector_store(args.repo_path, force=args.force)
        sys.exit(0 if success else 1)
