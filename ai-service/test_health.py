"""
test_health.py — Test GET /health endpoint
Tool-75: AI Assistant with RAG | AI Developer 2

Tests:
  1. Health endpoint returns 200
  2. All required fields are present
  3. Component statuses are reported
  4. Uptime is counting correctly
  5. Cache stats are present

Start Flask first : python app.py
Then run          : python test_health.py
"""

import requests
import time

BASE_URL = "http://localhost:5000"

# Required fields in the health response
REQUIRED_FIELDS = [
    "status",
    "model_name",
    "avg_response_time",
    "chroma_doc_count",
    "uptime_seconds",
    "uptime_human",
    "cache_stats",
    "components"
]

REQUIRED_COMPONENTS = ["groq_api", "chromadb", "redis"]
REQUIRED_CACHE_KEYS = ["hits", "misses", "hit_rate"]


def separator(title):
    print(f"\n── {title} {'─' * (46 - len(title))}")


def run_tests():
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | /health Test Suite")
    print("=" * 55)

    passed = 0
    failed = 0

    # ── Test 1: Endpoint returns 200 ──────────────────────────────────────────
    separator("Test 1: GET /health returns 200")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)

        if response.status_code == 200:
            print(f"  ✅ Status code: 200")
            passed += 1
        else:
            print(f"  ❌ Expected 200, got {response.status_code}")
            failed += 1
            return

    except requests.exceptions.ConnectionError:
        print("  ❌ Cannot connect — is Flask running? (python app.py)")
        return

    data = response.json()

    # ── Test 2: All required fields present ───────────────────────────────────
    separator("Test 2: All required fields present")
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if not missing:
        print(f"  ✅ All {len(REQUIRED_FIELDS)} required fields present")
        passed += 1
    else:
        print(f"  ❌ Missing fields: {missing}")
        failed += 1

    # ── Test 3: Component statuses ────────────────────────────────────────────
    separator("Test 3: Component statuses")
    components = data.get("components", {})
    missing_components = [c for c in REQUIRED_COMPONENTS if c not in components]
    if not missing_components:
        print(f"  ✅ All components reported:")
        for k, v in components.items():
            icon = "✅" if v == "ok" else "⚠️ "
            print(f"     {icon} {k}: {v}")
        passed += 1
    else:
        print(f"  ❌ Missing components: {missing_components}")
        failed += 1

    # ── Test 4: Uptime is a positive number ───────────────────────────────────
    separator("Test 4: Uptime tracking")
    uptime_seconds = data.get("uptime_seconds", 0)
    uptime_human   = data.get("uptime_human", "")

    if uptime_seconds > 0 and uptime_human:
        print(f"  ✅ Uptime: {uptime_human} ({uptime_seconds}s)")
        passed += 1
    else:
        print(f"  ❌ Uptime not tracking correctly: {uptime_seconds}s")
        failed += 1

    # ── Test 5: Cache stats ───────────────────────────────────────────────────
    separator("Test 5: Cache stats structure")
    cache = data.get("cache_stats", {})
    missing_cache = [k for k in REQUIRED_CACHE_KEYS if k not in cache]
    if not missing_cache:
        print(f"  ✅ Cache stats present:")
        print(f"     Hits     : {cache.get('hits')}")
        print(f"     Misses   : {cache.get('misses')}")
        print(f"     Hit Rate : {cache.get('hit_rate')}")
        passed += 1
    else:
        print(f"  ❌ Missing cache keys: {missing_cache}")
        failed += 1

    # ── Test 6: Full response display ─────────────────────────────────────────
    separator("Full /health Response")
    print(f"  status             : {data.get('status')}")
    print(f"  model_name         : {data.get('model_name')}")
    print(f"  avg_response_time  : {data.get('avg_response_time')}ms")
    print(f"  chroma_doc_count   : {data.get('chroma_doc_count')}")
    print(f"  uptime_human       : {data.get('uptime_human')}")

    # ── Test 7: Uptime increases over time ────────────────────────────────────
    separator("Test 6: Uptime increases over time")
    time.sleep(2)
    response2 = requests.get(f"{BASE_URL}/health", timeout=10)
    data2 = response2.json()
    uptime2 = data2.get("uptime_seconds", 0)

    if uptime2 > uptime_seconds:
        print(f"  ✅ Uptime is counting up: {uptime_seconds}s → {uptime2}s")
        passed += 1
    else:
        print(f"  ❌ Uptime not increasing: {uptime_seconds}s → {uptime2}s")
        failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Results: {passed} passed | {failed} failed")
    if failed == 0:
        print("  🎉 /health endpoint fully working!")
    else:
        print("  ⚠️  Review failures above")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()