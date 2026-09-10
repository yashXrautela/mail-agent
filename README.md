# AI Mail Agent

An AI-powered Gmail assistant that uses Google Gemini to summarize emails and generate contextual email responses.

## Features

- Fetch emails from Gmail
- Summarize emails using Google Gemini
- Generate contextual email responses
- Send emails through Gmail
- Google OAuth 2.0 authentication
- Streamlit frontend
- FastAPI backend

## Tech Stack

- Python
- FastAPI
- Streamlit
- Google Gmail API
- Google Gemini API
- Google OAuth 2.0
- Pydantic
- BeautifulSoup4
- Uvicorn

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yashXRautela/mail-agent.git
cd mail-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

Create a `.env` file in the project root with:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql://user:password@host:5432/database
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:8501
SESSION_SECRET=generate-a-long-random-value
OAUTH_ENCRYPTION_KEY=generate-with-fernet
COOKIE_SECURE=false
```

For production, set `FRONTEND_URL` to the deployed Streamlit URL, set
`COOKIE_SECURE=true`, and use a strong random `SESSION_SECRET`. Generate the
encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

`credentials.json` remains server-only and is never sent to Streamlit.

Place your Google OAuth credentials file in the project directory as:

```text
credentials.json
```

> **Important:** Never commit API keys, OAuth credentials, tokens, or other sensitive information to GitHub.

### 5. Run the application

Start the FastAPI backend:

```bash
uvicorn server:app --reload
```

Open another terminal and start the Streamlit frontend:

```bash
streamlit run frontend.py
```

## Google OAuth Setup

This project uses Google OAuth 2.0 to access Gmail.

### Steps

1. Go to the Google Cloud Console.
2. Create a new project.
3. Enable the Gmail API.
4. Configure the OAuth consent screen.
5. Create OAuth client credentials.
6. Download the credentials file.
7. Rename it to `credentials.json` if necessary.
8. Place `credentials.json` in the project directory.
9. Run the application and complete the Google authentication flow.

Google credentials are encrypted with `OAUTH_ENCRYPTION_KEY` and stored per
user in PostgreSQL. No `token.json` file is created.

## How It Works

```text
Gmail
  │
  ▼
Fetch Emails
  │
  ▼
Process Email Content
  │
  ▼
Google Gemini
  │
  ├── Summarize Email
  │
  └── Generate Response
  │
  ▼
Streamlit Interface
  │
  ▼
Send Response Through Gmail
```

## Backend

The backend is built using FastAPI and handles communication between the frontend, Gmail API, and Gemini API.

Start the backend with:

```bash
uvicorn server:app --reload
```

## Frontend

The frontend is built using Streamlit.

Start the frontend with:

```bash
streamlit run frontend.py
```

## Security

Never commit sensitive credentials or secrets to GitHub.

The following files and information should remain private:

- `.env`
- `credentials.json`
- API keys
- OAuth client secrets
- Access tokens

Make sure sensitive files are included in `.gitignore`.

## Multi-user authentication and database

The backend creates these PostgreSQL tables on startup:

- `users`: one row per Google account, with encrypted OAuth credentials.
- `oauth_login_tickets`: short-lived, one-time OAuth handoff tickets.
- `app_sessions`: hashed application session tokens.
- `email_cache`: summarized email data keyed by internal user ID.

The OAuth callback identifies the Google account through Gmail's `me` profile,
upserts that account, and redirects to Streamlit with only a one-time opaque
ticket. Streamlit exchanges it for an application session token. Every Gmail,
cache, compose, and send endpoint requires that token; the server resolves the
token to one internal user ID and loads only that user's encrypted credentials.

No database migration command is required for a new deployment: the tables are
created by the FastAPI lifespan startup. For an existing production database,
back it up, deploy the new code, and restart the service once so the schema is
created. Existing `token.json` credentials cannot be migrated safely as a
shared account; each user must sign in again.

### Local testing

1. Start PostgreSQL and set the variables above (`COOKIE_SECURE=false` locally).
2. Install dependencies with `pip install -r requirements.txt`.
3. Start FastAPI with `uvicorn server:app --reload`.
4. Start Streamlit with `streamlit run frontend.py`.
5. Sign in through the displayed Google button.

### Production deployment on Render

1. Add the PostgreSQL service's `DATABASE_URL` to the backend service.
2. Add `GEMINI_API_KEY`, `GEMINI_MODEL`, `GOOGLE_REDIRECT_URI`,
   `FRONTEND_URL`, `SESSION_SECRET`, `OAUTH_ENCRYPTION_KEY`, and
   `COOKIE_SECURE=true` as Render environment variables.
3. Keep the existing Google OAuth redirect URI unchanged.
4. Deploy/restart the backend, then deploy the Streamlit frontend.
5. Confirm the startup logs show no token file creation and verify OAuth from
   the deployed frontend.

### Two-account isolation test

1. Use a private browser profile for Google account A, sign in, refresh, open
   an email, generate a reply, compose, and send a test message. Record only
   the expected email IDs and recipient; never log tokens.
2. Use a separate private profile for Google account B and repeat the sign-in.
3. Confirm B sees only B's cached inbox and that B's send operation arrives
   from B's Gmail account.
4. Replay A's email ID using B's application session: `/emails/{id}` and
   `/emails/{id}/generate-response` must return 404.
5. Call `/refresh` and `/send_email` with no token or an expired token: both
   must return 401.
6. Log out/revoke A and confirm its session can no longer read, compose, or
   send. Production readiness requires this test to pass with two real Google
   accounts.

## Future Improvements

- Better email categorization
- Automatic priority detection
- Improved response generation
- Email search and filtering
- Conversation history
- Cloud deployment
- More advanced AI-powered email actions

## Author

Yash Rautela

## License

This project is for educational and development purposes.