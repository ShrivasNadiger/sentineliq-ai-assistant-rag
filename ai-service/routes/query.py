"""
routes/query.py — POST /query (Day 9 — Standardised Meta)
Tool-75: AI Assistant with RAG | AI Developer 2

Full RAG pipeline with standardised meta object on all responses.

Request Body:
    {
        "question"   : "What security issues have been reported?",
        "n_results"  : 3,          (optional, default 3)
        "skip_cache" : false       (optional, default false)
    }

Response:
    {
        "answer"  : "Based on the knowledge base...",
        "sources" : [ ... ],
        "meta": {
            "confidence"       : 0.85,
            "model_used"       : "llama-3.3-70b-versatile",
            "tokens_used"      : 312,
            "response_time_ms" : 945.2,
            "cached"           : false
        }
    }
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq, get_fallback_response
from services.chroma_client import query_similar
from services.redis_cache import cache_get, cache_set
from services.meta_helper import build_meta_from_groq, build_fallback_meta

logger = logging.getLogger("query")

query_bp = Blueprint("query", __name__)

ENDPOINT    = "/query"
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "query_prompt.txt")


def load_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Answer the question using the context below.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{question}"


@query_bp.route("/query", methods=["POST"])
def query():
    """POST /query — Full RAG pipeline with standardised meta."""

    # ── 1. Validate ───────────────────────────────────────────────────────────
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON", "status": 400}), 400

    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Field 'question' is required and cannot be empty", "status": 400}), 400
    if len(question) > 2000:
        return jsonify({"error": "Field 'question' must be under 2000 characters", "status": 400}), 400

    n_results  = min(int(data.get("n_results", 3)), 5)
    skip_cache = data.get("skip_cache", False)

    # ── 2. Check Redis cache ──────────────────────────────────────────────────
    if not skip_cache:
        cached = cache_get(ENDPOINT, question)
        if cached:
            return jsonify(cached), 200

    # ── 3. Retrieve ChromaDB chunks ───────────────────────────────────────────
    chunks = query_similar(question, n_results=n_results)

    if not chunks:
        context_text = "No relevant documents found in the knowledge base."
    else:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "unknown")
            context_parts.append(f"[Source {i} — {source}]\n{chunk['text']}")
        context_text = "\n\n".join(context_parts)

    # ── 4. Build and call Groq ────────────────────────────────────────────────
    prompt_template = load_prompt()
    final_prompt    = prompt_template.replace("{context}", context_text).replace("{question}", question)

    result = call_groq(
        prompt=final_prompt,
        system_prompt="You are a helpful business intelligence assistant. Answer using only the provided context.",
        temperature=0.3
    )

    # ── 5. Handle failure ─────────────────────────────────────────────────────
    if not result:
        fallback = get_fallback_response(ENDPOINT)
        return jsonify({
            "answer"  : fallback["result"],
            "sources" : [],
            "meta"    : build_fallback_meta()
        }), 200

    # ── 6. Build standardised response ───────────────────────────────────────
    # Confidence based on how many chunks were retrieved
    confidence = min(0.95, 0.6 + (len(chunks) * 0.1)) if chunks else 0.5

    sources = [{
        "id"       : c["id"],
        "text"     : c["text"],
        "metadata" : c["metadata"],
        "distance" : c["distance"]
    } for c in chunks]

    response = {
        "answer"  : result["text"],
        "sources" : sources,
        "meta"    : build_meta_from_groq(result, cached=False, confidence=confidence)
    }

    # ── 7. Cache and return ───────────────────────────────────────────────────
    cache_set(ENDPOINT, question, response)
    return jsonify(response), 200