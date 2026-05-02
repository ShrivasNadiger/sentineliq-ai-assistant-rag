"""
services/meta_helper.py — Standardised Meta Object Builder
Tool-75: AI Assistant with RAG | AI Developer 2

Every AI endpoint response must include a consistent meta object.
This helper ensures all endpoints return the same meta structure.

Standard meta format (as per Day 9 spec):
    {
        "confidence"       : 0.95,   (0.0 - 1.0)
        "model_used"       : "llama-3.3-70b-versatile",
        "tokens_used"      : 312,
        "response_time_ms" : 843.2,
        "cached"           : false
    }
"""

from services.groq_client import MODEL_NAME


def build_meta(
    tokens_used      : int   = 0,
    response_time_ms : float = 0.0,
    cached           : bool  = False,
    confidence       : float = None,
    is_fallback      : bool  = False,
    model_used       : str   = None
) -> dict:
    """
    Build a standardised meta object for any AI endpoint response.

    Args:
        tokens_used      : Total tokens consumed by Groq API call
        response_time_ms : Time taken for the AI call in milliseconds
        cached           : Whether this response came from Redis cache
        confidence       : Confidence score 0.0-1.0 (None if not applicable)
        is_fallback      : Whether this is a fallback response
        model_used       : AI model name (defaults to current model)

    Returns:
        Standardised meta dict ready to include in any response
    """

    meta = {
        "model_used"       : model_used or MODEL_NAME,
        "tokens_used"      : tokens_used,
        "response_time_ms" : round(response_time_ms, 2),
        "cached"           : cached,
    }

    # Only include confidence if provided (not all endpoints have it)
    if confidence is not None:
        meta["confidence"] = round(max(0.0, min(1.0, float(confidence))), 2)

    # Only include is_fallback if True (keeps response clean normally)
    if is_fallback:
        meta["is_fallback"] = True

    return meta


def build_meta_from_groq(groq_result: dict, cached: bool = False, confidence: float = None) -> dict:
    """
    Build meta directly from a call_groq() result dict.

    Args:
        groq_result : The dict returned by call_groq() or call_groq_json()
        cached      : Whether response came from cache
        confidence  : Optional confidence score

    Returns:
        Standardised meta dict
    """
    if not groq_result:
        return build_meta(is_fallback=True)

    # Handle _meta key from call_groq_json()
    if "_meta" in groq_result:
        source = groq_result["_meta"]
    else:
        source = groq_result

    return build_meta(
        tokens_used      = source.get("tokens_used", 0),
        response_time_ms = source.get("response_time_ms", 0.0),
        cached           = cached,
        confidence       = confidence,
        model_used       = source.get("model_used", MODEL_NAME)
    )


def build_fallback_meta() -> dict:
    """Build a meta object for fallback responses."""
    return build_meta(is_fallback=True)