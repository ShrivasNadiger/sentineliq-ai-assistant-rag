"""
services/groq_client.py — Groq API Client (Day 2 - Production Ready)
Tool-75: AI Assistant with RAG | AI Developer 2

Features:
  - API call with model selection
  - JSON response parsing helper
  - 3-retry with exponential backoff
  - Response time tracking
  - Token usage logging
  - Structured error logging
"""

import os
import time
import json
import logging
from groq import Groq

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("GroqClient")

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME   = "llama-3.3-70b-versatile"
MAX_RETRIES  = 3
RETRY_DELAY  = 2   # seconds — doubles each retry (2s → 4s → 8s)


# ── Response time tracker (stores last 10 response times for /health) ─────────
_response_times: list[float] = []

def _record_response_time(ms: float):
    """Keep a rolling window of the last 10 response times."""
    _response_times.append(ms)
    if len(_response_times) > 10:
        _response_times.pop(0)

def get_avg_response_time() -> float:
    """Return average response time in ms (used by /health endpoint)."""
    if not _response_times:
        return 0.0
    return round(sum(_response_times) / len(_response_times), 2)


# ── Core API Call ─────────────────────────────────────────────────────────────
def call_groq(
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.3,
    max_tokens: int = 1000
) -> dict | None:
    """
    Call the Groq API with retry logic.

    Args:
        prompt        : The user message to send to the AI
        system_prompt : Optional system instruction (sets AI behaviour)
        temperature   : 0.3 = factual/consistent | 0.7 = creative/varied
        max_tokens    : Maximum tokens in the AI response

    Returns:
        dict with keys:
            - text          : The AI response string
            - tokens_used   : Total tokens consumed
            - response_time_ms : How long the call took
            - model_used    : Model name used
        OR None if all retries fail
    """

    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not set in .env — cannot call Groq API")
        return None

    client = Groq(api_key=GROQ_API_KEY)

    # Build messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt}/{MAX_RETRIES} — calling Groq ({MODEL_NAME})")
            start_time = time.time()

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Calculate response time
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            _record_response_time(elapsed_ms)

            # Extract content
            text         = response.choices[0].message.content
            tokens_used  = response.usage.total_tokens if response.usage else 0

            logger.info(f"Success — {tokens_used} tokens used, {elapsed_ms}ms")

            return {
                "text"             : text,
                "tokens_used"      : tokens_used,
                "response_time_ms" : elapsed_ms,
                "model_used"       : MODEL_NAME,
            }

        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * (2 ** (attempt - 1))  # 2s, 4s, 8s
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error("All retries exhausted — returning None")
                return None


# ── JSON Parsing Helper ───────────────────────────────────────────────────────
def call_groq_json(
    prompt: str,
    system_prompt: str = None,
    temperature: float = 0.3
) -> dict | None:
    """
    Call Groq and parse the response as JSON.

    Use this when your prompt asks the AI to return structured JSON.
    Automatically strips markdown fences (```json ... ```) if present.

    Returns:
        Parsed Python dict, or None if parsing fails
    """

    # Tell the AI explicitly to return only JSON
    json_system = (system_prompt or "") + (
        "\nIMPORTANT: Respond ONLY with valid JSON. "
        "No explanation, no markdown fences, no extra text."
    )

    result = call_groq(prompt, system_prompt=json_system, temperature=temperature)

    if not result:
        return None

    raw_text = result["text"].strip()

    # Strip markdown fences if AI wrapped response in ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
        # Attach meta info to parsed result
        parsed["_meta"] = {
            "tokens_used"      : result["tokens_used"],
            "response_time_ms" : result["response_time_ms"],
            "model_used"       : result["model_used"],
        }
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Raw AI response was: {raw_text[:300]}")
        return None


# ── Fallback Template ─────────────────────────────────────────────────────────
def get_fallback_response(endpoint: str) -> dict:
    """
    Return a safe fallback when Groq is unavailable.
    Always include is_fallback: true so frontend can handle it.

    Used by all route handlers when call_groq() returns None.
    """
    return {
        "result"      : f"AI service temporarily unavailable for {endpoint}. Please try again shortly.",
        "is_fallback" : True,
        "model_used"  : MODEL_NAME,
        "tokens_used" : 0,
    }