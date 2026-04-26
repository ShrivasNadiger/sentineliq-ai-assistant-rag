"""
test_groq.py — Verify Groq API Connection
Tool-75: AI Assistant with RAG | AI Developer 2

Run this script ONCE to confirm your GROQ_API_KEY works.
Usage: python test_groq.py
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env before importing groq_client

from services.groq_client import call_groq

def test_groq_connection():
    print("=" * 50)
    print("Testing Groq API Connection...")
    print("=" * 50)

    # Simple test prompt
    response = call_groq(
        prompt="Say hello and tell me which AI model you are in one sentence.",
        system_prompt="You are a helpful assistant.",
        temperature=0.3
    )

    if response:
        print("\n✅ SUCCESS — Groq API is working!")
        print(f"\nAI Response:\n{response}")
    else:
        print("\n❌ FAILED — Check your GROQ_API_KEY in .env")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_groq_connection()