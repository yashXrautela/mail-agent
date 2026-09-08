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

def generate_response(subject: str, body: str, user_note: str = "") -> str:
    """
    Generate a polite, professional email reply with optional user instructions.
    
    Args:
        subject: Email subject
        body: Email body
        user_note: Additional instructions from the user
    """
    prompt = f"""
You are an AI email assistant. Write a short, polite, professional reply to the following email.

Use my details if needed:
Name : Yash Rautela

Subject: {subject}
Body:
{body}

Additional Instructions from User:
{user_note if user_note else "No specific instructions provided."}
"""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=400,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return (response.text or "").strip()
    except Exception as e:
        return f"[Gemini Error: {e}]"


if __name__ == "__main__":
    # Example usage
    user_note = input("Anything you'd like to add? ")
    subject = "Project Deadline Extension"
    body = "Hi Yash, can you please submit your assignment by next Monday instead of Friday?"
    reply = generate_response(subject, body, user_note)
    print("📧 Generated reply:\n")
    print(reply)