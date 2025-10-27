#!/usr/bin/env python3
"""
Vector Store Module for DocuCat
Handles initialization and management of Milvus Lite vector database.
"""

import os
import json
import subprocess
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
from langchain_google_genai import GoogleGenerativeAIEmbeddings


# Default collection name for code and document embeddings
DEFAULT_COLLECTION_NAME = "docu_cat_embeddings"

# Embedding dimension for Gemini
EMBEDDING_DIM = 256


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


def get_store_json_path(repo_path: str) -> Path:
    """
    Get the path to the store.json metadata file.

    Args:
        repo_path: Path to the repository

    Returns:
        Path: Path to the store.json file
    """
    return get_vector_store_path(repo_path) / "store.json"


def get_current_git_sha(repo_path: Path) -> Optional[str]:
    """
    Get the full SHA of the current git commit.

    Args:
        repo_path: Path to the git repository

    Returns:
        str: Full SHA of the current commit, or None if not a git repo or error occurs
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def save_store_metadata(repo_path: Path, commit_sha: str) -> bool:
    """
    Save metadata to store.json file in the .docucat directory.

    Args:
        repo_path: Path to the repository
        commit_sha: Full SHA of the current commit

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        store_json_path = get_store_json_path(repo_path)

        metadata = {
            "last_update_sha": commit_sha
        }

        with open(store_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return True
    except Exception:
        return False


def load_store_metadata(repo_path: Path) -> Optional[Dict]:
    """
    Load metadata from store.json file in the .docucat directory.

    Args:
        repo_path: Path to the repository

    Returns:
        dict: Metadata dictionary with 'last_update_sha', or None if file doesn't exist or error occurs
    """
    try:
        store_json_path = get_store_json_path(repo_path)

        if not store_json_path.exists():
            return None

        with open(store_json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        return metadata
    except Exception:
        return None


def get_changed_files(repo_path: Path, old_sha: str, new_sha: str) -> tuple[List[str], Optional[str]]:
    """
    Get list of files that changed between two commits.

    Args:
        repo_path: Path to the git repository
        old_sha: Old commit SHA
        new_sha: New commit SHA

    Returns:
        tuple: (list of changed file paths relative to repo root, error message or None)
    """
    try:
        # Use git diff to get list of changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", old_sha, new_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Filter out empty lines
        changed_files = [line.strip() for line in result.stdout.split('\n') if line.strip()]

        return changed_files, None
    except subprocess.CalledProcessError as e:
        return [], f"Error getting changed files: {e.stderr}"
    except Exception as e:
        return [], f"Error getting changed files: {str(e)}"


def delete_chunks_by_file_path(collection: Collection, file_path: str) -> tuple[int, Optional[str]]:
    """
    Delete all chunks for a specific file from the collection.

    Args:
        collection: Milvus collection
        file_path: Relative path to the file

    Returns:
        tuple: (number of chunks deleted, error message or None)
    """
    try:
        # Query to find all entities with matching file_path
        expr = f'file_path == "{file_path}"'

        # Get the IDs of entities to delete
        collection.load()
        results = collection.query(
            expr=expr,
            output_fields=["id"]
        )

        if not results:
            return 0, None

        # Extract IDs
        ids_to_delete = [result["id"] for result in results]

        # Delete the entities
        collection.delete(expr=f"id in {ids_to_delete}")
        collection.flush()

        return len(ids_to_delete), None
    except Exception as e:
        return 0, f"Error deleting chunks for {file_path}: {str(e)}"


def create_embeddings_model():
    """
    Create and return a Gemini embeddings model.
    
    Returns:
        GoogleGenerativeAIEmbeddings: Configured embeddings model
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT",
        google_api_key=api_key,
    )


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


def scan_repository_files(repo_path: Path) -> tuple[List[tuple], Optional[str]]:
    """
    Scan repository for files with supported extensions.

    Args:
        repo_path: Path to the repository

    Returns:
        tuple: (list of tuples (file_path, file_type, absolute_path), error message or None)
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

        return supported_files, None

    except Exception as e:
        return [], f"Error scanning repository: {e}"


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


def split_file_into_chunks(file_path: str, file_type: str) -> tuple[List[str], Optional[str]]:
    """
    Split a file into chunks using RecursiveCharacterTextSplitter.
    Uses language-specific splitting when available for better chunk boundaries.

    Args:
        file_path: Absolute path to the file
        file_type: Type of file (for language-specific splitting)

    Returns:
        tuple: (list of text chunks, error message or None)
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Skip empty files
        if not content.strip():
            return [], None

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

        return chunks, None

    except Exception as e:
        return [], f"Error splitting file {file_path}: {e}"


def initialize_vector_store(repo_path: str, force: bool = False) -> Dict:
    """
    Initialize an empty Milvus Lite vector store.

    Args:
        repo_path: Path to the target repository
        force: If True, recreate the store even if it exists

    Returns:
        dict: Result containing 'success' (bool), and additional data or error message
              On success: {
                  'success': True,
                  'db_path': str,
                  'collection_name': str,
                  'files_scanned': int,
                  'files_processed': int,
                  'chunks_stored': int,
                  'embedding_dim': int,
                  'store_existed': bool
              }
              On failure: {
                  'success': False,
                  'error': str,
                  'error_type': str  # 'validation', 'already_exists', 'scan_error', 'processing_error'
              }
    """
    try:
        repo_path = Path(repo_path).resolve()

        # Validate repository path
        if not repo_path.exists():
            return {
                'success': False,
                'error': f"Repository path does not exist: {repo_path}",
                'error_type': 'validation'
            }

        if not repo_path.is_dir():
            return {
                'success': False,
                'error': f"Path is not a directory: {repo_path}",
                'error_type': 'validation'
            }

        # Create .docucat directory
        docucat_dir = get_vector_store_path(repo_path)
        milvus_db_path = get_milvus_db_path(repo_path)

        # Check if store already exists
        if milvus_db_path.exists() and not force:
            return {
                'success': False,
                'error': f"Vector store already exists at: {docucat_dir}",
                'error_type': 'already_exists',
                'store_path': str(docucat_dir)
            }

        # Create directory if it doesn't exist
        docucat_dir.mkdir(parents=True, exist_ok=True)

        # If force is True and DB exists, remove it
        store_existed = False
        if force and milvus_db_path.exists():
            store_existed = True
            # Need to disconnect first if connected
            try:
                connections.disconnect("default")
            except:
                pass
            # Remove the database file
            milvus_db_path.unlink()

        # Connect to Milvus Lite
        connections.connect(
            alias="default",
            uri=str(milvus_db_path)
        )

        # Drop collection if it exists (for force mode)
        if force and utility.has_collection(DEFAULT_COLLECTION_NAME):
            utility.drop_collection(DEFAULT_COLLECTION_NAME)

        # Create collection schema
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
        collection = Collection(
            name=DEFAULT_COLLECTION_NAME,
            schema=schema,
            using="default"
        )

        # Create index for vector field
        index_params = {
            "index_type": "FLAT",  # Simple exact search, good for small datasets
            "metric_type": "L2",   # L2 distance
            "params": {}
        }

        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        # Scan repository for supported files
        supported_files, scan_error = scan_repository_files(repo_path)

        if scan_error:
            connections.disconnect("default")
            return {
                'success': False,
                'error': scan_error,
                'error_type': 'scan_error'
            }

        if not supported_files:
            connections.disconnect("default")

            # Save metadata to store.json
            commit_sha = get_current_git_sha(repo_path)
            if commit_sha:
                save_store_metadata(repo_path, commit_sha)

            return {
                'success': True,
                'db_path': str(milvus_db_path),
                'collection_name': DEFAULT_COLLECTION_NAME,
                'files_scanned': 0,
                'files_processed': 0,
                'chunks_stored': 0,
                'embedding_dim': EMBEDDING_DIM,
                'store_existed': store_existed
            }

        # Process files and insert chunks
        total_chunks = 0
        files_processed = 0
        processing_errors = []

        # Initialize embeddings model
        try:
            embeddings_model = create_embeddings_model()
        except ValueError as e:
            connections.disconnect("default")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'processing_error'
            }

        # Prepare data for batch insert
        file_paths = []
        contents = []
        file_types = []
        text_chunks = []  # Store text for embedding generation

        for relative_path, file_type, absolute_path in supported_files:
            chunks, error = split_file_into_chunks(absolute_path, file_type)

            if error:
                processing_errors.append((relative_path, error))
                continue

            if chunks:
                files_processed += 1
                for chunk in chunks:
                    file_paths.append(relative_path)
                    contents.append(chunk[:65535])  # Ensure within max length
                    file_types.append(file_type)
                    text_chunks.append(chunk)
                    total_chunks += 1

        # Generate embeddings and insert data into collection
        if total_chunks > 0:
            # Generate embeddings for all chunks with specified dimensionality
            try:
                embeddings = embeddings_model.embed_documents(
                    text_chunks,
                    output_dimensionality=EMBEDDING_DIM
                )
                
                # Ensure embeddings have the correct dimension
                if embeddings and len(embeddings[0]) != EMBEDDING_DIM:
                    connections.disconnect("default")
                    return {
                        'success': False,
                        'error': f"Embedding dimension mismatch: expected {EMBEDDING_DIM}, got {len(embeddings[0])}",
                        'error_type': 'processing_error'
                    }
            except Exception as e:
                connections.disconnect("default")
                return {
                    'success': False,
                    'error': f"Error generating embeddings: {str(e)}",
                    'error_type': 'processing_error'
                }

            data = [
                file_paths,
                contents,
                file_types,
                embeddings
            ]

            collection.insert(data)
            collection.flush()

        # Disconnect
        connections.disconnect("default")

        # Save metadata to store.json
        commit_sha = get_current_git_sha(repo_path)
        if commit_sha:
            save_store_metadata(repo_path, commit_sha)

        return {
            'success': True,
            'db_path': str(milvus_db_path),
            'collection_name': DEFAULT_COLLECTION_NAME,
            'files_scanned': len(supported_files),
            'files_processed': files_processed,
            'chunks_stored': total_chunks,
            'embedding_dim': EMBEDDING_DIM,
            'store_existed': store_existed,
            'processing_errors': processing_errors if processing_errors else None
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_type': 'processing_error',
            'traceback': error_trace
        }


def update_vector_store(repo_path: str) -> Dict:
    """
    Update the vector store by processing only changed files since last update.

    Args:
        repo_path: Path to the target repository

    Returns:
        dict: Result containing 'success' (bool), and additional data or error message
              On success: {
                  'success': True,
                  'old_sha': str,
                  'new_sha': str,
                  'changed_files': int,
                  'processed_files': int,
                  'chunks_deleted': int,
                  'chunks_added': int
              }
              On failure: {
                  'success': False,
                  'error': str,
                  'error_type': str
              }
    """
    try:
        repo_path = Path(repo_path).resolve()

        # Validate repository path
        if not repo_path.exists():
            return {
                'success': False,
                'error': f"Repository path does not exist: {repo_path}",
                'error_type': 'validation'
            }

        if not repo_path.is_dir():
            return {
                'success': False,
                'error': f"Path is not a directory: {repo_path}",
                'error_type': 'validation'
            }

        # Check if vector store exists
        milvus_db_path = get_milvus_db_path(repo_path)
        if not milvus_db_path.exists():
            return {
                'success': False,
                'error': f"Vector store does not exist. Use 'rag --init' to create it first.",
                'error_type': 'validation'
            }

        # Load metadata to get last update SHA
        metadata = load_store_metadata(repo_path)
        if not metadata or 'last_update_sha' not in metadata:
            return {
                'success': False,
                'error': f"No store.json found or missing last_update_sha. Use 'rag --force-init' to recreate the store.",
                'error_type': 'validation'
            }

        old_sha = metadata['last_update_sha']

        # Get current commit SHA
        new_sha = get_current_git_sha(repo_path)
        if not new_sha:
            return {
                'success': False,
                'error': f"Could not get current git commit SHA. Is this a git repository?",
                'error_type': 'validation'
            }

        # Check if there are any changes
        if old_sha == new_sha:
            return {
                'success': True,
                'old_sha': old_sha,
                'new_sha': new_sha,
                'changed_files': 0,
                'processed_files': 0,
                'chunks_deleted': 0,
                'chunks_added': 0,
                'message': 'No changes since last update'
            }

        # Get changed files
        changed_files, error = get_changed_files(repo_path, old_sha, new_sha)
        if error:
            return {
                'success': False,
                'error': error,
                'error_type': 'git_error'
            }

        if not changed_files:
            # Update metadata even if no files changed
            save_store_metadata(repo_path, new_sha)
            return {
                'success': True,
                'old_sha': old_sha,
                'new_sha': new_sha,
                'changed_files': 0,
                'processed_files': 0,
                'chunks_deleted': 0,
                'chunks_added': 0,
                'message': 'No files changed'
            }

        # Connect to Milvus
        connections.connect(
            alias="default",
            uri=str(milvus_db_path)
        )

        # Get collection
        collection = Collection(DEFAULT_COLLECTION_NAME)

        # Initialize embeddings model
        try:
            embeddings_model = create_embeddings_model()
        except ValueError as e:
            connections.disconnect("default")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'processing_error'
            }

        # Get supported extensions
        supported_extensions = get_supported_extensions()

        # Process each changed file
        total_chunks_deleted = 0
        total_chunks_added = 0
        processed_files = 0
        processing_errors = []

        for changed_file in changed_files:
            # Get file extension
            file_ext = Path(changed_file).suffix.lower()

            # Skip files with unsupported extensions
            if file_ext not in supported_extensions:
                continue

            file_type = supported_extensions[file_ext]
            absolute_path = repo_path / changed_file

            # Delete old chunks for this file
            chunks_deleted, error = delete_chunks_by_file_path(collection, changed_file)
            if error:
                processing_errors.append((changed_file, error))
                continue

            total_chunks_deleted += chunks_deleted

            # If file still exists, add new chunks
            if absolute_path.exists():
                chunks, error = split_file_into_chunks(str(absolute_path), file_type)

                if error:
                    processing_errors.append((changed_file, error))
                    continue

                if chunks:
                    # Prepare data for this file
                    file_paths = [changed_file] * len(chunks)
                    contents = [chunk[:65535] for chunk in chunks]
                    file_types = [file_type] * len(chunks)

                    # Generate embeddings
                    try:
                        embeddings = embeddings_model.embed_documents(
                            chunks,
                            output_dimensionality=EMBEDDING_DIM
                        )

                        # Insert chunks
                        data = [
                            file_paths,
                            contents,
                            file_types,
                            embeddings
                        ]

                        collection.insert(data)
                        collection.flush()

                        total_chunks_added += len(chunks)
                    except Exception as e:
                        processing_errors.append((changed_file, f"Error generating embeddings: {str(e)}"))
                        continue

            processed_files += 1

        # Disconnect
        connections.disconnect("default")

        # Update metadata with new SHA
        save_store_metadata(repo_path, new_sha)

        return {
            'success': True,
            'old_sha': old_sha,
            'new_sha': new_sha,
            'changed_files': len(changed_files),
            'processed_files': processed_files,
            'chunks_deleted': total_chunks_deleted,
            'chunks_added': total_chunks_added,
            'processing_errors': processing_errors if processing_errors else None
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_type': 'processing_error',
            'traceback': error_trace
        }


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

    except Exception:
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

    except Exception:
        return None
