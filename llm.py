import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not found in .env")

# Init Gemini client
client = genai.Client(api_key=API_KEY)

def summarize_with_llm(body: str) -> str:
    """Summarize email with Gemini."""
    prompt = (
        "Strictly summarize the email with necessary details only. "
        "No extra text, no elaboration. Keep it concise and actionable.\n\n"
        f"{body}"
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=300,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return (response.text or "").strip()
    except Exception as e:
        return f"[Gemini Error: {e}]"

if __name__ == "__main__":
    # Load from raw_emails.json
    with open("raw_emails.json", "r", encoding="utf-8") as f:
        raw_emails = json.load(f)

    structured_emails = []
    for email in raw_emails:
        summary = summarize_with_llm(email["body"])
        structured_emails.append({
            "id": email["id"],
            "to": email["from"],
            "subject": email["subject"],
            "body": email["body"],
            "summary": summary
        })

    # Save to summarized_emails.json
    with open("summarized_emails.json", "w", encoding="utf-8") as f:
        json.dump(structured_emails, f, indent=2, ensure_ascii=False)

    print(f"✅ Summarized {len(structured_emails)} emails with Gemini and saved to summarized_emails.json")