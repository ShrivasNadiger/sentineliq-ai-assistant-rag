"""
test_chroma.py — Verify ChromaDB Setup
Tool-75: AI Assistant with RAG | AI Developer 2

Tests:
  1. ChromaDB client initialises correctly
  2. Documents can be added (embedded + stored)
  3. Query returns semantically correct results
  4. Collection stats work (for /health)
  5. Cleanup — deletes test documents after

Usage: python test_chroma.py
NOTE: Run from inside ai-service/ folder
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.chroma_client import (
    get_collection,
    add_documents,
    query_similar,
    get_collection_stats,
    delete_document
)

# ── Test documents — realistic domain knowledge ───────────────────────────────
TEST_DOCS = [
    {
        "id"  : "test_doc_001",
        "text": "A critical security vulnerability was found in the authentication module. "
                "Users should reset their passwords immediately.",
        "meta": {"source": "security_alert", "severity": "critical"}
    },
    {
        "id"  : "test_doc_002",
        "text": "The system is experiencing high CPU usage due to an unoptimised database query. "
                "The engineering team is investigating the root cause.",
        "meta": {"source": "incident_report", "severity": "high"}
    },
    {
        "id"  : "test_doc_003",
        "text": "A new partnership opportunity has emerged with a leading cloud provider. "
                "This could reduce infrastructure costs by 30 percent.",
        "meta": {"source": "business_update", "type": "opportunity"}
    },
    {
        "id"  : "test_doc_004",
        "text": "The quarterly review shows a 15 percent increase in user engagement. "
                "Mobile usage has grown significantly over the past three months.",
        "meta": {"source": "analytics_report", "period": "Q1"}
    },
    {
        "id"  : "test_doc_005",
        "text": "All team members must complete security awareness training by end of month. "
                "Non-compliance will result in access restrictions.",
        "meta": {"source": "hr_notice", "type": "task"}
    },
]


def separator(title: str):
    print(f"\n── {title} {'─' * (48 - len(title))}")


def run_tests():
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | ChromaDB Test Suite")
    print("=" * 55)

    passed = 0
    failed = 0

    # ── Test 1: Init collection ───────────────────────────────────────────────
    separator("Test 1: Initialise Collection")
    try:
        collection = get_collection()
        print(f"  ✅ Collection ready: '{collection.name}'")
        passed += 1
    except Exception as e:
        print(f"  ❌ Failed to initialise: {e}")
        failed += 1
        print("\nCannot continue without ChromaDB. Exiting.")
        return

    # ── Test 2: Add documents ─────────────────────────────────────────────────
    separator("Test 2: Add Documents (embed + store)")
    try:
        success = add_documents(
            documents=[d["text"] for d in TEST_DOCS],
            ids=[d["id"] for d in TEST_DOCS],
            metadatas=[d["meta"] for d in TEST_DOCS]
        )
        if success:
            print(f"  ✅ Added {len(TEST_DOCS)} documents successfully")
            passed += 1
        else:
            print("  ❌ add_documents returned False")
            failed += 1
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Test 3: Query — security related ─────────────────────────────────────
    separator("Test 3: Query — security vulnerability")
    try:
        results = query_similar("security breach and password reset", n_results=2)
        print(f"  Found {len(results)} results:")
        for r in results:
            print(f"    → [{r['id']}] distance={r['distance']}")
            print(f"       {r['text'][:80]}...")

        # The security doc should be the top result
        if results and results[0]["id"] == "test_doc_001":
            print("  ✅ Correct — security doc ranked #1")
            passed += 1
        else:
            print("  ⚠️  Top result was not the security doc — check embeddings")
            failed += 1
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Test 4: Query — business opportunity ─────────────────────────────────
    separator("Test 4: Query — business opportunity")
    try:
        results = query_similar("cloud partnership cost savings", n_results=2)
        print(f"  Found {len(results)} results:")
        for r in results:
            print(f"    → [{r['id']}] distance={r['distance']}")
            print(f"       {r['text'][:80]}...")

        if results and results[0]["id"] == "test_doc_003":
            print("  ✅ Correct — opportunity doc ranked #1")
            passed += 1
        else:
            print("  ⚠️  Top result was not the opportunity doc — check embeddings")
            failed += 1
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Test 5: Collection stats ──────────────────────────────────────────────
    separator("Test 5: Collection Stats (for /health)")
    try:
        stats = get_collection_stats()
        print(f"  Collection : {stats['collection_name']}")
        print(f"  Doc count  : {stats['document_count']}")
        print(f"  Status     : {stats['status']}")

        if stats["status"] == "ok" and stats["document_count"] >= len(TEST_DOCS):
            print("  ✅ Stats working correctly")
            passed += 1
        else:
            print("  ❌ Stats returned unexpected values")
            failed += 1
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Cleanup — delete test documents ──────────────────────────────────────
    separator("Cleanup: Removing test documents")
    try:
        for doc in TEST_DOCS:
            delete_document(doc["id"])
        print(f"  ✅ Cleaned up {len(TEST_DOCS)} test documents")
    except Exception as e:
        print(f"  ⚠️  Cleanup error (not a test failure): {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Results: {passed} passed | {failed} failed")
    if failed == 0:
        print("  🎉 ChromaDB fully working — RAG pipeline ready!")
    else:
        print("  ⚠️  Review failures above before Day 5 RAG work")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()