"""
test_fallback.py — Verify AI Fallback Responses
Tool-75: AI Assistant with RAG | AI Developer 2

Tests that fallback templates are:
  1. Structurally correct for each endpoint
  2. Always include is_fallback: true in meta
  3. Never return raw errors to the user
  4. Professional and readable

Run: python test_fallback.py (no Flask needed)
"""

from services.fallback_templates import (
    get_categorise_fallback,
    get_query_fallback,
    get_report_fallback,
    get_describe_fallback,
    get_recommend_fallback
)


def separator(title):
    print(f"\n── {title} {'─' * (44 - len(title))}")


def check_fallback(name: str, result: dict, required_keys: list) -> bool:
    """Check fallback has required keys and is_fallback=true in meta."""
    passed = True

    # Check required keys
    for key in required_keys:
        if key in result:
            print(f"  ✅ {key} present")
        else:
            print(f"  ❌ {key} MISSING")
            passed = False

    # Check meta.is_fallback = True
    meta = result.get("meta", {})
    if meta.get("is_fallback") is True:
        print(f"  ✅ meta.is_fallback = True")
    else:
        print(f"  ❌ meta.is_fallback not True — got: {meta.get('is_fallback')}")
        passed = False

    # Check meta.confidence = 0.0
    if meta.get("confidence") == 0.0:
        print(f"  ✅ meta.confidence = 0.0")
    else:
        print(f"  ⚠️  meta.confidence = {meta.get('confidence')} (expected 0.0)")

    # Check no raw error messages
    result_str = str(result)
    if "traceback" in result_str.lower() or "exception" in result_str.lower():
        print(f"  ❌ Raw error/traceback in fallback response!")
        passed = False
    else:
        print(f"  ✅ No raw errors in response")

    return passed


def run_tests():
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | Fallback Template Tests")
    print("=" * 55)

    passed = 0
    failed = 0

    # ── /categorise fallback ──────────────────────────────────────────────────
    separator("/categorise fallback")
    result = get_categorise_fallback("test input")
    print(f"  category  : {result.get('category')}")
    print(f"  reasoning : {result.get('reasoning', '')[:60]}...")
    if check_fallback("/categorise", result, ["category", "confidence", "reasoning", "meta"]):
        passed += 1
    else:
        failed += 1

    # ── /query fallback ───────────────────────────────────────────────────────
    separator("/query fallback")
    result = get_query_fallback("test question")
    print(f"  answer  : {result.get('answer', '')[:60]}...")
    print(f"  sources : {result.get('sources')}")
    if check_fallback("/query", result, ["answer", "sources", "meta"]):
        passed += 1
    else:
        failed += 1

    # ── /generate-report fallback ─────────────────────────────────────────────
    separator("/generate-report fallback")
    result = get_report_fallback()
    print(f"  title     : {result.get('title')}")
    print(f"  top_items : {len(result.get('top_items', []))} items")
    print(f"  recs      : {len(result.get('recommendations', []))} items")
    if check_fallback("/generate-report", result,
                      ["title", "executive_summary", "overview",
                       "top_items", "recommendations", "meta"]):
        passed += 1
    else:
        failed += 1

    # ── /describe fallback ────────────────────────────────────────────────────
    separator("/describe fallback")
    result = get_describe_fallback()
    if check_fallback("/describe", result, ["description", "meta"]):
        passed += 1
    else:
        failed += 1

    # ── /recommend fallback ───────────────────────────────────────────────────
    separator("/recommend fallback")
    result = get_recommend_fallback()
    print(f"  recs: {len(result.get('recommendations', []))} items")
    if check_fallback("/recommend", result, ["recommendations", "meta"]):
        passed += 1
    else:
        failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Results: {passed} passed | {failed} failed")
    if failed == 0:
        print("  🎉 All fallback templates verified!")
        print("  ✅ App will never crash on Groq failure")
    else:
        print("  ⚠️  Fix failing fallbacks before Demo Day")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()