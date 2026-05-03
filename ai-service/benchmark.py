"""
benchmark.py — Performance Benchmark Suite
Tool-75: AI Assistant with RAG | AI Developer 2

Day 12 requirement:
  - p50/p95/p99 response times for all endpoints
  - 50 requests each
  - Optimise any endpoint exceeding targets

Performance Targets:
  /health      : p99 < 200ms
  /categorise  : p99 < 3000ms  (cached), p99 < 8000ms (uncached)
  /query       : p99 < 5000ms  (cached), p99 < 10000ms (uncached)
  /generate-report (submit) : p99 < 500ms  (async — returns instantly)

Start Flask first : python app.py
Then run          : python benchmark.py
"""

import requests
import time
import statistics
import json
from services.chroma_client import add_documents, delete_document

BASE_URL = "http://localhost:5000"

# ── Benchmark config ──────────────────────────────────────────────────────────
REQUESTS_PER_ENDPOINT = 50
WARMUP_REQUESTS       = 3   # Discard first N requests (cold start)

# ── Performance targets (p99 in ms) ──────────────────────────────────────────
TARGETS = {
    "/health"           : 200,
    "/categorise"       : 3000,    # cached hits
    "/query"            : 5000,    # cached hits
    "/generate-report"  : 500,     # async submit only
}

# ── Seed data ─────────────────────────────────────────────────────────────────
SEED_DOCS = [
    {"id": "bench_001", "text": "System performance improved after database indexing.", "meta": {"source": "perf_log"}},
    {"id": "bench_002", "text": "Security audit revealed two medium severity findings.", "meta": {"source": "security"}},
    {"id": "bench_003", "text": "User adoption grew 34% following the new UI launch.", "meta": {"source": "analytics"}},
]

CATEGORISE_INPUT = "The production database is experiencing high CPU usage and slow queries."
QUERY_INPUT      = "What performance improvements were made to the system?"
REPORT_INPUT     = "Monthly metrics: 99.7% uptime, 3 incidents, 15% revenue growth, 2 new clients."


# ── Core benchmark function ───────────────────────────────────────────────────
def benchmark_endpoint(name: str, method: str, url: str, payload: dict = None, n: int = REQUESTS_PER_ENDPOINT) -> dict:
    """
    Run N requests against an endpoint and calculate percentile stats.

    Returns dict with p50, p95, p99, min, max, avg, failures
    """
    times    = []
    failures = 0

    print(f"\n  Benchmarking {name} ({n} requests)...")

    # Warmup requests — discarded
    for _ in range(WARMUP_REQUESTS):
        try:
            if method == "GET":
                requests.get(url, timeout=30)
            else:
                requests.post(url, json=payload, timeout=30)
        except Exception:
            pass

    # Actual benchmark
    for i in range(n):
        try:
            start = time.time()
            if method == "GET":
                r = requests.get(url, timeout=30)
            else:
                r = requests.post(url, json=payload, timeout=30)
            elapsed_ms = (time.time() - start) * 1000

            if r.status_code in (200, 202):
                times.append(elapsed_ms)
            else:
                failures += 1

        except Exception as e:
            failures += 1

        # Progress indicator every 10 requests
        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{n}] completed...")

    if not times:
        return {"error": "All requests failed", "failures": failures}

    times.sort()

    def percentile(data, p):
        idx = max(0, int(len(data) * p / 100) - 1)
        return round(data[idx], 2)

    return {
        "count"    : len(times),
        "failures" : failures,
        "min_ms"   : round(min(times), 2),
        "max_ms"   : round(max(times), 2),
        "avg_ms"   : round(statistics.mean(times), 2),
        "p50_ms"   : percentile(times, 50),
        "p95_ms"   : percentile(times, 95),
        "p99_ms"   : percentile(times, 99),
    }


def print_result(name: str, result: dict, target_p99: int):
    """Print benchmark result with pass/fail against target."""
    if "error" in result:
        print(f"  ❌ {name}: {result['error']}")
        return False

    p99    = result["p99_ms"]
    passed = p99 <= target_p99
    icon   = "✅" if passed else "❌"

    print(f"\n  {icon} {name}")
    print(f"     Requests : {result['count']} ok | {result['failures']} failed")
    print(f"     Min      : {result['min_ms']}ms")
    print(f"     Avg      : {result['avg_ms']}ms")
    print(f"     p50      : {result['p50_ms']}ms")
    print(f"     p95      : {result['p95_ms']}ms")
    print(f"     p99      : {result['p99_ms']}ms  (target: < {target_p99}ms)")

    if not passed:
        print(f"     ⚠️  p99 exceeds target by {round(p99 - target_p99, 2)}ms")

    return passed


def run_benchmark():
    print("=" * 58)
    print("  Tool-75 | AI Developer 2 | Performance Benchmark")
    print(f"  {REQUESTS_PER_ENDPOINT} requests per endpoint | Warmup: {WARMUP_REQUESTS}")
    print("=" * 58)

    # Check Flask is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ Flask not running — start with: python app.py")
        return

    # Seed ChromaDB for query benchmark
    try:
        add_documents(
            documents=[d["text"] for d in SEED_DOCS],
            ids=[d["id"] for d in SEED_DOCS],
            metadatas=[d["meta"] for d in SEED_DOCS]
        )
        print("\n  ✅ ChromaDB seeded for query benchmark")
    except Exception as e:
        print(f"\n  ⚠️  ChromaDB seed failed: {e}")

    results  = {}
    all_pass = True

    # ── 1. /health ────────────────────────────────────────────────────────────
    print("\n── Benchmarking GET /health ─────────────────────────")
    results["/health"] = benchmark_endpoint(
        name="/health", method="GET",
        url=f"{BASE_URL}/health"
    )
    if not print_result("/health", results["/health"], TARGETS["/health"]):
        all_pass = False

    # ── 2. /categorise (cached) ───────────────────────────────────────────────
    print("\n── Benchmarking POST /categorise (cached) ───────────")
    # First call to warm cache
    requests.post(f"{BASE_URL}/categorise", json={"text": CATEGORISE_INPUT}, timeout=30)
    results["/categorise"] = benchmark_endpoint(
        name="/categorise", method="POST",
        url=f"{BASE_URL}/categorise",
        payload={"text": CATEGORISE_INPUT, "skip_cache": False}
    )
    if not print_result("/categorise", results["/categorise"], TARGETS["/categorise"]):
        all_pass = False

    # ── 3. /query (cached) ────────────────────────────────────────────────────
    print("\n── Benchmarking POST /query (cached) ────────────────")
    # First call to warm cache
    requests.post(f"{BASE_URL}/query", json={"question": QUERY_INPUT}, timeout=30)
    results["/query"] = benchmark_endpoint(
        name="/query", method="POST",
        url=f"{BASE_URL}/query",
        payload={"question": QUERY_INPUT, "skip_cache": False}
    )
    if not print_result("/query", results["/query"], TARGETS["/query"]):
        all_pass = False

    # ── 4. /generate-report (async submit only) ───────────────────────────────
    print("\n── Benchmarking POST /generate-report (submit) ──────")
    results["/generate-report"] = benchmark_endpoint(
        name="/generate-report", method="POST",
        url=f"{BASE_URL}/generate-report",
        payload={"data": REPORT_INPUT, "title_hint": "Performance Test"}
    )
    if not print_result("/generate-report", results["/generate-report"], TARGETS["/generate-report"]):
        all_pass = False

    # ── Cleanup ───────────────────────────────────────────────────────────────
    try:
        for d in SEED_DOCS:
            delete_document(d["id"])
    except Exception:
        pass

    # ── Final Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    print("  BENCHMARK SUMMARY")
    print("=" * 58)
    for endpoint, result in results.items():
        if "error" not in result:
            target = TARGETS[endpoint]
            p99    = result["p99_ms"]
            icon   = "✅" if p99 <= target else "❌"
            print(f"  {icon} {endpoint:<22} p99={p99}ms  (target<{target}ms)")

    print()
    if all_pass:
        print("  🎉 All endpoints within performance targets!")
    else:
        print("  ⚠️  Some endpoints exceed targets — see optimisation tips below")
        print()
        print("  OPTIMISATION TIPS:")
        print("  - /categorise slow? → Check Redis is running (pip install redis)")
        print("  - /query slow?      → Verify ChromaDB is returning chunks fast")
        print("  - /health slow?     → ChromaDB init taking too long at startup")
        print("  - All slow?         → Run: docker start redis-tool75")
    print("=" * 58)

    # Save results to file for Day 12 documentation
    with open("benchmark_results.json", "w") as f:
        json.dump({
            "targets"    : TARGETS,
            "results"    : results,
            "all_passed" : all_pass
        }, f, indent=2)
    print("\n  📄 Results saved to benchmark_results.json")


if __name__ == "__main__":
    run_benchmark()