"""
final_prompt_qa.py — Final Prompt QA Against 30 Demo Records
Tool-75: AI Assistant with RAG | AI Developer 2

Day 14 requirement:
  Run all prompts against 30 demo inputs
  Verify every output is professional and demo-ready
  Flag any output that would embarrass on Demo Day

Start Flask first : python app.py
Then run          : python final_prompt_qa.py
"""

import requests
import json

BASE_URL = "http://localhost:5000"

# ── 30 Demo-ready test inputs ─────────────────────────────────────────────────
# 10 per endpoint — realistic business scenarios

CATEGORISE_DEMO_INPUTS = [
    {"text": "Critical vulnerability found in payment gateway — immediate patch required.", "expected": "RISK"},
    {"text": "All API endpoints returning 500 errors since 2PM deployment.", "expected": "INCIDENT"},
    {"text": "Please update the user documentation before the client presentation.", "expected": "TASK"},
    {"text": "Partnership proposal from AWS could reduce infrastructure costs by 35%.", "expected": "OPPORTUNITY"},
    {"text": "Weekly system health report: 99.9% uptime, 8,420 requests processed.", "expected": "REPORT"},
    {"text": "Unpatched server detected running outdated SSL certificate version.", "expected": "RISK"},
    {"text": "Mobile app crash rate spiked to 12% after last night's update.", "expected": "INCIDENT"},
    {"text": "Schedule security awareness training for all staff by end of month.", "expected": "TASK"},
    {"text": "New AI feature increased user engagement by 45% in first week.", "expected": "OPPORTUNITY"},
    {"text": "Monthly summary: 14 incidents resolved, average resolution time 2.3 hours.", "expected": "REPORT"},
]

REPORT_DEMO_INPUTS = [
    {"data": "Q1 security summary: 8 incidents, 2 critical, 6 minor. All resolved. Zero data breaches. OWASP scan: clean.", "hint": "Q1 Security Summary"},
    {"data": "System performance: avg response 280ms, 99.8% uptime, peak 9200 users, 3 slowdowns under 5 min each.", "hint": "Performance Report"},
    {"data": "Sales pipeline: 23 new leads, 8 converted, $1.8M new ARR, 3 enterprise deals closing Q2.", "hint": "Sales Pipeline Update"},
    {"data": "User feedback: NPS 76, top complaint login speed, top praise AI assistant, 94% would recommend.", "hint": "User Satisfaction Report"},
    {"data": "Infrastructure costs: $42K/month, down 18% from last quarter after Redis optimisation and CDN setup.", "hint": "Infrastructure Cost Review"},
    {"data": "Sprint 12 completed: 87 story points, 2 bugs fixed, new dashboard launched, 1 feature deferred.", "hint": "Sprint 12 Review"},
    {"data": "Compliance status: GDPR audit passed, 2 minor findings resolved, next audit scheduled September.", "hint": "Compliance Status Report"},
    {"data": "Support metrics: 1,840 tickets, 97% resolved within SLA, top issue password reset (23%), CSAT 4.6/5.", "hint": "Support Metrics Report"},
    {"data": "AI assistant usage: 12,400 queries this month, 89% resolved without human escalation, avg 1.2s response.", "hint": "AI Assistant Usage Report"},
    {"data": "Team capacity: 6 engineers, 82% utilisation, 2 hiring in progress, 1 senior engineer onboarded.", "hint": "Team Capacity Report"},
]

QUERY_DEMO_INPUTS = [
    "What is the incident response time requirement for P1 security issues?",
    "What AI model and technology stack does the system use?",
    "What are the password requirements for system access?",
    "How does Redis caching improve system performance?",
    "What security vulnerabilities have been identified and mitigated?",
    "What were the system incidents in 2026 and how were they resolved?",
    "What are the upcoming business opportunities and roadmap plans?",
    "What is the data retention policy for user information?",
    "What are the system performance benchmarks and targets?",
    "What roles and access levels exist in the system?",
]


def separator(title):
    print(f"\n── {title} {'─' * (44 - len(title))}")


def is_demo_ready(text: str) -> bool:
    """Check if output text is professional and demo-ready."""
    if not text or len(text) < 20:
        return False
    text_lower = text.lower()
    # Reject obviously bad outputs
    bad_phrases = [
        "i cannot", "i don't know", "i'm not sure",
        "as an ai", "i apologize", "temporarily unavailable",
        "error", "exception", "none", "null"
    ]
    return not any(phrase in text_lower for phrase in bad_phrases)


def run_qa():
    print("=" * 58)
    print("  Tool-75 | AI Developer 2 | Final Prompt QA — Day 14")
    print("  Testing 30 demo inputs for Demo Day readiness")
    print("=" * 58)

    # Check Flask
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ Flask not running — start with: python app.py")
        return

    total_pass  = 0
    total_fail  = 0
    demo_issues = []

    # ── /categorise QA ───────────────────────────────────────────────────────
    separator("POST /categorise — 10 demo inputs")
    for i, item in enumerate(CATEGORISE_DEMO_INPUTS, 1):
        try:
            r    = requests.post(f"{BASE_URL}/categorise",
                                 json={"text": item["text"], "skip_cache": True}, timeout=30)
            data = r.json()
            cat  = data.get("category", "")
            conf = data.get("confidence", 0)
            reas = data.get("reasoning", "")
            ok   = cat == item["expected"] and conf >= 0.7 and is_demo_ready(reas)
            icon = "✅" if ok else "⚠️ "
            print(f"  {icon} [{i:02d}] {cat} (expected {item['expected']}) conf={conf}")
            if ok:
                total_pass += 1
            else:
                total_fail += 1
                demo_issues.append(f"/categorise input {i}: got {cat}, expected {item['expected']}")
        except Exception as e:
            print(f"  ❌ [{i:02d}] Error: {e}")
            total_fail += 1

    # ── /generate-report QA ───────────────────────────────────────────────────
    separator("POST /generate-report — 10 demo inputs")
    for i, item in enumerate(REPORT_DEMO_INPUTS, 1):
        try:
            r    = requests.post(f"{BASE_URL}/generate-report",
                                 json={"data": item["data"], "title_hint": item["hint"],
                                       "skip_cache": True}, timeout=60)
            data = r.json()

            # For async — wait for job
            if "job_id" in data:
                import time
                job_id = data["job_id"]
                for _ in range(20):
                    time.sleep(3)
                    r2   = requests.get(f"{BASE_URL}/generate-report/{job_id}", timeout=10)
                    d2   = r2.json()
                    if d2.get("status") == "COMPLETED":
                        data = d2.get("result", {})
                        break
                    elif d2.get("status") == "FAILED":
                        break

            title = data.get("title", "")
            items = data.get("top_items", [])
            recs  = data.get("recommendations", [])
            ok    = (is_demo_ready(title) and len(items) == 3
                     and len(recs) == 3 and not data.get("meta", {}).get("is_fallback"))
            icon  = "✅" if ok else "⚠️ "
            print(f"  {icon} [{i:02d}] '{title[:50]}'")
            if ok:
                total_pass += 1
            else:
                total_fail += 1
                demo_issues.append(f"/generate-report input {i}: title='{title[:40]}'")
        except Exception as e:
            print(f"  ❌ [{i:02d}] Error: {e}")
            total_fail += 1

    # ── /query QA ─────────────────────────────────────────────────────────────
    separator("POST /query — 10 demo questions")
    for i, question in enumerate(QUERY_DEMO_INPUTS, 1):
        try:
            r      = requests.post(f"{BASE_URL}/query",
                                   json={"question": question, "skip_cache": True}, timeout=30)
            data   = r.json()
            answer  = data.get("answer", "")
            sources = data.get("sources", [])
            ok      = is_demo_ready(answer) and len(answer) > 50
            icon    = "✅" if ok else "⚠️ "
            print(f"  {icon} [{i:02d}] sources={len(sources)} | '{answer[:60]}...'")
            if ok:
                total_pass += 1
            else:
                total_fail += 1
                demo_issues.append(f"/query input {i}: answer too short or unprofessional")
        except Exception as e:
            print(f"  ❌ [{i:02d}] Error: {e}")
            total_fail += 1

    # ── Final Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    print(f"  Results : {total_pass}/30 demo-ready | {total_fail} need review")

    if total_fail == 0:
        print("  🎉 All 30 outputs are demo-ready!")
        print("  ✅ Prompts cleared for Demo Day")
    else:
        print(f"\n  ⚠️  Issues to review:")
        for issue in demo_issues:
            print(f"    - {issue}")

    score_pct = round((total_pass / 30) * 100, 1)
    print(f"\n  Demo readiness: {score_pct}%")
    if score_pct >= 80:
        print("  ✅ Above 80% threshold — cleared for Demo Day!")
    else:
        print("  ⚠️  Below 80% — review failing prompts before Demo Day")
    print("=" * 58)


if __name__ == "__main__":
    run_qa()