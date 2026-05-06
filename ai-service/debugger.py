# from dotenv import load_dotenv
# load_dotenv()

# from services.groq_client import call_groq_json

# result = call_groq_json(
#     prompt="Classify this: The server is down and users cannot login",
#     system_prompt="Return JSON with key category set to INCIDENT",
#     temperature=0.1
# )

# print("Result:", result)


# from dotenv import load_dotenv
# load_dotenv()
# import requests
# r = requests.post('http://localhost:5000/categorise', json={'text': 'The server is down', 'skip_cache': True}, timeout=30)
# print(r.json())

"""
debugger.py — Test /categorise endpoint via HTTP
Tool-75: AI Assistant with RAG | AI Developer 2

Start Flask first : python app.py
Then run          : python debugger.py
"""

import requests

BASE_URL = "http://localhost:5000"

TEST_INPUTS = [
    "The production server has been down for 2 hours and users cannot login.",
    "Critical vulnerability found in payment gateway — immediate patch required.",
    "Please update the user documentation before the client presentation.",
    "Partnership proposal from AWS could reduce infrastructure costs by 35%.",
    "Weekly system health report: 99.9% uptime, 8420 requests processed.",
]

print("=" * 55)
print("  Categorise Endpoint Debug Test")
print("=" * 55)

for text in TEST_INPUTS:
    r    = requests.post(
        f"{BASE_URL}/categorise",
        json={"text": text, "skip_cache": True},
        timeout=30
    )
    data = r.json()
    print(f"\n  Input      : {text[:60]}...")
    print(f"  Category   : {data.get('category')}")
    print(f"  Confidence : {data.get('confidence')}")
    print(f"  Reasoning  : {data.get('reasoning', '')[:70]}")
    print(f"  Tokens     : {data.get('meta', {}).get('tokens_used')}")
