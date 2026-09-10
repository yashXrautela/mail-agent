from dotenv import load_dotenv
import os
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

def generate_new_email(to: str, idea: str, sender_name: str = "") -> dict:
    """
    Generate a new email from a brief idea.
    
    Args:
        to: Recipient's email address
        idea: Brief description of what the email should be about
    
    Returns:
        dict with subject and body
    """
    sender_name = sender_name.strip()
    sender_details = (
        f"The sender's name is {sender_name}. Use it when appropriate."
        if sender_name
        else "Do not assume or invent the sender's name."
    )
    prompt = f"""
You are an AI email assistant. Generate a professional email based on the following idea.
Write both a subject line and the email body.

The email should be sent to: {to}
Email idea/topic: {idea}

{sender_details}

Format your response exactly like this:
SUBJECT: [Your generated subject line]
BODY:
[Your generated email body]
"""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=800,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        
        text = response.text.strip()
        # Parse the response
        parts = text.split("BODY:", 1)
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        
        return {
            "subject": subject,
            "body": body
        }
    except Exception as e:
        return {
            "subject": f"Error: {str(e)}",
            "body": "Failed to generate email content."
        }

if __name__ == "__main__":
    # Example usage
    to = "example@email.com"
    idea = "Schedule a meeting next week to discuss project progress"
    result = generate_new_email(to, idea)
    print("Generated email:\n")
    print(f"Subject: {result['subject']}\n")
    print(f"Body:\n{result['body']}")