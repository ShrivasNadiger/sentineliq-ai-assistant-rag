"""
test_async_report.py — Test Async /generate-report Job Processing
Tool-75: AI Assistant with RAG | AI Developer 2

Tests:
  1. POST returns job_id instantly (under 500ms)
  2. GET /generate-report/<id> shows PENDING/PROCESSING
  3. Polling until COMPLETED works
  4. Result has all required fields
  5. Invalid job_id returns 404

Start Flask first : python app.py
Then run          : python test_async_report.py
"""

import requests
import time

BASE_URL = "http://localhost:5000"

TEST_DATA = (
    "Q3 performance review: Revenue up 22%. Three system outages occurred. "
    "Support tickets increased by 15%. Two new enterprise clients signed. "
    "Team headcount grew from 18 to 24. Infrastructure costs reduced by 12%."
)


def separator(title):
    print(f"\n── {title} {'─' * (46 - len(title))}")


def run_tests():
    print("=" * 55)
    print("  Tool-75 | AI Dev 2 | Async Job Processing Tests")
    print("=" * 55)

    passed = 0
    failed = 0

    # ── Test 1: POST returns instantly ────────────────────────────────────────
    separator("Test 1: POST returns job_id instantly")
    try:
        start = time.time()
        r     = requests.post(
            f"{BASE_URL}/generate-report",
            json={"data": TEST_DATA, "title_hint": "Q3 Review"},
            timeout=10
        )
        elapsed = round((time.time() - start) * 1000, 2)

        data   = r.json()
        job_id = data.get("job_id")

        print(f"  HTTP status  : {r.status_code} (expect 202)")
        print(f"  Response time: {elapsed}ms (expect < 500ms)")
        print(f"  job_id       : {job_id}")
        print(f"  status       : {data.get('status')}")
        print(f"  poll_url     : {data.get('poll_url')}")

        if r.status_code == 202 and job_id and elapsed < 500:
            print(f"  ✅ Job submitted instantly")
            passed += 1
        else:
            print(f"  ❌ Response too slow or wrong status code")
            failed += 1

    except requests.exceptions.ConnectionError:
        print("  ❌ Flask not running — start with: python app.py")
        return
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # ── Test 2: Immediate poll shows PENDING/PROCESSING ───────────────────────
    separator("Test 2: Immediate poll shows PENDING or PROCESSING")
    try:
        r2   = requests.get(f"{BASE_URL}/generate-report/{job_id}", timeout=10)
        d2   = r2.json()
        stat = d2.get("status")

        print(f"  status : {stat}")

        if stat in ("PENDING", "PROCESSING", "COMPLETED"):
            print(f"  ✅ Valid status returned")
            passed += 1
        else:
            print(f"  ❌ Unexpected status: {stat}")
            failed += 1

    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Test 3: Poll until COMPLETED ──────────────────────────────────────────
    separator("Test 3: Poll until COMPLETED (max 60s)")
    try:
        max_wait   = 60
        poll_every = 3
        elapsed    = 0
        final_data = None

        print(f"  Polling every {poll_every}s...")

        while elapsed < max_wait:
            time.sleep(poll_every)
            elapsed += poll_every

            r3   = requests.get(f"{BASE_URL}/generate-report/{job_id}", timeout=10)
            d3   = r3.json()
            stat = d3.get("status")

            print(f"  [{elapsed:02d}s] status: {stat}")

            if stat == "COMPLETED":
                final_data = d3
                break
            elif stat == "FAILED":
                print(f"  ❌ Job FAILED: {d3.get('error')}")
                failed += 1
                break

        if final_data:
            print(f"  ✅ Job completed in ~{elapsed}s")
            passed += 1
        elif elapsed >= max_wait:
            print(f"  ❌ Job did not complete within {max_wait}s")
            failed += 1

    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1
        final_data = None

    # ── Test 4: Result has all required fields ────────────────────────────────
    separator("Test 4: Result has all required fields")
    try:
        if final_data and final_data.get("result"):
            result   = final_data["result"]
            required = ["title", "executive_summary", "overview", "top_items", "recommendations", "meta"]
            missing  = [f for f in required if f not in result]

            if not missing:
                print(f"  ✅ All required fields present")
                print(f"     title   : {result.get('title')}")
                print(f"     items   : {len(result.get('top_items', []))} top items")
                print(f"     recs    : {len(result.get('recommendations', []))} recommendations")
                passed += 1
            else:
                print(f"  ❌ Missing fields: {missing}")
                failed += 1
        else:
            print(f"  ⚠️  No result to check — job may not have completed")
            failed += 1

    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Test 5: Invalid job_id returns 404 ────────────────────────────────────
    separator("Test 5: Invalid job_id returns 404")
    try:
        r5 = requests.get(f"{BASE_URL}/generate-report/invalid-job-id-999", timeout=10)
        if r5.status_code == 404:
            print(f"  ✅ Correctly returned 404 for invalid job_id")
            passed += 1
        else:
            print(f"  ❌ Expected 404, got {r5.status_code}")
            failed += 1

    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Results: {passed} passed | {failed} failed")
    if failed == 0:
        print("  🎉 Async job processing fully working!")
    else:
        print("  ⚠️  Review failures above")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()