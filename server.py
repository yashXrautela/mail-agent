import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from raw_mail import retrieve_emails  # Your Gmail fetcher
from llm import summarize_with_llm    # Your summarizer
from send_email import send_email     # Your sender
from response import generate_response  
from compose import generate_new_email


# In-memory cache and API usage tracking
email_cache = {}
api_usage = {
    "total_calls": 0,
    "summarize_calls": 0,
    "response_calls": 0,
    "last_reset": None
}

def track_api_call(call_type: str):
    """Track an API call"""
    global api_usage
    api_usage["total_calls"] += 1
    if call_type in api_usage:
        api_usage[call_type] += 1

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context: runs once when the app starts, and cleans up on shutdown.
    """
    print("📩 Fetching emails from Gmail...")

    # Step 1: Fetch raw emails
    retrieve_emails()

    # Step 2: Load raw_emails.json
    if not os.path.exists("raw_emails.json"):
        print("⚠️ No raw_emails.json found after fetching. Skipping summarization.")
        yield
        return

    with open("raw_emails.json", "r", encoding="utf-8") as f:
        emails = json.load(f)

    summarized = []

    # Step 3: Summarize each email body
    print("📝 Summarizing emails...")
    for email in emails:
        body = email.get("body", "")
        summary = summarize_with_llm(body)
        summarized.append({
            "id": email.get("id"),
            "from": email.get("from"),
            "subject": email.get("subject"),
            "body": body,
            "summary": summary
        })

    # Step 4: Save to summarized_emails.json
    with open("summarized_emails.json", "w", encoding="utf-8") as f:
        json.dump(summarized, f, indent=4, ensure_ascii=False)

    # Store in memory for faster access
    email_cache["summarized"] = summarized

    print(f"✅ Summarized {len(summarized)} emails and saved to summarized_emails.json")

    yield  # App runs here

    # Cleanup step (when shutting down)
    email_cache.clear()
    print("🧹 Cleared email cache on shutdown")


app = FastAPI(lifespan=lifespan)


@app.post("/refresh")
async def refresh_emails():
    """Force refresh emails from Gmail and resummarize."""
    try:
        print("📩 Fetching new emails from Gmail...")
        retrieve_emails()

        if not os.path.exists("raw_emails.json"):
            raise HTTPException(status_code=500, detail="No emails found after fetching")

        with open("raw_emails.json", "r", encoding="utf-8") as f:
            emails = json.load(f)

        summarized = []
        print("📝 Summarizing new emails...")
        for email in emails:
            body = email.get("body", "")
            summary = summarize_with_llm(body)
            summarized.append({
                "id": email.get("id"),
                "from": email.get("from"),
                "subject": email.get("subject"),
                "body": body,
                "summary": summary
            })

        # Update cache and file
        email_cache["summarized"] = summarized
        with open("summarized_emails.json", "w", encoding="utf-8") as f:
            json.dump(summarized, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Summarized {len(summarized)} emails and saved to summarized_emails.json")
        return {"status": "success", "count": len(summarized)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails")
def get_emails():
    """Returns summarized emails."""
    if "summarized" not in email_cache:
        if not os.path.exists("summarized_emails.json"):
            return {"error": "No summarized emails found."}
        with open("summarized_emails.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return email_cache["summarized"]


@app.get("/emails/{email_id}")
def get_email(email_id: str):
    """Return a single email by ID."""
    emails = email_cache.get("summarized", [])
    for email in emails:
        if email["id"] == email_id:
            return email
    raise HTTPException(status_code=404, detail="Email not found")


class ResponseRequest(BaseModel):
    user_note: str = ""

@app.post("/emails/{email_id}/generate-response")
def generate_response_endpoint(email_id: str, req: ResponseRequest):
    """Generate a reply for a given email using Gemini."""
    emails = email_cache.get("summarized", [])
    for email in emails:
        if email["id"] == email_id:
            subject = email.get("subject", "")
            body = email.get("body", "")
            reply = generate_response(subject, body, req.user_note)  # Include user's instructions
            return {"id": email_id, "response": reply}

    raise HTTPException(status_code=404, detail="Email not found")

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


@app.post("/send_email")
def send_email_endpoint(req: EmailRequest):
    try:
        result = send_email(req.to, req.subject, req.body)
        return {"status": "sent", "message_id": result["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ComposeRequest(BaseModel):
    to: str
    idea: str

@app.post("/compose")
def compose_email(req: ComposeRequest):
    """Generate a new email from a brief idea."""
    try:
        result = generate_new_email(req.to, req.idea)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))