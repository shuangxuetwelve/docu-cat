"""
Vector store query tool for the AI agent.

This module provides a LangChain tool that allows the agent to query
the local vector store for relevant code and document chunks. This enables
the agent to retrieve contextual information when analyzing changes.
"""

import os
from typing import Optional
from pathlib import Path
from langchain_core.tools import tool
from pymilvus import connections, Collection
from langchain_google_genai import GoogleGenerativeAIEmbeddings


@tool
def query_vector_store(query: str, repo_path: str = ".", top_k: int = 10) -> str:
    """
    Query the local vector store for relevant code and document chunks.

    Use this to find relevant code or documentation sections related to a specific topic.
    This helps you understand the codebase context when analyzing changes.

    Args:
        query: The search query (e.g., "authentication logic", "API endpoints")
        repo_path: Path to the repository (default: current directory)
        top_k: Number of results to return (default: 10)

    Returns:
        String containing relevant chunks with their file paths and content, 
        or error message if query fails
    """
    print(f"🔍 Querying vector store for query: {query}")
    try:
        from vector_store import get_milvus_db_path, DEFAULT_COLLECTION_NAME, EMBEDDING_DIM
        
        repo_path = Path(repo_path).resolve()
        milvus_db_path = get_milvus_db_path(str(repo_path))
        
        # Check if vector store exists
        if not milvus_db_path.exists():
            return f"Error: Vector store not found at {repo_path}/.docucat. Please initialize it first with 'rag --init'."
        
        # Get API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY environment variable is not set"
        
        # Create embeddings model for queries
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            task_type="RETRIEVAL_QUERY",
            google_api_key=api_key,
        )
        
        # Generate embedding for the query
        query_embedding = embeddings_model.embed_query(query)
        
        # Ensure correct dimensionality
        if len(query_embedding) != EMBEDDING_DIM:
            # Pad or truncate if needed
            if len(query_embedding) < EMBEDDING_DIM:
                query_embedding = query_embedding + [0.0] * (EMBEDDING_DIM - len(query_embedding))
            else:
                query_embedding = query_embedding[:EMBEDDING_DIM]
        
        # Connect to Milvus
        connections.connect(
            alias="default",
            uri=str(milvus_db_path)
        )
        
        # Get collection
        collection = Collection(DEFAULT_COLLECTION_NAME)
        collection.load()
        
        # Search for similar chunks
        search_params = {
            "metric_type": "L2",
            "params": {}
        }
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["file_path", "content", "file_type"]
        )

        # Disconnect
        connections.disconnect("default")
        
        # Format results
        if not results or len(results[0]) == 0:
            return "No relevant chunks found in the vector store."
        
        formatted_results = []
        formatted_results.append(f"Found {len(results[0])} relevant chunks:\n")
        
        for idx, hit in enumerate(results[0], 1):
            file_path = hit.entity.get("file_path")
            content = hit.entity.get("content")
            file_type = hit.entity.get("file_type")
            distance = hit.distance
            
            formatted_results.append(f"\n--- Result {idx} ---")
            formatted_results.append(f"File: {file_path} ({file_type})")
            formatted_results.append(f"Relevance score: {1.0 / (1.0 + distance):.3f}")
            formatted_results.append(f"Content:\n{content}")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error querying vector store: {str(e)}"

