"""
test_groq.py — Verify Groq API + Day 2 Features
Tool-75: AI Assistant with RAG | AI Developer 2

Tests:
  1. Basic API call with response time + token tracking
  2. JSON parsing helper
  3. Fallback response

Usage: python test_groq.py
"""

from dotenv import load_dotenv
load_dotenv()

from services.groq_client import call_groq, call_groq_json, get_fallback_response, get_avg_response_time

def test_basic_call():
    print("\n── Test 1: Basic API Call ───────────────────────────────")
    result = call_groq(
        prompt="Say hello and tell me which AI model you are in one sentence.",
        system_prompt="You are a helpful assistant.",
        temperature=0.3
    )
    if result:
        print(f"✅ SUCCESS")
        print(f"   Response    : {result['text']}")
        print(f"   Tokens used : {result['tokens_used']}")
        print(f"   Time        : {result['response_time_ms']}ms")
        print(f"   Model       : {result['model_used']}")
    else:
        print("❌ FAILED — check your GROQ_API_KEY in .env")

def test_json_parsing():
    print("\n── Test 2: JSON Parsing Helper ─────────────────────────")
    result = call_groq_json(
        prompt='Return a JSON object with keys: "status" (value: "ok") and "message" (value: "JSON parsing works").',
        temperature=0.1
    )
    if result:
        print(f"✅ SUCCESS — Parsed JSON:")
        print(f"   status  : {result.get('status')}")
        print(f"   message : {result.get('message')}")
        print(f"   _meta   : {result.get('_meta')}")
    else:
        print("❌ FAILED — JSON parsing broken")

def test_fallback():
    print("\n── Test 3: Fallback Response ───────────────────────────")
    fallback = get_fallback_response("/categorise")
    print(f"✅ Fallback result  : {fallback['result']}")
    print(f"   is_fallback     : {fallback['is_fallback']}")

def test_avg_response_time():
    print("\n── Test 4: Avg Response Time (for /health) ─────────────")
    avg = get_avg_response_time()
    print(f"✅ Avg response time: {avg}ms (across last 10 calls)")

if __name__ == "__main__":
    print("=" * 55)
    print("  Tool-75 | AI Developer 2 | Day 2 Test Suite")
    print("=" * 55)

    test_basic_call()
    test_json_parsing()
    test_fallback()
    test_avg_response_time()

    print("\n" + "=" * 55)
    print("  All tests done!")
    print("=" * 55)