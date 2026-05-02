"""
test_meta.py — Verify Standardised Meta on All Endpoints
Tool-75: AI Assistant with RAG | AI Developer 2

Day 9 requirement: Every AI endpoint must return:
    meta: {
        confidence       : 0.0 - 1.0  (where applicable)
        model_used       : string
        tokens_used      : int
        response_time_ms : float
        cached           : bool
    }

Start Flask first : python app.py
Then run          : python test_meta.py
"""

import requests

BASE_URL = "http://localhost:5000"

# Required meta keys for every endpoint
REQUIRED_META_KEYS = ["model_used", "tokens_used", "response_time_ms", "cached"]

# Endpoints to test with their payloads
ENDPOINTS = [
    {
        "name"    : "POST /categorise",
        "method"  : "POST",
        "url"     : f"{BASE_URL}/categorise",
        "payload" : {"text": "The server crashed and no one can login right now."}
    },
    {
        "name"    : "POST /generate-report",
        "method"  : "POST",
        "url"     : f"{BASE_URL}/generate-report",
        "payload" : {
            "data": "System had 3 incidents this week. Response times increased by 40%. "
                    "Two vulnerabilities were patched. User satisfaction dropped by 12%."
        }
    },
    {
        "name"    : "POST /query",
        "method"  : "POST",
        "url"     : f"{BASE_URL}/query",
        "payload" : {"question": "What are the main risks in the system?"}
    },
    {
        "name"    : "GET /health",
        "method"  : "GET",
        "url"     : f"{BASE_URL}/health",
        "payload" : None
    },
]


def separator(title):
    print(f"\n── {title} {'─' * (44 - len(title))}")


def check_meta(meta: dict, endpoint_name: str) -> tuple[int, int]:
    """Check meta object has all required keys with valid values."""
    passed = 0
    failed = 0

    if not meta:
        print(f"  ❌ No meta object in response")
        return 0, 1

    for key in REQUIRED_META_KEYS:
        if key in meta:
            print(f"  ✅ {key}: {meta[key]}")
            passed += 1
        else:
            print(f"  ❌ Missing: {key}")
            failed += 1

    # Check confidence if present
    if "confidence" in meta:
        conf = meta["confidence"]
        if 0.0 <= conf <= 1.0:
            print(f"  ✅ confidence: {conf} (valid range 0.0-1.0)")
            passed += 1
        else:
            print(f"  ❌ confidence: {conf} (out of range!)")
            failed += 1

    # Validate types
    if "cached" in meta and not isinstance(meta["cached"], bool):
        print(f"  ❌ cached must be bool, got {type(meta['cached'])}")
        failed += 1

    if "tokens_used" in meta and not isinstance(meta["tokens_used"], int):
        print(f"  ❌ tokens_used must be int, got {type(meta['tokens_used'])}")
        failed += 1

    return passed, failed


def run_tests():
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | Meta Consistency Tests")
    print("=" * 55)

    total_passed = 0
    total_failed = 0

    for ep in ENDPOINTS:
        separator(ep["name"])

        try:
            if ep["method"] == "POST":
                r = requests.post(ep["url"], json=ep["payload"], timeout=60)
            else:
                r = requests.get(ep["url"], timeout=10)

            if r.status_code != 200:
                print(f"  ❌ HTTP {r.status_code} — endpoint not working")
                total_failed += 1
                continue

            data = r.json()

            # /health has a different structure — check cache_stats instead
            if ep["name"] == "GET /health":
                cache_stats = data.get("cache_stats", {})
                if cache_stats:
                    print(f"  ✅ cache_stats present: {cache_stats}")
                    total_passed += 1
                else:
                    print(f"  ❌ cache_stats missing from /health")
                    total_failed += 1
                continue

            meta = data.get("meta", {})
            p, f = check_meta(meta, ep["name"])
            total_passed += p
            total_failed += f

        except requests.exceptions.ConnectionError:
            print("  ❌ Flask not running — start with: python app.py")
            return
        except Exception as e:
            print(f"  ❌ Error: {e}")
            total_failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Results: {total_passed} passed | {total_failed} failed")
    if total_failed == 0:
        print("  🎉 All endpoints have consistent meta objects!")
    else:
        print("  ⚠️  Some endpoints missing meta fields — review above")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()