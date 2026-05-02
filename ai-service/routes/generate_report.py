"""
routes/generate_report.py — POST /generate-report (Day 9 — Standardised Meta)
Tool-75: AI Assistant with RAG | AI Developer 2

Generates a structured executive report with standardised meta object.

Request Body:
    {
        "data"       : "Text or summary of data to generate report from",
        "title_hint" : "Optional hint for the report title",
        "skip_cache" : false   (optional)
    }
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq_json, get_fallback_response
from services.redis_cache import cache_get, cache_set
from services.meta_helper import build_meta_from_groq, build_fallback_meta

logger = logging.getLogger("generate_report")

generate_report_bp = Blueprint("generate_report", __name__)

ENDPOINT    = "/generate-report"
PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "generate_report_prompt.txt"
)


def load_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Generate a structured business report in JSON format."


def fallback_report() -> dict:
    return {
        "title"             : "Report Generation Temporarily Unavailable",
        "executive_summary" : "The AI service is temporarily unavailable. Please try again shortly.",
        "overview"          : "The system attempted to generate a report but the AI service did not respond.",
        "top_items"         : [
            "AI service timeout or rate limit reached",
            "Input data was received successfully",
            "Please retry the request in a few moments"
        ],
        "recommendations"   : [
            "Retry the report generation after 30 seconds",
            "Contact support if the issue persists beyond 5 minutes",
            "Review the input data for any unusually large content"
        ],
        "meta" : build_fallback_meta()
    }


@generate_report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """POST /generate-report — Structured report with standardised meta."""

    # ── 1. Validate ───────────────────────────────────────────────────────────
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON", "status": 400}), 400

    input_data = data.get("data", "").strip()
    if not input_data:
        return jsonify({"error": "Field 'data' is required and cannot be empty", "status": 400}), 400
    if len(input_data) > 8000:
        return jsonify({"error": "Field 'data' must be under 8000 characters", "status": 400}), 400

    title_hint = data.get("title_hint", "").strip()
    skip_cache = data.get("skip_cache", False)

    # ── 2. Check cache ────────────────────────────────────────────────────────
    if not skip_cache:
        cached = cache_get(ENDPOINT, input_data)
        if cached:
            return jsonify(cached), 200

    # ── 3. Call Groq ──────────────────────────────────────────────────────────
    system_prompt = load_prompt()
    user_prompt   = f"Generate a professional report from the following data:\n\n{input_data}"
    if title_hint:
        user_prompt += f"\n\nSuggested report title theme: {title_hint}"

    result = call_groq_json(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.4
    )

    # ── 4. Handle failure ─────────────────────────────────────────────────────
    if not result:
        return jsonify(fallback_report()), 200

    # ── 5. Extract and validate fields ───────────────────────────────────────
    groq_meta       = result.pop("_meta", {})
    title           = result.get("title", "Untitled Report")
    exec_summary    = result.get("executive_summary", "No summary available.")
    overview        = result.get("overview", "No overview available.")
    top_items       = result.get("top_items", [])
    recommendations = result.get("recommendations", [])

    if not isinstance(top_items, list):
        top_items = [str(top_items)]
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    top_items       = [str(i) for i in top_items[:3]]
    recommendations = [str(r) for r in recommendations[:3]]

    while len(top_items) < 3:
        top_items.append("No additional findings identified.")
    while len(recommendations) < 3:
        recommendations.append("Review and monitor the situation.")

    # ── 6. Build standardised response ───────────────────────────────────────
    response = {
        "title"             : title,
        "executive_summary" : exec_summary,
        "overview"          : overview,
        "top_items"         : top_items,
        "recommendations"   : recommendations,
        "meta"              : build_meta_from_groq(groq_meta, cached=False, confidence=0.9)
    }

    # ── 7. Cache and return ───────────────────────────────────────────────────
    cache_set(ENDPOINT, input_data, response)
    return jsonify(response), 200