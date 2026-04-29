"""
routes/generate_report.py — POST /generate-report
Tool-75: AI Assistant with RAG | AI Developer 2

Generates a structured executive report from input data.

Request Body:
    {
        "data": "Text or summary of data to generate report from",
        "title_hint": "Optional hint for the report title"  (optional)
    }

Response:
    {
        "title"             : "Q1 Security Incident Analysis Report",
        "executive_summary" : "Three critical incidents were identified...",
        "overview"          : "During the review period, the system...",
        "top_items"         : [
            "SQL injection vulnerability patched on March 3rd",
            "Server downtime totalled 4.2 hours across 3 incidents",
            "User data remained uncompromised throughout all incidents"
        ],
        "recommendations"   : [
            "Implement automated vulnerability scanning on all endpoints",
            "Review incident response procedures with the engineering team",
            "Escalate repeated login failures to the security operations centre"
        ],
        "meta": {
            "model_used"       : "llama-3.3-70b-versatile",
            "tokens_used"      : 487,
            "response_time_ms" : 1823.4,
            "cached"           : false,
            "is_fallback"      : false
        }
    }
"""

import os
import logging
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq_json, get_fallback_response

logger = logging.getLogger("generate_report")

generate_report_bp = Blueprint("generate_report", __name__)

# ── Load prompt template ──────────────────────────────────────────────────────
PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "generate_report_prompt.txt"
)

def load_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {PROMPT_PATH}")
        return "Generate a structured business report in JSON format."


# ── Fallback report template ──────────────────────────────────────────────────
def get_report_fallback(data_preview: str) -> dict:
    """Return a safe static fallback report when Groq is unavailable."""
    return {
        "title"             : "Report Generation Temporarily Unavailable",
        "executive_summary" : "The AI report generation service is temporarily unavailable. Please try again shortly.",
        "overview"          : "The system attempted to generate a report but the AI service did not respond within the expected time.",
        "top_items"         : [
            "AI service timeout or rate limit reached",
            "Input data was received successfully",
            "Please retry the request in a few moments"
        ],
        "recommendations"   : [
            "Retry the report generation request after 30 seconds",
            "Contact support if the issue persists beyond 5 minutes",
            "Review the input data for any unusually large content"
        ],
        "meta": {
            "model_used"       : "llama-3.3-70b-versatile",
            "tokens_used"      : 0,
            "response_time_ms" : 0,
            "cached"           : False,
            "is_fallback"      : True
        }
    }


# ── Route ─────────────────────────────────────────────────────────────────────
@generate_report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    POST /generate-report
    Generate a structured executive report from input data using Groq.
    """

    # ── 1. Parse and validate request ────────────────────────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error"  : "Request body must be valid JSON",
            "status" : 400
        }), 400

    input_data = data.get("data", "").strip()

    if not input_data:
        return jsonify({
            "error"  : "Field 'data' is required and cannot be empty",
            "status" : 400
        }), 400

    if len(input_data) > 8000:
        return jsonify({
            "error"  : "Field 'data' must be under 8000 characters",
            "status" : 400
        }), 400

    # Optional title hint to guide the AI
    title_hint = data.get("title_hint", "").strip()

    # ── 2. Build prompt ───────────────────────────────────────────────────────
    system_prompt = load_prompt()

    user_prompt = f"Generate a professional report from the following data:\n\n{input_data}"
    if title_hint:
        user_prompt += f"\n\nSuggested report title theme: {title_hint}"

    logger.info(f"Generating report from {len(input_data)} chars of input data...")

    # ── 3. Call Groq ──────────────────────────────────────────────────────────
    result = call_groq_json(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.4   # Slightly creative for report writing
    )

    # ── 4. Handle Groq failure ────────────────────────────────────────────────
    if not result:
        logger.warning("Groq call failed — returning fallback report")
        return jsonify(get_report_fallback(input_data[:100])), 200

    # ── 5. Extract and validate report fields ─────────────────────────────────
    meta = result.pop("_meta", {})

    title             = result.get("title", "Untitled Report")
    executive_summary = result.get("executive_summary", "No summary available.")
    overview          = result.get("overview", "No overview available.")
    top_items         = result.get("top_items", [])
    recommendations   = result.get("recommendations", [])

    # Ensure top_items and recommendations are lists of strings
    if not isinstance(top_items, list):
        top_items = [str(top_items)]
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    # Trim to exactly 3 items each (as per spec)
    top_items       = [str(i) for i in top_items[:3]]
    recommendations = [str(r) for r in recommendations[:3]]

    # Pad with placeholders if AI returned fewer than 3
    while len(top_items) < 3:
        top_items.append("No additional findings identified.")
    while len(recommendations) < 3:
        recommendations.append("Review and monitor the situation.")

    # ── 6. Return structured report ───────────────────────────────────────────
    return jsonify({
        "title"             : title,
        "executive_summary" : executive_summary,
        "overview"          : overview,
        "top_items"         : top_items,
        "recommendations"   : recommendations,
        "meta": {
            "model_used"       : meta.get("model_used", "llama-3.3-70b-versatile"),
            "tokens_used"      : meta.get("tokens_used", 0),
            "response_time_ms" : meta.get("response_time_ms", 0),
            "cached"           : False,
            "is_fallback"      : False
        }
    }), 200