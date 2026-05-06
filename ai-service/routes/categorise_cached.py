"""
routes/categorise.py — POST /categorise (with Redis Cache)
Tool-75: AI Assistant with RAG | AI Developer 2

Classifies any input text into a predefined category.
Responses are cached in Redis for 15 minutes.

Request Body:
    {
        "text"        : "The server has been down for 2 hours.",
        "skip_cache"  : false   (optional — set true to force fresh AI call)
    }

Response:
    {
        "category"   : "INCIDENT",
        "confidence" : 0.97,
        "reasoning"  : "Describes an active system outage affecting users.",
        "meta": {
            "model_used"       : "llama-3.3-70b-versatile",
            "tokens_used"      : 142,
            "response_time_ms" : 823.5,
            "cached"           : false
        }
    }
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq_json, get_fallback_response
from services.redis_cache import cache_get, cache_set

logger = logging.getLogger("categorise")

categorise_bp = Blueprint("categorise", __name__)

ENDPOINT = "/categorise"

# ── Load prompt template ──────────────────────────────────────────────────────
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "categorise_prompt.txt")

def load_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found at {PROMPT_PATH}")
        return "Classify the input into a category and return JSON."

VALID_CATEGORIES = {"RISK", "OPPORTUNITY", "INCIDENT", "TASK", "REPORT", "GENERAL"}


# ── Route ─────────────────────────────────────────────────────────────────────
@categorise_bp.route("/categorise", methods=["POST"])
def categorise():
    """POST /categorise — Classify input text with Redis caching."""

    # ── 1. Validate request ───────────────────────────────────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON", "status": 400}), 400

    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Field 'text' is required and cannot be empty", "status": 400}), 400

    if len(text) > 5000:
        return jsonify({"error": "Field 'text' must be under 5000 characters", "status": 400}), 400

    skip_cache = data.get("skip_cache", False)

    # ── 2. Check Redis cache first ────────────────────────────────────────────
    if not skip_cache:
        cached = cache_get(ENDPOINT, text)
        if cached:
            logger.info("Returning cached categorise response")
            return jsonify(cached), 200

    # ── 3. Call Groq ──────────────────────────────────────────────────────────
    system_prompt = load_prompt()
    result = call_groq_json(
        prompt=f"Classify the following input:\n\n{text}",
        system_prompt=system_prompt,
        temperature=0.1
    )

    # ── 4. Handle Groq failure ────────────────────────────────────────────────
    if not result:
        fallback = get_fallback_response(ENDPOINT)
        return jsonify({
            "category"   : "GENERAL",
            "confidence" : 0.0,
            "reasoning"  : fallback["result"],
            "meta": {
                "model_used"       : fallback["model_used"],
                "tokens_used"      : 0,
                "response_time_ms" : 0,
                "cached"           : False,
                "is_fallback"      : True
            }
        }), 200

    # ── 5. Extract _meta FIRST by popping it out ──────────────────────────────
    # call_groq_json injects _meta into the result dict
    # must pop() it before reading other keys
    meta       = result.pop("_meta", {})
    category   = result.get("category", "GENERAL").upper()
    confidence = float(result.get("confidence", 0.5))
    reasoning  = result.get("reasoning", "")

    # ── 6. Validate category ──────────────────────────────────────────────────
    if category not in VALID_CATEGORIES:
        logger.warning(f"Unknown category '{category}' — defaulting to GENERAL")
        category   = "GENERAL"
        confidence = 0.5

    confidence = max(0.0, min(1.0, confidence))

    if not reasoning:
        reasoning = f"Input classified as {category} based on content analysis."

    # ── 7. Build response ─────────────────────────────────────────────────────
    response = {
        "category"   : category,
        "confidence" : round(confidence, 2),
        "reasoning"  : reasoning,
        "meta": {
            "model_used"       : meta.get("model_used", "llama-3.3-70b-versatile"),
            "tokens_used"      : meta.get("tokens_used", 0),
            "response_time_ms" : meta.get("response_time_ms", 0),
            "cached"           : False
        }
    }

    # ── 8. Store in Redis cache ───────────────────────────────────────────────
    cache_set(ENDPOINT, text, response)

    return jsonify(response), 200