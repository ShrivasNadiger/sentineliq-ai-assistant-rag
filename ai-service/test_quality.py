"""
test_quality_review.py — Week 2 AI Quality Review
Tool-75: AI Assistant with RAG | AI Developer 2

Day 10 requirement:
  - 10 fresh inputs per endpoint
  - Score accuracy (target average >= 4/5)
  - Auto-scores based on response quality criteria
  - Flags any endpoint scoring below 4/5 for prompt rewriting

Endpoints reviewed:
  - POST /categorise       (10 inputs)
  - POST /generate-report  (10 inputs)
  - POST /query            (10 inputs)

Start Flask first : python app.py
Then run          : python test_quality_review.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# ── 10 Fresh inputs for /categorise ──────────────────────────────────────────
CATEGORISE_INPUTS = [
    {"text": "Unauthorised access attempt detected on admin panel at 3AM.", "expected": "RISK"},
    {"text": "Please review and approve the updated data retention policy by EOD.", "expected": "TASK"},
    {"text": "All API endpoints are returning 503 errors since the last deployment.", "expected": "INCIDENT"},
    {"text": "Our competitor just shut down — this is a major market opportunity.", "expected": "OPPORTUNITY"},
    {"text": "Here is the end of quarter analysis of all support tickets.", "expected": "REPORT"},
    {"text": "SSL certificate expires in 7 days and needs to be renewed immediately.", "expected": "TASK"},
    {"text": "Memory leak discovered in payment module — could cause system crash.", "expected": "RISK"},
    {"text": "New AI integration reduced customer response time by 60 percent.", "expected": "OPPORTUNITY"},
    {"text": "Database replication lag spiked to 45 seconds causing data inconsistency.", "expected": "INCIDENT"},
    {"text": "Monthly summary: 99.8 percent uptime, 12000 tickets resolved, NPS score 72.", "expected": "REPORT"},
]

# ── 10 Fresh inputs for /generate-report ─────────────────────────────────────
REPORT_INPUTS = [
    {
        "data": "5 security incidents this month. 2 resolved, 3 pending. Average resolution time: 4 hours. No data breaches occurred.",
        "hint": "Monthly Security Report"
    },
    {
        "data": "Server uptime: 99.6%. Peak load: 12000 users. Two performance degradations lasted under 10 minutes each.",
        "hint": "Infrastructure Performance Review"
    },
    {
        "data": "New feature launched: AI chat assistant. 3200 users adopted in week 1. 87% positive feedback. 3 bugs reported.",
        "hint": "Feature Launch Summary"
    },
    {
        "data": "Support tickets: 1240 opened, 1180 resolved. Top issues: login errors (34%), slow load times (28%), billing (18%).",
        "hint": "Customer Support Weekly Review"
    },
    {
        "data": "Q2 revenue: $2.4M, up 18% from Q1. New clients: 14. Churn: 3 clients. Pipeline: $8M for Q3.",
        "hint": "Q2 Revenue Report"
    },
    {
        "data": "Compliance audit completed. 2 critical findings fixed. 4 medium findings in progress. Next audit due in 6 months.",
        "hint": "Compliance Audit Results"
    },
    {
        "data": "Team productivity: 94 story points completed vs 80 planned. 2 sprint goals missed. Blockers: API dependency delays.",
        "hint": "Sprint Review Report"
    },
    {
        "data": "Database query optimisation: average query time reduced from 840ms to 120ms. Index added to 3 tables.",
        "hint": "Database Optimisation Summary"
    },
    {
        "data": "User onboarding redesign: completion rate improved from 61% to 84%. Drop-off at step 3 reduced by 70%.",
        "hint": "Onboarding Improvement Report"
    },
    {
        "data": "API rate limit breaches: 234 this week, up from 89 last week. Top offenders: 3 enterprise clients. Action needed.",
        "hint": "API Usage Anomaly Report"
    },
]

# ── Seed documents + 10 questions for /query ─────────────────────────────────
QUERY_SEED_DOCS = [
    {
        "id"  : "qr_001",
        "text": "The system experienced three major outages in Q2. Root causes: misconfigured load balancer, expired SSL cert, and a bad deployment. All were resolved within 4 hours.",
        "meta": {"source": "incident_log"}
    },
    {
        "id"  : "qr_002",
        "text": "Security policy requires all passwords to be at least 12 characters, include a number and special character, and be rotated every 90 days.",
        "meta": {"source": "security_policy"}
    },
    {
        "id"  : "qr_003",
        "text": "The AI assistant uses ChromaDB for vector storage and Groq LLaMA-3.3-70b for generation. Redis caches responses for 15 minutes to reduce API costs.",
        "meta": {"source": "technical_docs"}
    },
    {
        "id"  : "qr_004",
        "text": "Customer satisfaction score dropped from 78 to 71 in March due to login issues. After the fix was deployed, NPS recovered to 79 by April end.",
        "meta": {"source": "customer_report"}
    },
    {
        "id"  : "qr_005",
        "text": "The on-call rotation requires engineers to respond to P1 incidents within 15 minutes and P2 incidents within 1 hour at all times including weekends.",
        "meta": {"source": "ops_runbook"}
    },
]

QUERY_QUESTIONS = [
    "How many outages occurred in Q2 and what caused them?",
    "What are the password requirements for the system?",
    "What technology does the AI assistant use for caching?",
    "How did customer satisfaction change after the login fix?",
    "What is the response time requirement for P1 incidents?",
    "Which vector database is used in the system?",
    "How long does Redis cache responses for?",
    "What was the NPS score before and after the fix?",
    "How quickly must engineers respond to P2 incidents?",
    "What were the root causes of the Q2 outages?",
]


# ── Scoring functions ─────────────────────────────────────────────────────────
def score_categorise(result: dict, expected: str) -> int:
    """Score a /categorise response out of 5."""
    score = 0
    category   = result.get("category", "")
    confidence = result.get("confidence", 0)
    reasoning  = result.get("reasoning", "")
    meta       = result.get("meta", {})

    if category == expected:                        score += 2  # Correct category
    elif category != "GENERAL":                     score += 1  # Wrong but not default
    if confidence >= 0.7:                           score += 1  # High confidence
    if len(reasoning) > 20:                         score += 1  # Has reasoning
    if meta.get("tokens_used", 0) > 0:             score += 1  # Real AI call

    return min(score, 5)


def score_report(result: dict) -> int:
    """Score a /generate-report response out of 5."""
    score = 0
    if len(result.get("title", "")) > 10:                       score += 1
    if len(result.get("executive_summary", "")) > 60:           score += 1
    if len(result.get("top_items", [])) == 3:                   score += 1
    if len(result.get("recommendations", [])) == 3:             score += 1
    if not result.get("meta", {}).get("is_fallback", False):    score += 1
    return score


def score_query(result: dict) -> int:
    """Score a /query response out of 5."""
    score = 0
    answer  = result.get("answer", "")
    sources = result.get("sources", [])
    meta    = result.get("meta", {})

    if len(answer) > 30:                            score += 2  # Has real answer
    if len(sources) > 0:                            score += 1  # Has sources
    if meta.get("tokens_used", 0) > 0:             score += 1  # Real AI call
    if not meta.get("is_fallback", False):          score += 1  # Not fallback

    return min(score, 5)


def separator(title):
    print(f"\n── {title} {'─' * (46 - len(title))}")


# ── Test runners ──────────────────────────────────────────────────────────────
def test_categorise():
    separator("POST /categorise — 10 Inputs")
    scores = []

    for i, item in enumerate(CATEGORISE_INPUTS, 1):
        try:
            r    = requests.post(f"{BASE_URL}/categorise", json={"text": item["text"], "skip_cache": True}, timeout=30)
            data = r.json()
            s    = score_categorise(data, item["expected"])
            scores.append(s)
            icon = "✅" if s >= 4 else "⚠️ "
            print(f"  {icon} [{i:02d}] score={s}/5 | got={data.get('category')} expected={item['expected']} | conf={data.get('confidence')}")
        except Exception as e:
            print(f"  ❌ [{i:02d}] Error: {e}")
            scores.append(0)

    avg = round(sum(scores) / len(scores), 2)
    status = "✅ PASS" if avg >= 4 else "⚠️  NEEDS TUNING"
    print(f"\n  Average: {avg}/5 — {status}")
    return avg


def test_generate_report():
    separator("POST /generate-report — 10 Inputs")
    scores = []

    for i, item in enumerate(REPORT_INPUTS, 1):
        try:
            r    = requests.post(f"{BASE_URL}/generate-report", json={"data": item["data"], "title_hint": item["hint"], "skip_cache": True}, timeout=60)
            data = r.json()
            s    = score_report(data)
            scores.append(s)
            icon = "✅" if s >= 4 else "⚠️ "
            print(f"  {icon} [{i:02d}] score={s}/5 | title='{data.get('title', '')[:45]}'")
        except Exception as e:
            print(f"  ❌ [{i:02d}] Error: {e}")
            scores.append(0)

    avg = round(sum(scores) / len(scores), 2)
    status = "✅ PASS" if avg >= 4 else "⚠️  NEEDS TUNING"
    print(f"\n  Average: {avg}/5 — {status}")
    return avg


def test_query():
    separator("POST /query — 10 Questions")

    # Seed ChromaDB first
    try:
        from services.chroma_client import add_documents, delete_document
        add_documents(
            documents=[d["text"] for d in QUERY_SEED_DOCS],
            ids=[d["id"] for d in QUERY_SEED_DOCS],
            metadatas=[d["meta"] for d in QUERY_SEED_DOCS]
        )
        print(f"  Seeded {len(QUERY_SEED_DOCS)} documents into ChromaDB")
    except Exception as e:
        print(f"  ⚠️  Could not seed ChromaDB: {e}")

    scores = []
    for i, question in enumerate(QUERY_QUESTIONS, 1):
        try:
            r    = requests.post(f"{BASE_URL}/query", json={"question": question, "skip_cache": True}, timeout=30)
            data = r.json()
            s    = score_query(data)
            scores.append(s)
            icon = "✅" if s >= 4 else "⚠️ "
            print(f"  {icon} [{i:02d}] score={s}/5 | sources={len(data.get('sources', []))} | answer='{data.get('answer','')[:60]}'")
        except Exception as e:
            print(f"  ❌ [{i:02d}] Error: {e}")
            scores.append(0)

    # Cleanup
    try:
        for d in QUERY_SEED_DOCS:
            delete_document(d["id"])
        print(f"  Cleaned up {len(QUERY_SEED_DOCS)} seed documents")
    except Exception:
        pass

    avg = round(sum(scores) / len(scores), 2)
    status = "✅ PASS" if avg >= 4 else "⚠️  NEEDS TUNING"
    print(f"\n  Average: {avg}/5 — {status}")
    return avg


# ── Main ──────────────────────────────────────────────────────────────────────
def run_quality_review():
    print("=" * 58)
    print("  Tool-75 | AI Developer 2 | Week 2 Quality Review")
    print("  Target: Average >= 4/5 per endpoint")
    print("=" * 58)

    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ Flask not running — start with: python app.py")
        return

    avg_cat    = test_categorise()
    avg_report = test_generate_report()
    avg_query  = test_query()

    overall = round((avg_cat + avg_report + avg_query) / 3, 2)

    print("\n" + "=" * 58)
    print(f"  /categorise      : {avg_cat}/5    {'✅' if avg_cat >= 4 else '⚠️  rewrite prompt'}")
    print(f"  /generate-report : {avg_report}/5    {'✅' if avg_report >= 4 else '⚠️  rewrite prompt'}")
    print(f"  /query           : {avg_query}/5    {'✅' if avg_query >= 4 else '⚠️  rewrite prompt'}")
    print(f"  ─────────────────────────────────────")
    print(f"  Overall Average  : {overall}/5")
    if overall >= 4:
        print("  🎉 Week 2 AI quality review PASSED!")
    else:
        print("  ⚠️  Some prompts need tuning — review scores above")
    print("=" * 58)


if __name__ == "__main__":
    run_quality_review()