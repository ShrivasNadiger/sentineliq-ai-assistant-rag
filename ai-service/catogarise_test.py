"""
test_categorise.py — Test POST /categorise endpoint
Tool-75: AI Assistant with RAG | AI Developer 2

Start Flask first: python app.py
Then run: python test_categorise.py
"""

import requests
import json

BASE_URL = "http://localhost:5000"

# ── Test cases — each should map to a specific category ──────────────────────
TEST_CASES = [
    {
        "label"    : "INCIDENT test",
        "text"     : "The production server has been down for 2 hours. Users cannot login.",
        "expected" : "INCIDENT"
    },
    {
        "label"    : "RISK test",
        "text"     : "We detected unusual login attempts from multiple foreign IP addresses.",
        "expected" : "RISK"
    },
    {
        "label"    : "OPPORTUNITY test",
        "text"     : "A new market segment has opened up that aligns perfectly with our product.",
        "expected" : "OPPORTUNITY"
    },
    {
        "label"    : "TASK test",
        "text"     : "Please update the API documentation before the end of the week.",
        "expected" : "TASK"
    },
    {
        "label"    : "REPORT test",
        "text"     : "Here is the weekly summary of all system performance metrics.",
        "expected" : "REPORT"
    },
    {
        "label"    : "Empty input (should return 400)",
        "text"     : "",
        "expected" : "400"
    },
]


def run_tests():
    print("=" * 58)
    print("  Tool-75 | AI Developer 2 | /categorise Test Suite")
    print("=" * 58)

    passed = 0
    failed = 0

    for test in TEST_CASES:
        label    = test["label"]
        text     = test["text"]
        expected = test["expected"]

        print(f"\n── {label} {'─' * (40 - len(label))}")

        try:
            response = requests.post(
                f"{BASE_URL}/categorise",
                json={"text": text},
                timeout=30
            )

            # Test for 400 error case
            if expected == "400":
                if response.status_code == 400:
                    print(f"  ✅ Correctly returned 400 for empty input")
                    passed += 1
                else:
                    print(f"  ❌ Expected 400, got {response.status_code}")
                    failed += 1
                continue

            data = response.json()
            print(data)
            category   = data.get("category")
            confidence = data.get("confidence")
            reasoning  = data.get("reasoning")
            meta       = data.get("meta", {})

            print(f"  Category   : {category} (expected: {expected})")
            print(f"  Confidence : {confidence}")
            print(f"  Reasoning  : {reasoning}")
            print(f"  Tokens     : {meta.get('tokens_used')} | Time: {meta.get('response_time_ms')}ms")

            if category == expected:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                print(f"  ⚠️  Category mismatch (AI may still be correct — review manually)")
                failed += 1

        except requests.exceptions.ConnectionError:
            print("  ❌ Cannot connect — is Flask running? (python app.py)")
            failed += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

    print("\n" + "=" * 58)
    print(f"  Results: {passed} passed | {failed} failed")
    print("=" * 58)


if __name__ == "__main__":
    run_tests()