"""
test_query.py — Test POST /query RAG Pipeline
Tool-75: AI Assistant with RAG | AI Developer 2

Tests the full RAG pipeline:
  1. Seeds ChromaDB with sample documents
  2. Sends questions to /query endpoint
  3. Verifies answer + sources are returned
  4. Cleans up test documents

Start Flask first : python app.py
Then run          : python test_query.py
"""

import requests
from dotenv import load_dotenv
load_dotenv()

from services.chroma_client import add_documents, delete_document

BASE_URL = "http://localhost:5000"

# ── Seed documents for testing ────────────────────────────────────────────────
SEED_DOCS = [
    {
        "id"  : "q_test_001",
        "text": "A critical SQL injection vulnerability was discovered in the login form. "
                "The security team has patched it and all users must reset their passwords.",
        "meta": {"source": "security_bulletin"}
    },
    {
        "id"  : "q_test_002",
        "text": "Server response times increased by 300% due to a missing database index. "
                "Adding an index on the user_id column resolved the performance issue.",
        "meta": {"source": "incident_report"}
    },
    {
        "id"  : "q_test_003",
        "text": "The company signed a new partnership with CloudPro Inc, reducing hosting "
                "costs by 40% and improving global latency for all users.",
        "meta": {"source": "business_update"}
    },
]

# ── Test questions ────────────────────────────────────────────────────────────
TEST_QUERIES = [
    {
        "label"   : "Security question",
        "question": "What security issues have been reported and what action is needed?",
    },
    {
        "label"   : "Performance question",
        "question": "Why did the server slow down and how was it fixed?",
    },
    {
        "label"   : "Business question",
        "question": "What partnerships have been made and what are the benefits?",
    },
    {
        "label"   : "Empty question (should return 400)",
        "question": "",
    },
]


def separator(title):
    print(f"\n── {title} {'─' * (46 - len(title))}")


def run_tests():
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | /query RAG Test Suite")
    print("=" * 55)

    passed = 0
    failed = 0

    # ── Seed ChromaDB ─────────────────────────────────────────────────────────
    separator("Seeding ChromaDB with test documents")
    try:
        add_documents(
            documents=[d["text"] for d in SEED_DOCS],
            ids=[d["id"] for d in SEED_DOCS],
            metadatas=[d["meta"] for d in SEED_DOCS]
        )
        print(f"  ✅ Seeded {len(SEED_DOCS)} documents")
    except Exception as e:
        print(f"  ❌ Seeding failed: {e}")
        return

    # ── Run query tests ───────────────────────────────────────────────────────
    for test in TEST_QUERIES:
        separator(test["label"])

        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={"question": test["question"]},
                timeout=30
            )

            # Empty question should return 400
            if not test["question"]:
                if response.status_code == 400:
                    print(f"  ✅ Correctly returned 400 for empty question")
                    passed += 1
                else:
                    print(f"  ❌ Expected 400, got {response.status_code}")
                    failed += 1
                continue

            data = response.json()

            answer  = data.get("answer", "")
            sources = data.get("sources", [])
            meta    = data.get("meta", {})

            print(f"  Answer    : {answer[:120]}...")
            print(f"  Sources   : {len(sources)} chunks retrieved")
            for s in sources:
                print(f"    → [{s['id']}] distance={s['distance']} | {s['metadata']}")
            print(f"  Tokens    : {meta.get('tokens_used')} | Time: {meta.get('response_time_ms')}ms")

            if answer and len(sources) > 0:
                print(f"  ✅ PASSED — answer + sources returned")
                passed += 1
            else:
                print(f"  ❌ FAILED — missing answer or sources")
                failed += 1

        except requests.exceptions.ConnectionError:
            print("  ❌ Cannot connect — is Flask running? (python app.py)")
            failed += 1
            break
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

    # ── Cleanup ───────────────────────────────────────────────────────────────
    separator("Cleanup: Removing test documents")
    for doc in SEED_DOCS:
        delete_document(doc["id"])
    print(f"  ✅ Cleaned up {len(SEED_DOCS)} test documents")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Results: {passed} passed | {failed} failed")
    if failed == 0:
        print("  🎉 Full RAG pipeline working end-to-end!")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()