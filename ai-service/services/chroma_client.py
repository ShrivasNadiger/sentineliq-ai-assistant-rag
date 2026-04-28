"""
services/chroma_client.py — ChromaDB Vector Database Client
Tool-75: AI Assistant with RAG | AI Developer 2

Handles all ChromaDB operations:
  - Initialize persistent collection
  - Add documents (embed + store)
  - Query similar documents (semantic search)
  - Get collection stats (for /health endpoint)

ChromaDB stores text as vectors so we can find
semantically similar content — this is the RAG pipeline core.
"""

import os
import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger("ChromaClient")

# ── Config ────────────────────────────────────────────────────────────────────
# Where ChromaDB stores its data on disk (persists between restarts)
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# Collection name — like a table in a regular database
COLLECTION_NAME = "tool75_knowledge_base"

# ── Singleton client and collection ──────────────────────────────────────────
# We reuse the same client across all requests (don't reconnect every time)
_client     = None
_collection = None


def get_client() -> chromadb.PersistentClient:
    """
    Get (or create) the ChromaDB persistent client.
    Uses singleton pattern — only one client instance per app lifetime.
    """
    global _client

    if _client is None:
        logger.info(f"Initialising ChromaDB at: {CHROMA_PERSIST_DIR}")
        _client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)  # disable telemetry
        )
        logger.info("ChromaDB client ready")

    return _client


def get_collection() -> chromadb.Collection:
    """
    Get (or create) the knowledge base collection.
    get_or_create ensures we never crash if collection already exists.
    """
    global _collection

    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}  # cosine similarity for text
        )
        logger.info(f"Collection '{COLLECTION_NAME}' ready — {_collection.count()} docs")

    return _collection


# ── Core Operations ───────────────────────────────────────────────────────────

def add_documents(documents: list[str], ids: list[str], metadatas: list[dict] = None) -> bool:
    """
    Add documents to ChromaDB collection.
    ChromaDB auto-embeds text using its built-in embedding model.

    Args:
        documents : List of text strings to store
        ids       : Unique ID for each document (must be unique strings)
        metadatas : Optional list of dicts with extra info per document
                    e.g. [{"source": "manual.pdf", "page": 1}]

    Returns:
        True if successful, False on error
    """
    try:
        collection = get_collection()

        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas or [{}] * len(documents)
        )

        logger.info(f"Added {len(documents)} documents to ChromaDB")
        return True

    except Exception as e:
        logger.error(f"Failed to add documents: {e}")
        return False


def query_similar(query_text: str, n_results: int = 3) -> list[dict]:
    """
    Find the most semantically similar documents to the query.
    This is the core of RAG — retrieve relevant context before calling Groq.

    Args:
        query_text : The question or input to search for
        n_results  : How many similar documents to return (default: 3)

    Returns:
        List of dicts, each with:
            - text     : The document text
            - id       : Document ID
            - metadata : Any metadata stored with the document
            - distance : Similarity score (lower = more similar for cosine)
    """
    try:
        collection = get_collection()

        # Can't query more results than exist in the collection
        count = collection.count()
        if count == 0:
            logger.warning("ChromaDB collection is empty — no results to return")
            return []

        n_results = min(n_results, count)

        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        # Flatten results into clean list of dicts
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "text"     : results["documents"][0][i],
                "id"       : results["ids"][0][i],
                "metadata" : results["metadatas"][0][i],
                "distance" : round(results["distances"][0][i], 4)
            })

        logger.info(f"Query returned {len(output)} results")
        return output

    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return []


def get_collection_stats() -> dict:
    """
    Return stats about the ChromaDB collection.
    Used by the /health endpoint on Day 7.

    Returns:
        dict with collection name and document count
    """
    try:
        collection = get_collection()
        return {
            "collection_name" : COLLECTION_NAME,
            "document_count"  : collection.count(),
            "status"          : "ok"
        }
    except Exception as e:
        logger.error(f"Failed to get ChromaDB stats: {e}")
        return {
            "collection_name" : COLLECTION_NAME,
            "document_count"  : 0,
            "status"          : "error"
        }


def delete_document(doc_id: str) -> bool:
    """
    Delete a document from the collection by ID.
    Useful for cleanup and testing.
    """
    try:
        collection = get_collection()
        collection.delete(ids=[doc_id])
        logger.info(f"Deleted document: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}")
        return False