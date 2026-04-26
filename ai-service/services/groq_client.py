"""
services/groq_client.py — Groq API Client
Tool-75: AI Assistant with RAG | AI Developer 2

Handles all communication with the Groq API.
Features: API call, JSON parsing, 3-retry with exponential backoff, error logging.
"""

import os
import time
import logging
from groq import Groq

# Set up logging so errors are visible in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment (never hardcode this!)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# The AI model we are using (LLaMA 3.3 70b — free on Groq)
MODEL_NAME = "llama-3.3-70b-versatile"

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2  # doubles each retry (exponential backoff)


def call_groq(prompt: str, system_prompt: str = None, temperature: float = 0.3) -> str | None:
    """
    Call the Groq API with retry logic.

    Args:
        prompt        : The user message / input to send to the AI
        system_prompt : Optional instruction that sets AI behaviour
        temperature   : 0.3 = factual/consistent | 0.7 = creative/varied

    Returns:
        The AI response text, or None if all retries fail
    """

    if not GROQ_API_KEY:
        logger.error("[GroqClient] GROQ_API_KEY is not set in .env")
        return None

    # Build the Groq client
    client = Groq(api_key=GROQ_API_KEY)

    # Build the messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Try up to MAX_RETRIES times
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[GroqClient] Attempt {attempt}/{MAX_RETRIES} — calling Groq API...")

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=1000,
            )

            # Extract the text from the response
            result = response.choices[0].message.content
            logger.info(f"[GroqClient] Success on attempt {attempt}")
            return result

        except Exception as e:
            logger.error(f"[GroqClient] Attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))  # 2s, 4s, 8s
                logger.info(f"[GroqClient] Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                logger.error("[GroqClient] All retries exhausted. Returning None.")
                return None