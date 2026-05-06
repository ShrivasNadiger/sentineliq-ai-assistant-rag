"""
chroma_seeder.py — Seed ChromaDB with Domain Knowledge Documents
Tool-75: AI Assistant with RAG | AI Developer 2

Day 14 requirement:
  Ingest 10 domain knowledge documents covering key topics
  relevant to this tool — so RAG queries return real answers.

Run once: python chroma_seeder.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.chroma_client import add_documents, get_collection_stats, delete_document

# ── 10 Domain Knowledge Documents ────────────────────────────────────────────
# These cover the key topics the AI assistant will be asked about
KNOWLEDGE_DOCS = [
    {
        "id"  : "kb_001",
        "text": (
            "Security incident response protocol: All P1 security incidents must be "
            "reported to the security team within 15 minutes of detection. The incident "
            "response team should isolate affected systems, preserve logs, and notify "
            "stakeholders. Post-incident reviews are mandatory within 48 hours."
        ),
        "meta": {"source": "security_policy", "category": "RISK", "topic": "incident_response"}
    },
    {
        "id"  : "kb_002",
        "text": (
            "System performance benchmarks: Target API response time is under 500ms for "
            "p95. Database queries should complete within 100ms. The system supports up to "
            "10,000 concurrent users. Redis caching reduces average response time by 85 percent. "
            "ChromaDB vector queries return results in under 50ms."
        ),
        "meta": {"source": "technical_specs", "category": "REPORT", "topic": "performance"}
    },
    {
        "id"  : "kb_003",
        "text": (
            "AI assistant capabilities: The system uses LLaMA-3.3-70b via Groq API for "
            "natural language processing. ChromaDB stores vector embeddings for semantic "
            "search. The RAG pipeline retrieves top-3 relevant chunks before generating "
            "responses. Redis caches AI responses for 15 minutes to reduce API costs."
        ),
        "meta": {"source": "technical_docs", "category": "REPORT", "topic": "ai_system"}
    },
    {
        "id"  : "kb_004",
        "text": (
            "Data retention policy: User data is retained for 7 years as per compliance "
            "requirements. Audit logs are kept for 3 years. Deleted records are soft-deleted "
            "and purged after 90 days. All data is encrypted at rest using AES-256. "
            "Backups are performed daily and stored in geographically separate locations."
        ),
        "meta": {"source": "compliance_policy", "category": "RISK", "topic": "data_policy"}
    },
    {
        "id"  : "kb_005",
        "text": (
            "Authentication and access control: The system uses JWT tokens with 24-hour "
            "expiry. Three role levels exist: ADMIN, MANAGER, and VIEWER. Password policy "
            "requires minimum 12 characters with numbers and special characters. "
            "Multi-factor authentication is mandatory for ADMIN accounts. Failed login "
            "attempts are locked after 5 tries."
        ),
        "meta": {"source": "security_policy", "category": "RISK", "topic": "authentication"}
    },
    {
        "id"  : "kb_006",
        "text": (
            "Business growth metrics Q1 2026: Revenue increased 22 percent year-over-year "
            "to 3.2 million dollars. New enterprise clients: 18. Customer churn rate: 2.8 percent. "
            "Net Promoter Score: 74. Mobile usage grew 41 percent. Feature adoption rate "
            "for AI assistant reached 67 percent within 30 days of launch."
        ),
        "meta": {"source": "quarterly_report", "category": "REPORT", "topic": "business_metrics"}
    },
    {
        "id"  : "kb_007",
        "text": (
            "Infrastructure overview: The system runs on 5 Docker containers managed by "
            "Docker Compose. Services include Spring Boot backend on port 8080, Flask AI "
            "service on port 5000, React frontend on port 80, PostgreSQL 15 database, "
            "and Redis 7 cache. All services communicate over an internal Docker network."
        ),
        "meta": {"source": "technical_docs", "category": "REPORT", "topic": "infrastructure"}
    },
    {
        "id"  : "kb_008",
        "text": (
            "Known vulnerabilities and mitigations: SQL injection is prevented through "
            "parameterised queries and input sanitisation. XSS attacks are mitigated by "
            "output encoding and Content Security Policy headers. Rate limiting blocks "
            "IPs exceeding 30 requests per minute. OWASP ZAP scans are run weekly "
            "with zero critical findings as of last scan."
        ),
        "meta": {"source": "security_report", "category": "RISK", "topic": "vulnerabilities"}
    },
    {
        "id"  : "kb_009",
        "text": (
            "Incident history 2026: January — database connection pool exhaustion caused "
            "15 minutes of downtime, resolved by increasing pool size. February — expired "
            "SSL certificate caused login failures for 8 minutes, resolved by automated "
            "renewal setup. March — Groq API rate limit exceeded during peak load, "
            "resolved by implementing Redis response caching."
        ),
        "meta": {"source": "incident_log", "category": "INCIDENT", "topic": "incident_history"}
    },
    {
        "id"  : "kb_010",
        "text": (
            "Upcoming opportunities and roadmap: Q2 2026 plans include mobile application "
            "launch targeting 50,000 downloads in first month. Partnership with three "
            "enterprise cloud providers under negotiation — estimated 30 percent cost "
            "reduction. AI model upgrade to next generation LLaMA planned for Q3. "
            "International expansion into European market targeted for Q4 2026."
        ),
        "meta": {"source": "roadmap", "category": "OPPORTUNITY", "topic": "roadmap"}
    },
]


def seed_chromadb():
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | ChromaDB Knowledge Seeder")
    print("=" * 55)

    # ── Check existing docs ───────────────────────────────────────────────────
    stats = get_collection_stats()
    print(f"\n  Current collection: {stats['document_count']} documents")

    # ── Remove old kb_ docs if they exist ────────────────────────────────────
    print("\n  Removing old knowledge base documents...")
    for doc in KNOWLEDGE_DOCS:
        try:
            delete_document(doc["id"])
        except Exception:
            pass  # Fine if they don't exist yet

    # ── Add all 10 documents ──────────────────────────────────────────────────
    print(f"  Seeding {len(KNOWLEDGE_DOCS)} domain knowledge documents...")

    success = add_documents(
        documents=[d["text"] for d in KNOWLEDGE_DOCS],
        ids=[d["id"] for d in KNOWLEDGE_DOCS],
        metadatas=[d["meta"] for d in KNOWLEDGE_DOCS]
    )

    if success:
        stats = get_collection_stats()
        print(f"\n  ✅ ChromaDB seeded successfully!")
        print(f"  Total documents now: {stats['document_count']}")
        print(f"\n  Documents added:")
        for doc in KNOWLEDGE_DOCS:
            print(f"    [{doc['id']}] {doc['meta']['topic']} — {doc['text'][:60]}...")
    else:
        print("  ❌ Seeding failed — check ChromaDB setup")

    print("\n" + "=" * 55)


if __name__ == "__main__":
    seed_chromadb()