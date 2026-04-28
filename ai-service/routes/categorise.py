"""
routes/categorise.py — POST /categorise
Tool-75: AI Assistant with RAG | AI Developer 2

Classifies any input text into a predefined category.

Request Body:
    {
        "text": "The server has been down for 2 hours and users cannot login."
    }

Response:
    {
        "category"   : "INCIDENT",
        "confidence" : 0.97,
        "reasoning"  : "The input describes an active system outage affecting users.",
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

logger = logging.getLogger("categorise")

categorise_bp = Blueprint("categorise", __name__)

# ── Load prompt template from file ────────────────────────────────────────────
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "categorise_prompt.txt")

def load_prompt() -> str:
    """Load the categorise system prompt from file."""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found at {PROMPT_PATH}")
        return "Classify the input into a category and return JSON."


# ── Valid categories ──────────────────────────────────────────────────────────
VALID_CATEGORIES = {"RISK", "OPPORTUNITY", "INCIDENT", "TASK", "REPORT", "GENERAL"}


# ── Route ─────────────────────────────────────────────────────────────────────
@categorise_bp.route("/categorise", methods=["POST"])
def categorise():
    """
    POST /categorise
    Classify input text into a predefined category.
    """

    # ── 1. Parse and validate request body ───────────────────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error"  : "Request body must be valid JSON",
            "status" : 400
        }), 400

    text = data.get("text", "").strip()

    if not text:
        return jsonify({
            "error"  : "Field 'text' is required and cannot be empty",
            "status" : 400
        }), 400

    if len(text) > 5000:
        return jsonify({
            "error"  : "Field 'text' must be under 5000 characters",
            "status" : 400
        }), 400

    # ── 2. Load prompt and call Groq ──────────────────────────────────────────
    system_prompt = load_prompt()

    logger.info(f"Categorising input ({len(text)} chars)...")

    result = call_groq_json(
        prompt=f"Classify the following input:\n\n{text}",
        system_prompt=system_prompt,
        temperature=0.1   # Low temperature = consistent, factual classification
    )

    # ── 3. Handle Groq failure — return fallback ──────────────────────────────
    if not result:
        logger.warning("Groq call failed — returning fallback response")
        fallback = get_fallback_response("/categorise")
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

    # ── 4. Validate AI returned a known category ──────────────────────────────
    category   = result.get("category", "GENERAL").upper()
    confidence = result.get("confidence", 0.0)
    reasoning  = result.get("reasoning", "No reasoning provided.")
    meta       = result.get("_meta", {})

    # If AI hallucinated an unknown category, default to GENERAL
    if category not in VALID_CATEGORIES:
        logger.warning(f"AI returned unknown category '{category}' — defaulting to GENERAL")
        category   = "GENERAL"
        confidence = 0.5

    # Clamp confidence between 0.0 and 1.0
    confidence = max(0.0, min(1.0, float(confidence)))

    # ── 5. Return structured response ─────────────────────────────────────────
    return jsonify({
        "category"   : category,
        "confidence" : round(confidence, 2),
        "reasoning"  : reasoning,
        "meta": {
            "model_used"       : meta.get("model_used", "llama-3.3-70b-versatile"),
            "tokens_used"      : meta.get("tokens_used", 0),
            "response_time_ms" : meta.get("response_time_ms", 0),
            "cached"           : False
        }
    }), 200