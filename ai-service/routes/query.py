"""
routes/query.py — POST /query (Full RAG Pipeline)
Tool-75: AI Assistant with RAG | AI Developer 2

This is the core RAG endpoint — it:
  1. Takes a question from the user
  2. Embeds the question and searches ChromaDB for similar docs
  3. Injects retrieved docs as context into the Groq prompt
  4. Returns AI answer + the sources it used

Request Body:
    {
        "question": "What security vulnerabilities have been reported?",
        "n_results": 3   (optional, default 3)
    }

Response:
    {
        "answer"  : "Based on the knowledge base...",
        "sources" : [
            {
                "id"       : "doc_001",
                "text"     : "A critical vulnerability was found...",
                "metadata" : { "source": "security_alert" },
                "distance" : 0.1423
            }
        ],
        "meta": {
            "model_used"       : "llama-3.3-70b-versatile",
            "tokens_used"      : 312,
            "response_time_ms" : 945.2,
            "chunks_retrieved" : 3,
            "cached"           : false
        }
    }
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq, get_fallback_response
from services.chroma_client import query_similar

logger = logging.getLogger("query")

query_bp = Blueprint("query", __name__)

# ── Load prompt template ──────────────────────────────────────────────────────
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "query_prompt.txt")

def load_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {PROMPT_PATH}")
        return "Answer the question using the context below.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{question}"


# ── Route ─────────────────────────────────────────────────────────────────────
@query_bp.route("/query", methods=["POST"])
def query():
    """
    POST /query
    Full RAG pipeline — retrieve context from ChromaDB then answer with Groq.
    """

    # ── 1. Parse and validate request ────────────────────────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error"  : "Request body must be valid JSON",
            "status" : 400
        }), 400

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error"  : "Field 'question' is required and cannot be empty",
            "status" : 400
        }), 400

    if len(question) > 2000:
        return jsonify({
            "error"  : "Field 'question' must be under 2000 characters",
            "status" : 400
        }), 400

    # How many ChromaDB chunks to retrieve (default 3, max 5)
    n_results = min(int(data.get("n_results", 3)), 5)

    # ── 2. Retrieve relevant chunks from ChromaDB ─────────────────────────────
    logger.info(f"RAG query: '{question[:80]}...' — retrieving {n_results} chunks")

    chunks = query_similar(question, n_results=n_results)

    if not chunks:
        logger.warning("ChromaDB returned no chunks — answering without context")
        context_text = "No relevant documents found in the knowledge base."
    else:
        # Build context string from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "unknown")
            context_parts.append(f"[Source {i} — {source}]\n{chunk['text']}")
        context_text = "\n\n".join(context_parts)

    logger.info(f"Retrieved {len(chunks)} chunks from ChromaDB")

    # ── 3. Build prompt with injected context ─────────────────────────────────
    prompt_template = load_prompt()
    final_prompt = prompt_template.replace("{context}", context_text).replace("{question}", question)

    # ── 4. Call Groq with context-enriched prompt ─────────────────────────────
    result = call_groq(
        prompt=final_prompt,
        system_prompt="You are a helpful business intelligence assistant. Answer using only the provided context.",
        temperature=0.3
    )

    # ── 5. Handle Groq failure ────────────────────────────────────────────────
    if not result:
        logger.warning("Groq call failed — returning fallback")
        fallback = get_fallback_response("/query")
        return jsonify({
            "answer"  : fallback["result"],
            "sources" : [],
            "meta": {
                "model_used"       : fallback["model_used"],
                "tokens_used"      : 0,
                "response_time_ms" : 0,
                "chunks_retrieved" : len(chunks),
                "cached"           : False,
                "is_fallback"      : True
            }
        }), 200

    # ── 6. Build sources list for response ────────────────────────────────────
    sources = [
        {
            "id"       : chunk["id"],
            "text"     : chunk["text"],
            "metadata" : chunk["metadata"],
            "distance" : chunk["distance"]
        }
        for chunk in chunks
    ]

    # ── 7. Return answer + sources ────────────────────────────────────────────
    return jsonify({
        "answer"  : result["text"],
        "sources" : sources,
        "meta": {
            "model_used"       : result["model_used"],
            "tokens_used"      : result["tokens_used"],
            "response_time_ms" : result["response_time_ms"],
            "chunks_retrieved" : len(chunks),
            "cached"           : False
        }
    }), 200