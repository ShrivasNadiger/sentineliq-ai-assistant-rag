"""
direct_test.py — Direct categorise test bypassing Flask
Tests groq_client + prompt directly without HTTP
"""
from dotenv import load_dotenv
load_dotenv()

import os
from services.groq_client import call_groq_json

# Load prompt
prompt_path = os.path.join("prompts", "categorise_prompts.txt")
with open(prompt_path, "r") as f:
    system_prompt = f.read().strip()

print("=== PROMPT FIRST LINE ===")
print(system_prompt.split("\n")[0])
print()

# Test call
result = call_groq_json(
    prompt="Classify the following input:\n\nThe production server has been down for 2 hours and users cannot login.",
    system_prompt=system_prompt,
    temperature=0.1
)

print("=== RAW RESULT ===")
print(result)
print()

if result:
    meta       = result.pop("_meta", {})
    category   = result.get("category", "GENERAL").upper()
    confidence = result.get("confidence", 0.0)
    reasoning  = result.get("reasoning", "")
    print(f"category   : {category}")
    print(f"confidence : {confidence}")
    print(f"reasoning  : {reasoning}")
    print(f"tokens     : {meta.get('tokens_used')}")
else:
    print("❌ call_groq_json returned None")