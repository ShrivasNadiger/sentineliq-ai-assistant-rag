"""
services/groq_client.py — Groq API Client (Day 13 — Optimised)
Tool-75: AI Assistant with RAG | AI Developer 2

Day 13 additions:
  - Explicit timeout on every Groq call (10s)
  - Startup preload so first request is fast
  - Shorter system prompt injection to reduce tokens
  - Retry only on timeout/rate-limit, not on bad input
"""

import os
import time
import json
import logging
from groq import Groq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("GroqClient")

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME   = "llama-3.3-70b-versatile"
MAX_RETRIES  = 3
RETRY_DELAY  = 2
REQUEST_TIMEOUT = 30  # seconds — prevents hanging requests

# ── Singleton Groq client — pre-initialised at startup ───────────────────────
_groq_client = None

def get_groq_client() -> Groq | None:
    """
    Get (or create) the Groq client singleton.
    Pre-initialised at startup so first request is fast.
    """
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY not set in .env")
            return None
        _groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info(f"Groq client initialised (model: {MODEL_NAME})")
    return _groq_client


def preload():
    """
    Call at app startup to initialise Groq client early.
    Prevents cold-start delay on first real request.
    """
    client = get_groq_client()
    if client:
        logger.info("Groq client preloaded successfully")
    else:
        logger.warning("Groq client preload failed — check GROQ_API_KEY")


# ── Response time tracker ─────────────────────────────────────────────────────
_response_times: list[float] = []

def _record_response_time(ms: float):
    _response_times.append(ms)
    if len(_response_times) > 10:
        _response_times.pop(0)

def get_avg_response_time() -> float:
    if not _response_times:
        return 0.0
    return round(sum(_response_times) / len(_response_times), 2)


# ── Core API Call ─────────────────────────────────────────────────────────────
def call_groq(
    prompt       : str,
    system_prompt: str   = None,
    temperature  : float = 0.3,
    max_tokens   : int   = 1000
) -> dict | None:
    """
    Call Groq API with timeout, retry, and error handling.

    Returns dict with text, tokens_used, response_time_ms, model_used
    or None if all retries fail.
    """
    client = get_groq_client()
    if not client:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Groq call attempt {attempt}/{MAX_RETRIES}")
            start = time.time()

            response = client.chat.completions.create(
                model      = MODEL_NAME,
                messages   = messages,
                temperature= temperature,
                max_tokens = max_tokens,
                timeout    = REQUEST_TIMEOUT,
            )

            elapsed_ms  = round((time.time() - start) * 1000, 2)
            _record_response_time(elapsed_ms)

            text        = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(f"Groq success — {tokens_used} tokens, {elapsed_ms}ms")

            return {
                "text"             : text,
                "tokens_used"      : tokens_used,
                "response_time_ms" : elapsed_ms,
                "model_used"       : MODEL_NAME,
            }

        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Attempt {attempt} failed: {e}")

            # Don't retry on bad input errors — only on timeout/rate limit
            if "invalid" in error_str or "400" in error_str:
                logger.error("Bad input error — not retrying")
                return None

            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * (2 ** (attempt - 1))
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error("All retries exhausted")
                return None


# ── JSON Parsing Helper ───────────────────────────────────────────────────────
def call_groq_json(
    prompt       : str,
    system_prompt: str   = None,
    temperature  : float = 0.3
) -> dict | None:
    """Call Groq and parse response as JSON."""
    json_system = (system_prompt or "") + (
        "\nRESPOND ONLY WITH VALID JSON. No markdown, no explanation."
    )

    result = call_groq(prompt, system_prompt=json_system, temperature=temperature)
    if not result:
        return None

    raw = result["text"].strip()

    # Strip markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        parsed["_meta"] = {
            "tokens_used"      : result["tokens_used"],
            "response_time_ms" : result["response_time_ms"],
            "model_used"       : result["model_used"],
        }
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e} | raw: {raw[:200]}")
        return None


# ── Fallback helper ───────────────────────────────────────────────────────────
def get_fallback_response(endpoint: str) -> dict:
    """Legacy fallback — use fallback_templates.py for new code."""
    return {
        "result"      : f"AI service temporarily unavailable for {endpoint}.",
        "is_fallback" : True,
        "model_used"  : MODEL_NAME,
        "tokens_used" : 0,
    }