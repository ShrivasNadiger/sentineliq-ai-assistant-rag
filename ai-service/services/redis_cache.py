"""
services/redis_cache.py — Redis AI Response Cache
Tool-75: AI Assistant with RAG | AI Developer 2

Caches AI responses in Redis to avoid repeated Groq API calls.

Features:
  - SHA256 cache key from endpoint + input text
  - 15 minute TTL (time to live)
  - Hit/miss counter tracking (feeds into /health)
  - skip_cache flag for fresh requests
  - Graceful fallback if Redis is unavailable
"""

import os
import json
import hashlib
import logging
import redis

logger = logging.getLogger("RedisCache")

# ── Config ────────────────────────────────────────────────────────────────────
REDIS_URL   = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL   = 60 * 15   # 15 minutes in seconds
KEY_PREFIX  = "tool75:ai:"

# ── Redis client (singleton) ──────────────────────────────────────────────────
_redis_client = None


def get_redis() -> redis.Redis | None:
    """
    Get (or create) the Redis client.
    Returns None if Redis is unavailable — allows graceful degradation.
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2)
        client.ping()  # Test connection immediately
        _redis_client = client
        logger.info(f"Redis connected at {REDIS_URL}")
        return _redis_client

    except Exception as e:
        logger.warning(f"Redis unavailable: {e} — caching disabled, AI will still work")
        return None


# ── Cache Key Generation ──────────────────────────────────────────────────────
def make_cache_key(endpoint: str, input_text: str) -> str:
    """
    Generate a SHA256 cache key from endpoint name + input text.

    Why SHA256?
      - Consistent fixed-length key regardless of input size
      - Same input always produces same key (deterministic)
      - Different inputs never collide (practically impossible)

    Example:
      endpoint   = "/categorise"
      input_text = "The server is down"
      key        = "tool75:ai:/categorise:a3f8c2..."
    """
    # Normalise input — lowercase and strip whitespace for consistent keys
    normalised = f"{endpoint}:{input_text.lower().strip()}"
    sha256_hash = hashlib.sha256(normalised.encode()).hexdigest()
    return f"{KEY_PREFIX}{endpoint}:{sha256_hash}"


# ── Cache Operations ──────────────────────────────────────────────────────────
def cache_get(endpoint: str, input_text: str) -> dict | None:
    """
    Try to get a cached AI response.

    Args:
        endpoint   : Route name e.g. "/categorise"
        input_text : The input that was sent to the AI

    Returns:
        Cached response dict if found, None if miss or Redis unavailable
    """
    client = get_redis()
    if not client:
        return None

    try:
        key   = make_cache_key(endpoint, input_text)
        value = client.get(key)

        if value:
            logger.info(f"Cache HIT for {endpoint}")
            _increment_counter("hits")
            data = json.loads(value)
            # Mark response as cached so frontend/meta knows
            if isinstance(data, dict) and "meta" in data:
                data["meta"]["cached"] = True
            return data

        logger.info(f"Cache MISS for {endpoint}")
        _increment_counter("misses")
        return None

    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


def cache_set(endpoint: str, input_text: str, response: dict) -> bool:
    """
    Store an AI response in Redis cache.

    Args:
        endpoint   : Route name e.g. "/categorise"
        input_text : The input that was sent to the AI
        response   : The full response dict to cache

    Returns:
        True if cached successfully, False otherwise
    """
    client = get_redis()
    if not client:
        return False

    try:
        key   = make_cache_key(endpoint, input_text)
        value = json.dumps(response)
        client.setex(key, CACHE_TTL, value)
        logger.info(f"Cached response for {endpoint} (TTL: {CACHE_TTL}s)")
        return True

    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


def cache_delete(endpoint: str, input_text: str) -> bool:
    """Delete a specific cached response. Useful for testing."""
    client = get_redis()
    if not client:
        return False

    try:
        key = make_cache_key(endpoint, input_text)
        client.delete(key)
        logger.info(f"Deleted cache key for {endpoint}")
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


# ── Hit/Miss Counters ─────────────────────────────────────────────────────────
def _increment_counter(counter_type: str):
    """Increment hit or miss counter in Redis."""
    client = get_redis()
    if not client:
        return

    try:
        key = f"{KEY_PREFIX}stats:{counter_type}"
        client.incr(key)
    except Exception:
        pass  # Counter failure should never break the main flow


def get_redis_cache_stats() -> dict:
    """
    Get cache hit/miss stats from Redis.
    Called by /health endpoint to show real Redis stats.

    Returns:
        dict with hits, misses, hit_rate, and redis status
    """
    client = get_redis()

    if not client:
        return {
            "status"   : "unavailable",
            "hits"     : 0,
            "misses"   : 0,
            "hit_rate" : "0%"
        }

    try:
        hits   = int(client.get(f"{KEY_PREFIX}stats:hits")   or 0)
        misses = int(client.get(f"{KEY_PREFIX}stats:misses") or 0)
        total  = hits + misses
        rate   = round((hits / total) * 100, 1) if total > 0 else 0.0

        return {
            "status"   : "ok",
            "hits"     : hits,
            "misses"   : misses,
            "hit_rate" : f"{rate}%"
        }

    except Exception as e:
        logger.error(f"Failed to get Redis stats: {e}")
        return {
            "status"   : "error",
            "hits"     : 0,
            "misses"   : 0,
            "hit_rate" : "0%"
        }


def is_redis_available() -> bool:
    """Quick check if Redis is reachable. Used by /health."""
    client = get_redis()
    if not client:
        return False
    try:
        return client.ping()
    except Exception:
        return False