#!/usr/bin/env python3
"""
Vector Store Module for DocuCat
Handles initialization and management of Milvus Lite vector database.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language


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


def get_supported_extensions() -> Dict[str, str]:
    """
    Get mapping of file extensions to file types supported by langchain_text_splitters.

    Returns:
        dict: Mapping of file extension to file type
    """
    # Based on Language enum from langchain_text_splitters
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective-c',
        '.mm': 'objective-c',
        '.md': 'markdown',
        '.tex': 'latex',
        '.html': 'html',
        '.htm': 'html',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sh': 'bash',
        '.bash': 'bash',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.txt': 'text',
    }
    return extension_map


def scan_repository_files(repo_path: Path) -> List[tuple]:
    """
    Scan repository for files with supported extensions.

    Args:
        repo_path: Path to the repository

    Returns:
        list: List of tuples (file_path, file_type)
    """
    supported_extensions = get_supported_extensions()
    supported_files = []

    # Directories to skip
    skip_dirs = {'.git', '.docucat', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
                 '.pytest_cache', '.tox', 'dist', 'build', '.egg-info'}

    try:
        for root, dirs, files in os.walk(repo_path):
            # Filter out skip directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                file_ext = file_path.suffix.lower()

                if file_ext in supported_extensions:
                    # Get relative path from repo root
                    try:
                        relative_path = file_path.relative_to(repo_path)
                        file_type = supported_extensions[file_ext]
                        supported_files.append((str(relative_path), file_type, str(file_path)))
                    except ValueError:
                        continue

        return supported_files

    except Exception as e:
        print(f"⚠️  Error scanning repository: {e}", file=sys.stderr)
        return []


def get_language_for_file_type(file_type: str) -> Optional[Language]:
    """
    Get Language enum value for file type if supported.

    Args:
        file_type: File type string (e.g., 'python', 'javascript')

    Returns:
        Language enum value or None if not supported
    """
    # Map file types to Language enum
    # Based on available Language enum values in langchain_text_splitters
    language_map = {
        'c': Language.C,
        'cpp': Language.CPP,
        'csharp': Language.CSHARP,
        'go': Language.GO,
        'java': Language.JAVA,
        'javascript': Language.JS,
        'typescript': Language.TS,
        'kotlin': Language.KOTLIN,
        'php': Language.PHP,
        'python': Language.PYTHON,
        'ruby': Language.RUBY,
        'rust': Language.RUST,
        'scala': Language.SCALA,
        'swift': Language.SWIFT,
        'html': Language.HTML,
        'latex': Language.LATEX,
        'markdown': Language.MARKDOWN,
        'powershell': Language.POWERSHELL,
        # Note: Some file types don't have language-specific splitters
        # and will fall back to generic splitting (e.g., objective-c, r, bash, etc.)
    }
    return language_map.get(file_type)


def split_file_into_chunks(file_path: str, file_type: str) -> List[str]:
    """
    Split a file into chunks using RecursiveCharacterTextSplitter.
    Uses language-specific splitting when available for better chunk boundaries.

    Args:
        file_path: Absolute path to the file
        file_type: Type of file (for language-specific splitting)

    Returns:
        list: List of text chunks
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Skip empty files
        if not content.strip():
            return []

        # Try to use language-specific splitter
        language = get_language_for_file_type(file_type)

        if language:
            # Use language-specific splitter for better chunk boundaries
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=200,
                chunk_overlap=30,
            )
        else:
            # Fall back to generic splitter for unsupported languages
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=200,
                chunk_overlap=30,
                length_function=len,
            )

        # Split the content
        chunks = splitter.split_text(content)

        return chunks

    except Exception as e:
        print(f"⚠️  Error splitting file {file_path}: {e}", file=sys.stderr)
        return []


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

        print(f"✅ Collection created successfully!")
        print()

        # Scan repository for supported files
        print(f"📂 Scanning repository for supported files...")
        supported_files = scan_repository_files(repo_path)

        if not supported_files:
            print(f"⚠️  No supported files found in repository")
            print()
            print(f"📊 Final Statistics:")
            print(f"   Files scanned: 0")
            print(f"   Chunks stored: 0")
            print()
            connections.disconnect("default")
            return True

        print(f"   Found {len(supported_files)} supported file(s)")
        print()

        # Process files and insert chunks
        print(f"📝 Processing files and creating chunks...")
        total_chunks = 0
        files_processed = 0

        # Prepare data for batch insert
        file_paths = []
        contents = []
        file_types = []
        embeddings = []

        for relative_path, file_type, absolute_path in supported_files:
            chunks = split_file_into_chunks(absolute_path, file_type)

            if chunks:
                files_processed += 1
                for chunk in chunks:
                    file_paths.append(relative_path)
                    contents.append(chunk[:65535])  # Ensure within max length
                    file_types.append(file_type)
                    # Empty embedding - use zero vector
                    embeddings.append([0.0] * EMBEDDING_DIM)
                    total_chunks += 1

                if files_processed % 10 == 0:
                    print(f"   Processed {files_processed}/{len(supported_files)} files...")

        print(f"   Processed all {files_processed} files")
        print()

        # Insert data into collection
        if total_chunks > 0:
            print(f"💾 Inserting {total_chunks} chunks into vector store...")

            data = [
                file_paths,
                contents,
                file_types,
                embeddings
            ]

            collection.insert(data)
            collection.flush()

            print(f"   ✓ All chunks inserted successfully")
        else:
            print(f"⚠️  No chunks created (all files might be empty)")

        print()
        print(f"✅ Vector store initialized and populated!")
        print()
        print(f"📊 Final Statistics:")
        print(f"   Database Path: {milvus_db_path}")
        print(f"   Collection: {DEFAULT_COLLECTION_NAME}")
        print(f"   Files scanned: {len(supported_files)}")
        print(f"   Files processed: {files_processed}")
        print(f"   Chunks stored: {total_chunks}")
        print(f"   Embedding Dimension: {EMBEDDING_DIM}")
        print()
        print(f"💡 Next Steps:")
        print(f"   1. Generate actual embeddings for the chunks")
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
        "--info",
        action="store_true",
        help="Show vector store information"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DocuCat Vector Store Manager")
    print("=" * 60)
    print()

    if args.info:
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
