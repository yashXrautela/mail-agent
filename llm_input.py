import base64
import re

from bs4 import BeautifulSoup
from googleapiclient.discovery import build


def clean_body(body):
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"[\u200E\u200F\u200B-\u200D\uFEFF]", "", text).strip()
    return re.sub(r"\s+", " ", text).strip()


def fetch_emails(credentials):
    service = build("gmail", "v1", credentials=credentials)
    results = service.users().messages().list(
        userId="me", maxResults=5, q="is:important"
    ).execute()
    emails = []
    for msg in results.get("messages", []):
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        service.users().messages().modify(
            userId="me", id=msg["id"], body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(No Sender)")
        body = ""
        payload = msg_data.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
        elif payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        emails.append({"id": msg["id"], "subject": subject, "from": sender, "body": clean_body(body)})
    return emails
