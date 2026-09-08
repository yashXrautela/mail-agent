from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText

# Scopes must allow sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def send_email(to_email, subject, body):
    """
    Sends an email via Gmail API.
    - to_email: recipient email address
    - subject: subject of the email
    - body: plain text email body
    """
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Build Gmail API service
    service = build('gmail', 'v1', credentials=creds)

    # Create MIME message
    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = subject

    # Encode message to base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Send email
    send_result = service.users().messages().send(
        userId='me',
        body={'raw': raw_message}
    ).execute()

    print(f"Email sent to {to_email} | Message ID: {send_result['id']}")
    return send_result
