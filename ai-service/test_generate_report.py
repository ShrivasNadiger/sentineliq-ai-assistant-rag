"""
test_generate_report.py — Test POST /generate-report + Prompt Tuning Score Sheet
Tool-75: AI Assistant with RAG | AI Developer 2

Tests:
  1. Generate report from sample business data
  2. Verify all required fields are present
  3. Score prompt quality (target: >= 7/10 per output)

Start Flask first : python app.py
Then run          : python test_generate_report.py
"""

import requests
import json

BASE_URL = "http://localhost:5000"

# ── 10 real test inputs for prompt tuning (Day 6 requirement) ─────────────────
TEST_INPUTS = [
    {
        "label": "Security incident data",
        "data" : "Three security incidents occurred this month. A SQL injection attempt was blocked. "
                 "Two failed login spikes were detected from foreign IPs. One API key was exposed in a public repo and rotated.",
        "hint" : "Monthly Security Incidents"
    },
    {
        "label": "Performance metrics",
        "data" : "Server uptime was 99.2% this month. Average response time was 340ms. "
                 "Peak load hit 8,000 concurrent users on March 15th. Two timeouts occurred during peak hours.",
        "hint" : "System Performance Review"
    },
    {
        "label": "Business growth data",
        "data" : "User registrations grew 23% month-over-month. Revenue increased by 18%. "
                 "Three new enterprise clients onboarded. Churn rate dropped from 5% to 3.2%.",
        "hint" : "Business Growth Summary"
    },
]

# ── Scoring criteria ──────────────────────────────────────────────────────────
SCORE_CRITERIA = [
    "title is relevant and professional (not generic)",
    "executive_summary covers key points in 2-3 sentences",
    "overview gives proper context",
    "top_items are specific findings (not vague)",
    "recommendations start with action verbs",
    "recommendations are actionable (not generic advice)",
    "language is professional and clear",
    "no made-up facts beyond what input provided",
    "JSON structure is complete and correct",
    "overall output is demo-ready quality"
]


def separator(title):
    print(f"\n── {title} {'─' * (46 - len(title))}")


def score_report(report: dict, label: str) -> int:
    """Interactively score a report against 10 criteria."""
    print(f"\n  📋 REPORT OUTPUT:")
    print(f"     Title     : {report.get('title')}")
    print(f"     Summary   : {report.get('executive_summary')}")
    print(f"     Overview  : {report.get('overview')}")
    print(f"     Top Items : {json.dumps(report.get('top_items'), indent=14)}")
    print(f"     Recs      : {json.dumps(report.get('recommendations'), indent=14)}")
    print(f"     Meta      : tokens={report.get('meta', {}).get('tokens_used')} | "
          f"time={report.get('meta', {}).get('response_time_ms')}ms")

    print(f"\n  📊 AUTO-SCORING against 10 criteria:")
    score = 0

    # Auto-score based on structural checks
    checks = [
        (bool(report.get("title")) and len(report.get("title", "")) > 5,
         "title is relevant and professional"),
        (bool(report.get("executive_summary")) and len(report.get("executive_summary", "")) > 50,
         "executive_summary covers key points"),
        (bool(report.get("overview")) and len(report.get("overview", "")) > 50,
         "overview gives proper context"),
        (len(report.get("top_items", [])) == 3 and all(len(i) > 10 for i in report.get("top_items", [])),
         "top_items are specific findings"),
        (len(report.get("recommendations", [])) == 3,
         "exactly 3 recommendations present"),
        (all(report.get("recommendations", [""])[i][0].isupper()
             for i in range(len(report.get("recommendations", [])))),
         "recommendations start with capital letter"),
        (all(len(r) > 20 for r in report.get("recommendations", [])),
         "recommendations are detailed enough"),
        (report.get("meta", {}).get("tokens_used", 0) > 0,
         "tokens were consumed (real AI call)"),
        (not report.get("meta", {}).get("is_fallback", False),
         "not a fallback response"),
        (report.get("meta", {}).get("response_time_ms", 0) > 0,
         "response time was recorded"),
    ]

    for passed, criterion in checks:
        status = "✅" if passed else "❌"
        print(f"     {status} {criterion}")
        if passed:
            score += 1

    print(f"\n  🎯 Score: {score}/10 {'— PASS ✅' if score >= 7 else '— NEEDS TUNING ⚠️'}")
    return score


def run_tests():
    print("=" * 58)
    print("  Tool-75 | AI Dev 2 | /generate-report + Prompt Tuning")
    print("=" * 58)

    total_score = 0
    passed = 0
    failed = 0

    # ── Test: empty input ─────────────────────────────────────────────────────
    separator("Validation: Empty input (expect 400)")
    try:
        r = requests.post(f"{BASE_URL}/generate-report", json={"data": ""}, timeout=30)
        if r.status_code == 400:
            print("  ✅ Correctly returned 400")
            passed += 1
        else:
            print(f"  ❌ Expected 400, got {r.status_code}")
            failed += 1
    except requests.exceptions.ConnectionError:
        print("  ❌ Flask not running — start with: python app.py")
        return

    # ── Test each real input ──────────────────────────────────────────────────
    for test in TEST_INPUTS:
        separator(test["label"])
        try:
            r = requests.post(
                f"{BASE_URL}/generate-report",
                json={"data": test["data"], "title_hint": test["hint"]},
                timeout=60
            )

            if r.status_code != 200:
                print(f"  ❌ HTTP {r.status_code}: {r.text[:100]}")
                failed += 1
                continue

            report = r.json()
            score  = score_report(report, test["label"])
            total_score += score

            if score >= 7:
                passed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    avg_score = round(total_score / len(TEST_INPUTS), 1) if TEST_INPUTS else 0

    print("\n" + "=" * 58)
    print(f"  Results  : {passed} passed | {failed} failed")
    print(f"  Avg Score: {avg_score}/10 (target: >= 7.0)")
    if avg_score >= 7:
        print("  🎉 Prompt quality meets the Day 6 target!")
    else:
        print("  ⚠️  Prompt needs more tuning — review failures above")
    print("=" * 58)


if __name__ == "__main__":
    run_tests()