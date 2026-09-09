from llm_input import fetch_emails


def retrieve_emails(credentials):
    return [
        {
            "id": email["id"],
            "from": email["from"],
            "subject": email["subject"],
            "body": email["body"],
        }
        for email in fetch_emails(credentials)
    ]
