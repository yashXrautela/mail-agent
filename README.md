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

Create a `.env` file in the project root and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

You will also need Google OAuth credentials to access Gmail.

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

After authentication, a `token.json` file may be generated to store the authentication token.

Keep both `credentials.json` and `token.json` private.

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
- `token.json`
- API keys
- OAuth client secrets
- Access tokens

Make sure sensitive files are included in `.gitignore`.

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