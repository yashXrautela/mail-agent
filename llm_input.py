import os.path
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from bs4 import BeautifulSoup
import re

def clean_body(body):
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text(separator=' ')
    text = re.sub(r'[\u200E\u200F\u200B-\u200D\uFEFF]', '', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_emails():
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=5, q='is:important').execute()
    messages = results.get('messages', [])
    emails = []
    # ...existing code...
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        # Mark the email as read
        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        headers = msg_data.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
        
        # Extract the full body (plain text)
        body = ''
        payload = msg_data.get('payload', {})
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        # Remove links from the body
        body = clean_body(body)

        emails.append({'id':msg['id'],'subject': subject, 'from': sender, 'body': body})
    return emails

if __name__ == '__main__':
    emails = fetch_emails()
    for email in emails:
        print(f"ID: {email['id']}\nFrom: {email['from']}\nSubject: {email['subject']}\nBody: {email['body']}\n{'-'*40}")