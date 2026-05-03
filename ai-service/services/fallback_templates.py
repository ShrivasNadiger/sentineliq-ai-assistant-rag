"""
services/fallback_templates.py — AI Fallback Response Templates
Tool-75: AI Assistant with RAG | AI Developer 2

Day 13 requirement:
  On Groq timeout/error, return pre-written template response
  with {is_fallback: true} in meta.

Every endpoint has its own professional fallback so the app
never crashes or returns a raw error to the user.
"""

from services.groq_client import MODEL_NAME


def _fallback_meta() -> dict:
    """Standard meta for all fallback responses."""
    return {
        "model_used"       : MODEL_NAME,
        "tokens_used"      : 0,
        "response_time_ms" : 0,
        "cached"           : False,
        "is_fallback"      : True,
        "confidence"       : 0.0
    }


def get_categorise_fallback(text: str = "") -> dict:
    """
    Fallback for POST /categorise.
    Defaults to GENERAL with low confidence.
    """
    return {
        "category"  : "GENERAL",
        "confidence": 0.0,
        "reasoning" : (
            "The AI classification service is temporarily unavailable. "
            "This item has been placed in the GENERAL category as a default. "
            "Please retry or manually classify this item."
        ),
        "meta": _fallback_meta()
    }


def get_query_fallback(question: str = "") -> dict:
    """
    Fallback for POST /query.
    Returns honest message that AI is unavailable.
    """
    return {
        "answer": (
            "The AI assistant is temporarily unavailable due to a service interruption. "
            "Your question has been received but cannot be answered at this time. "
            "Please try again in a few moments. "
            "If the issue persists, contact your system administrator."
        ),
        "sources": [],
        "meta"   : _fallback_meta()
    }


def get_report_fallback(input_preview: str = "") -> dict:
    """
    Fallback for POST /generate-report.
    Returns a structured but empty report template.
    """
    return {
        "title"             : "Report Generation Temporarily Unavailable",
        "executive_summary" : (
            "The AI report generation service experienced a temporary interruption. "
            "The input data was received successfully but could not be processed at this time."
        ),
        "overview"          : (
            "This is an automated fallback response generated when the AI service "
            "is unavailable due to rate limiting, timeout, or a temporary outage. "
            "No data analysis has been performed. Please retry the request."
        ),
        "top_items"         : [
            "AI service temporarily unavailable — please retry",
            "Input data was received and stored successfully",
            "No findings available until AI service recovers"
        ],
        "recommendations"   : [
            "Retry the report generation request after 30 seconds",
            "Contact support if the issue persists beyond 5 minutes",
            "Check the /health endpoint to verify AI service status"
        ],
        "meta": _fallback_meta()
    }


def get_describe_fallback(text: str = "") -> dict:
    """Fallback for POST /describe (AI Developer 1 endpoint)."""
    return {
        "description"  : "AI description service temporarily unavailable. Please retry.",
        "generated_at" : None,
        "meta"         : _fallback_meta()
    }


def get_recommend_fallback() -> dict:
    """Fallback for POST /recommend (AI Developer 1 endpoint)."""
    return {
        "recommendations": [
            {
                "action_type" : "RETRY",
                "description" : "AI recommendation service temporarily unavailable. Please retry.",
                "priority"    : "HIGH"
            }
        ],
        "meta": _fallback_meta()
    }