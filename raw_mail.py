from llm_input import fetch_emails  # your Gmail fetch function
import json

def retrieve_emails():
    raw_emails = fetch_emails()  # returns list of emails
    structured_emails = []

    for email in raw_emails:
        structured_emails.append({
            "id": email["id"],
            "from": email["from"],
            "subject": email["subject"],
            "body": email["body"]
        })

    with open("raw_emails.json", "w", encoding="utf-8") as f:
        json.dump(structured_emails, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(structured_emails)} raw emails to raw_emails.json")

if __name__ == "__main__":
    retrieve_emails()