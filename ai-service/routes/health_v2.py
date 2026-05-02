"""
routes/health.py — GET /health (Updated Day 8 — Real Redis Stats)
Tool-75: AI Assistant with RAG | AI Developer 2

Response:
    {
        "status"            : "ok",
        "model_name"        : "llama-3.3-70b-versatile",
        "avg_response_time" : 843.2,
        "chroma_doc_count"  : 47,
        "uptime_seconds"    : 3600,
        "uptime_human"      : "1h 0m 0s",
        "cache_stats": {
            "status"   : "ok",
            "hits"     : 12,
            "misses"   : 34,
            "hit_rate" : "26.1%"
        },
        "components": {
            "groq_api" : "ok",
            "chromadb" : "ok",
            "redis"    : "ok"
        }
    }
"""

import time
import logging
from flask import Blueprint, jsonify
from services.groq_client import get_avg_response_time, MODEL_NAME
from services.chroma_client import get_collection_stats
from services.redis_cache import get_redis_cache_stats, is_redis_available

logger = logging.getLogger("health")

health_bp = Blueprint("health", __name__)

# Service start time — set when module first loads
SERVICE_START_TIME = time.time()


def format_uptime(seconds: float) -> str:
    """Convert seconds into human readable string e.g. '1h 4m 32s'"""
    seconds = int(seconds)
    hours   = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs    = seconds % 60
    return f"{hours}h {minutes}m {secs}s"


@health_bp.route("/health", methods=["GET"])
def health():
    """GET /health — Returns real-time status of all AI service components."""

    # ── Uptime ────────────────────────────────────────────────────────────────
    uptime_seconds = round(time.time() - SERVICE_START_TIME, 1)
    uptime_human   = format_uptime(uptime_seconds)

    # ── Groq API ──────────────────────────────────────────────────────────────
    avg_response_time = get_avg_response_time()
    groq_status       = "ok" if avg_response_time > 0 else "not yet called"

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_stats  = get_collection_stats()
    chroma_status = chroma_stats.get("status", "error")
    chroma_count  = chroma_stats.get("document_count", 0)

    # ── Redis Cache ───────────────────────────────────────────────────────────
    redis_available = is_redis_available()
    redis_status    = "ok" if redis_available else "unavailable"
    cache_stats     = get_redis_cache_stats()

    # ── Overall status ────────────────────────────────────────────────────────
    overall_status = "ok" if chroma_status == "ok" else "degraded"

    return jsonify({
        "status"            : overall_status,
        "model_name"        : MODEL_NAME,
        "avg_response_time" : avg_response_time,
        "chroma_doc_count"  : chroma_count,
        "uptime_seconds"    : uptime_seconds,
        "uptime_human"      : uptime_human,
        "cache_stats"       : cache_stats,
        "components": {
            "groq_api" : groq_status,
            "chromadb" : chroma_status,
            "redis"    : redis_status
        }
    }), 200