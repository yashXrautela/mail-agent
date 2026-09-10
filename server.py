import hashlib
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import psycopg
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from compose import generate_new_email
from llm import summarize_with_llm
from raw_mail import retrieve_emails
from response import generate_response
from send_email import send_email

# Render supplies environment variables directly.  Loading a local .env as well
# keeps the documented local-development setup working without overriding Render.
load_dotenv()

GOOGLE_CLIENT_SECRETS = "credentials.json"
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
DATABASE_URL = os.getenv("DATABASE_URL")
SESSION_SECRET = os.getenv("SESSION_SECRET")
FERNET_KEY = os.getenv("OAUTH_ENCRYPTION_KEY")
if GOOGLE_REDIRECT_URI and GOOGLE_REDIRECT_URI.startswith("http://localhost"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7
OAUTH_BROWSER_SESSION_TTL_SECONDS = 10 * 60

if not GOOGLE_REDIRECT_URI:
    raise RuntimeError("GOOGLE_REDIRECT_URI is required")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is required")
if not FERNET_KEY:
    raise RuntimeError("OAUTH_ENCRYPTION_KEY is required")

cipher = Fernet(FERNET_KEY.encode())


def db():
    return psycopg.connect(DATABASE_URL)


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def init_database():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                google_account_id TEXT UNIQUE NOT NULL,
                credentials_encrypted TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS oauth_login_tickets (
                ticket_hash TEXT PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TIMESTAMPTZ NOT NULL
            );
            CREATE TABLE IF NOT EXISTS oauth_pending_requests (
                state_hash TEXT PRIMARY KEY,
                code_verifier TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL
            );
            CREATE TABLE IF NOT EXISTS app_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TIMESTAMPTZ NOT NULL
            );
            CREATE TABLE IF NOT EXISTS email_cache (
                user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                emails JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "true").lower() == "true",
    max_age=OAUTH_BROWSER_SESSION_TTL_SECONDS,
)


def encrypted_credentials(credentials: Credentials) -> str:
    return cipher.encrypt(credentials.to_json().encode()).decode()


def load_credentials(user_id: int) -> Credentials:
    with db() as conn:
        row = conn.execute(
            "SELECT credentials_encrypted FROM users WHERE id = %s", (user_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Google account is not connected")

    data = json.loads(cipher.decrypt(row[0].encode()).decode())
    credentials = Credentials.from_authorized_user_info(data, GOOGLE_SCOPES)
    if credentials.expired:
        if not credentials.refresh_token:
            raise HTTPException(status_code=401, detail="Google authorization expired")
        credentials.refresh(GoogleRequest())
        with db() as conn:
            conn.execute(
                "UPDATE users SET credentials_encrypted = %s, updated_at = NOW() WHERE id = %s",
                (encrypted_credentials(credentials), user_id),
            )
    return credentials


def gmail_sender_name(credentials: Credentials) -> str:
    """Return the display name for the signed-in account's default sender."""
    try:
        service = build("gmail", "v1", credentials=credentials)
        senders = service.users().settings().sendAs().list(userId="me").execute()
        identities = senders.get("sendAs", [])
        default_identity = next(
            (identity for identity in identities if identity.get("isDefault")),
            identities[0] if identities else {},
        )
        return (default_identity.get("displayName") or "").strip()
    except Exception:
        return ""


def current_user(request: Request) -> int:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token_hash = hash_token(header[7:].strip())
    with db() as conn:
        row = conn.execute(
            """
            SELECT user_id FROM app_sessions
            WHERE token_hash = %s AND expires_at > NOW()
            """,
            (token_hash,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return row[0]


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute(
            """
            INSERT INTO app_sessions (token_hash, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (hash_token(token), user_id, datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)),
        )
    return token


@app.get("/auth/google")
async def google_login(request: Request):
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    flow.code_verifier = secrets.token_urlsafe(64)
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    with db() as conn:
        conn.execute(
            """
            INSERT INTO oauth_pending_requests (state_hash, code_verifier, expires_at)
            VALUES (%s, %s, NOW() + INTERVAL '10 minutes')
            """,
            (hash_token(state), flow.code_verifier),
        )
    return RedirectResponse(authorization_url)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    state = request.query_params.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="OAuth session is missing or expired")
    with db() as conn:
        pending = conn.execute(
            """
            DELETE FROM oauth_pending_requests
            WHERE state_hash = %s AND expires_at > NOW()
            RETURNING code_verifier
            """,
            (hash_token(state),),
        ).fetchone()
    if not pending:
        raise HTTPException(status_code=400, detail="OAuth session is missing or expired")
    code_verifier = pending[0]

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=GOOGLE_SCOPES,
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI,
        code_verifier=code_verifier,
    )
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    service = build("gmail", "v1", credentials=credentials)
    profile = service.users().getProfile(userId="me").execute()
    google_account_id = profile.get("emailAddress")
    if not google_account_id:
        raise HTTPException(status_code=400, detail="Google account identity unavailable")
    google_account_id = google_account_id.lower()

    with db() as conn:
        existing = conn.execute(
            "SELECT credentials_encrypted FROM users WHERE google_account_id = %s",
            (google_account_id,),
        ).fetchone()
        if not credentials.refresh_token and existing:
            previous = json.loads(cipher.decrypt(existing[0].encode()).decode())
            credentials.refresh_token = previous.get("refresh_token")
        row = conn.execute(
            """
            INSERT INTO users (google_account_id, credentials_encrypted)
            VALUES (%s, %s)
            ON CONFLICT (google_account_id) DO UPDATE SET
                credentials_encrypted = EXCLUDED.credentials_encrypted,
                updated_at = NOW()
            RETURNING id
            """,
            (google_account_id, encrypted_credentials(credentials)),
        ).fetchone()
        ticket = secrets.token_urlsafe(32)
        conn.execute(
            """
            INSERT INTO oauth_login_tickets (ticket_hash, user_id, expires_at)
            VALUES (%s, %s, NOW() + INTERVAL '2 minutes')
            """,
            (hash_token(ticket), row[0]),
        )
    return RedirectResponse(f"{FRONTEND_URL}?oauth_ticket={ticket}")


@app.post("/auth/exchange")
async def exchange_ticket(request: Request):
    payload = await request.json()
    ticket = payload.get("ticket", "")
    if not ticket:
        raise HTTPException(status_code=400, detail="OAuth ticket is required")
    with db() as conn:
        row = conn.execute(
            """
            DELETE FROM oauth_login_tickets
            WHERE ticket_hash = %s AND expires_at > NOW()
            RETURNING user_id
            """,
            (hash_token(ticket),),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired OAuth ticket")
    return {"session_token": create_session(row[0])}


@app.post("/auth/logout")
async def logout(request: Request):
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        with db() as conn:
            conn.execute("DELETE FROM app_sessions WHERE token_hash = %s", (hash_token(header[7:].strip()),))
    return {"status": "logged out"}


@app.post("/refresh")
async def refresh_emails(user_id: int = Depends(current_user)):
    credentials = load_credentials(user_id)
    raw_emails = retrieve_emails(credentials)
    summarized = [
        {
            **email,
            "summary": summarize_with_llm(email.get("body", "")),
        }
        for email in raw_emails
    ]
    with db() as conn:
        conn.execute(
            """
            INSERT INTO email_cache (user_id, emails) VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET emails = EXCLUDED.emails, updated_at = NOW()
            """,
            (user_id, json.dumps(summarized)),
        )
    return {"status": "success", "count": len(summarized)}


def cached_emails(user_id: int):
    with db() as conn:
        row = conn.execute("SELECT emails FROM email_cache WHERE user_id = %s", (user_id,)).fetchone()
    return row[0] if row else []


@app.get("/emails")
def get_emails(user_id: int = Depends(current_user)):
    return cached_emails(user_id)


@app.get("/emails/{email_id}")
def get_email(email_id: str, user_id: int = Depends(current_user)):
    email = next((item for item in cached_emails(user_id) if item["id"] == email_id), None)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


class ResponseRequest(BaseModel):
    user_note: str = ""


@app.post("/emails/{email_id}/generate-response")
def generate_response_endpoint(email_id: str, req: ResponseRequest, user_id: int = Depends(current_user)):
    email = next((item for item in cached_emails(user_id) if item["id"] == email_id), None)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    credentials = load_credentials(user_id)
    sender_name = gmail_sender_name(credentials)
    return {"id": email_id, "response": generate_response(email.get("subject", ""), email.get("body", ""), req.user_note, sender_name)}


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


@app.post("/send_email")
def send_email_endpoint(req: EmailRequest, user_id: int = Depends(current_user)):
    result = send_email(req.to, req.subject, req.body, load_credentials(user_id))
    return {"status": "sent", "message_id": result["id"]}


class ComposeRequest(BaseModel):
    to: str
    idea: str


@app.post("/compose")
def compose_email(req: ComposeRequest, user_id: int = Depends(current_user)):
    credentials = load_credentials(user_id)
    sender_name = gmail_sender_name(credentials)
    return generate_new_email(req.to, req.idea, sender_name)
