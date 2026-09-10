
import os

import streamlit as st
import requests
import html
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# ---------- Page setup ----------
st.set_page_config(
    page_title="AI Mail Agent",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def api_headers():
    token = st.session_state.get("session_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def initialize_auth():
    st.session_state.setdefault("session_token", None)
    ticket = st.query_params.get("oauth_ticket")
    if ticket:
        response = requests.post(
            f"{API_BASE}/auth/exchange", json={"ticket": ticket}, timeout=30
        )
        response.raise_for_status()
        st.session_state["session_token"] = response.json()["session_token"]
        for key in ("selected_email", "drafts", "compose_result", "show_compose"):
            st.session_state.pop(key, None)
        st.query_params.clear()


initialize_auth()
if not st.session_state.get("session_token"):
    st.title("AI Mail Agent")
    st.write("Connect your Google account to access your Gmail.")
    st.link_button("Sign in with Google", f"{API_BASE}/auth/google")
    st.stop()

# ---------- Professional UI ----------
st.markdown("""
<style>
/* App background */
.stApp {
    background: #050505;
    color: #f3f4f6;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0b0c0f;
    border-right: 1px solid #1d2025;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

.sidebar-brand {
    font-size: 1.35rem;
    font-weight: 750;
    letter-spacing: -0.02em;
    margin-bottom: 1.5rem;
}

.sidebar-subtitle {
    color: #969ca8;
    font-size: 0.82rem;
    margin-top: -1rem;
    margin-bottom: 1.5rem;
}

/* Hide Streamlit menu/footer and multipage navigation */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebarNav"] {display: none !important;}

/* Main header */
.app-title {
    font-size: 2.15rem;
    font-weight: 780;
    letter-spacing: -0.045em;
    margin-bottom: 0.2rem;
}

.app-subtitle {
    color: #969ca8;
    font-size: 0.95rem;
    margin-bottom: 1.6rem;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.38rem 0.75rem;
    border: 1px solid #26312b;
    border-radius: 999px;
    background: #0b110e;
    color: #a7d8b7;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Email rows */
.email-meta {
    color: #9298a3;
    font-size: 0.78rem;
    margin-bottom: 0.22rem;
}

.email-subject {
    color: #f5f6f8;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin-bottom: 0.4rem;
}

.email-summary {
    color: #b0b5bf;
    font-size: 0.86rem;
    line-height: 1.55;
    margin-bottom: 0.45rem;
}

/* Streamlit bordered containers used as actual email cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0b0c0f;
    border: 1px solid #202329 !important;
    border-radius: 14px !important;
    padding: 0.35rem 0.55rem 0.85rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.15s ease, background 0.15s ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #30343b !important;
    background: #0d0f12;
}

.sender {
    color: #a4aab5;
    font-size: 0.82rem;
    margin-bottom: 0.25rem;
}


.summary-label {
    color: #dfe2e7;
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.25rem;
}

.email-body {
    background: #08090b;
    border: 1px solid #202329;
    border-radius: 11px;
    padding: 1.15rem;
    color: #dfe2e7;
    line-height: 1.65;
    white-space: pre-wrap;
    margin: 0.8rem 0 1rem;
}

.section-label {
    color: #e2e5ea;
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 1rem 0 0.45rem;
}

.ai-box {
    background: #0a0c0f;
    border: 1px solid #252a32;
    border-radius: 12px;
    padding: 1rem;
    margin: 0.6rem 0 1rem;
}

.ai-title {
    color: #e3e7ee;
    font-weight: 700;
    margin-bottom: 0.35rem;
}

.empty-state {
    text-align: center;
    padding: 4rem 1rem;
    border: 1px dashed #2a2d33;
    border-radius: 16px;
    color: #969ca8;
}

/* Inputs */
.stTextArea textarea,
.stTextInput input {
    background: #08090b !important;
    color: #e8eaf0 !important;
    border: 1px solid #25282e !important;
    border-radius: 10px !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #6b7280 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 9px;
    border: 1px solid #292d34;
    background: #101216;
    color: #f3f4f6;
    font-weight: 600;
    min-height: 2.35rem;
}

.stButton > button:hover {
    border-color: #464b54;
    background: #16181c;
    color: #ffffff;
}

/* Primary buttons */
.primary-btn .stButton > button {
    background: #f1f3f5;
    color: #050505;
    border-color: #f3f4f6;
}

.primary-btn .stButton > button:hover {
    background: #ffffff;
}

/* Keep paired action buttons structurally aligned. */
.secondary-btn {
    margin: 0;
    padding: 0;
}

/* Divider */
.soft-divider {
    height: 1px;
    background: #202329;
    margin: 1.3rem 0;
}

/* Metrics */
.metric-card {
    background: #0b0c0f;
    border: 1px solid #202329;
    border-radius: 12px;
    padding: 0.85rem 1rem;
}

.metric-number {
    font-size: 1.25rem;
    font-weight: 750;
}

.metric-label {
    color: #858b96;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)


# ---------- State ----------
def init_state():
    st.session_state.setdefault("page", "Inbox")
    st.session_state.setdefault("selected_email", None)
    st.session_state.setdefault("drafts", {})
    st.session_state.setdefault("compose_result", None)
    st.session_state.setdefault("show_compose", False)


init_state()


def send_compose_callback():
    """Send the compose draft before Streamlit rerenders the page."""
    to = st.session_state.get("compose_to", "").strip()
    subject = st.session_state.get("compose_subject", "")
    body = st.session_state.get("compose_body", "")
    if not to:
        st.session_state["compose_error"] = "Please enter a recipient."
        return
    try:
        send_email(to, subject, body)
        st.session_state["compose_result"] = None
        st.session_state["compose_sent"] = True
        st.session_state.pop("compose_error", None)
    except Exception as e:
        st.session_state["compose_error"] = f"Failed to send email: {e}"

def send_reply_callback(selected_id, to_addr, subject):
    """Send reply before Streamlit rerenders."""
    draft = st.session_state.get(f"draft_editor_{selected_id}", "")
    try:
        send_email(to=to_addr, subject=f"Re: {subject}", body=draft)
        st.session_state["drafts"].pop(selected_id, None)
        st.session_state["reply_sent"] = selected_id
        st.session_state.pop("reply_error", None)
    except Exception as e:
        st.session_state["reply_error"] = f"Failed to send reply: {e}"


# ---------- API helpers ----------
@st.cache_data(ttl=30, show_spinner=False)
def fetch_emails(session_token):
    r = requests.get(
        f"{API_BASE}/emails",
        headers={"Authorization": f"Bearer {session_token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def fetch_email(email_id: str):
    r = requests.get(f"{API_BASE}/emails/{email_id}", headers=api_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def generate_reply(email_id: str, user_note: str):
    payload = {"user_note": user_note}
    r = requests.post(
        f"{API_BASE}/emails/{email_id}/generate-response",
        json=payload,
        headers=api_headers(),
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("response", "")


def send_email(to: str, subject: str, body: str):
    payload = {"to": to, "subject": subject, "body": body}
    r = requests.post(
        f"{API_BASE}/send_email",
        json=payload,
        headers=api_headers(),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def compose_email(to: str, idea: str):
    payload = {"to": to, "idea": idea}
    r = requests.post(
        f"{API_BASE}/compose",
        json=payload,
        headers=api_headers(),
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def refresh_emails():
    r = requests.post(f"{API_BASE}/refresh", headers=api_headers(), timeout=120)
    r.raise_for_status()
    fetch_emails.clear()
    return r.json()


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">✉️ AI Mail Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-subtitle">Your intelligent Gmail workspace</div>',
        unsafe_allow_html=True,
    )

    if st.button("📥  Inbox", use_container_width=True):
        st.session_state["page"] = "Inbox"
        st.session_state["selected_email"] = None
        st.session_state["show_compose"] = False
        st.rerun()

    if st.button("✍️  Compose", use_container_width=True):
        st.session_state["page"] = "Inbox"
        st.session_state["selected_email"] = None
        st.session_state["show_compose"] = True
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄  Refresh Gmail", use_container_width=True):
        try:
            with st.spinner("Fetching and summarizing emails..."):
                result = refresh_emails()
            st.success(f"Updated {result.get('count', 0)} emails.")
            st.rerun()
        except Exception as e:
            st.error(f"Refresh failed: {e}")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="status-pill">● Gmail connected</div>',
        unsafe_allow_html=True,
    )


# ---------- Compose (inline on Inbox) ----------
if st.session_state.get("show_compose"):
    st.markdown('<div class="app-title">Compose</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Draft a new email with the help of AI.</div>',
        unsafe_allow_html=True,
    )

    to = st.text_input(
        "Recipient",
        placeholder="name@example.com",
        key="compose_to",
    )

    idea = st.text_area(
        "What do you want to say?",
        placeholder="Describe what you want the email to communicate...",
        height=160,
        key="compose_idea",
    )

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    generate_clicked = st.button("✦ Generate Email", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if generate_clicked:
        if not to.strip() or not idea.strip():
            st.warning("Please enter both a recipient and an idea.")
        else:
            try:
                with st.spinner("Writing your email..."):
                    result = compose_email(to.strip(), idea.strip())
                st.session_state["compose_result"] = result
                st.success("Email generated.")
            except Exception as e:
                st.error(f"Failed to generate email: {e}")

    if st.session_state.pop("compose_sent", False):
        st.success("Email sent successfully.")

    result = st.session_state.get("compose_result")
    if result:
        st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
        st.markdown("### Review your email")

        subject = st.text_input(
            "Subject",
            value=result.get("subject", ""),
            key="compose_subject",
        )

        body = st.text_area(
            "Message",
            value=result.get("body", ""),
            height=300,
            key="compose_body",
        )

        with st.form(key="compose_action_form", clear_on_submit=False):
            c1, c2 = st.columns([1, 1], vertical_alignment="bottom")
            with c1:
                st.form_submit_button(
                    "📤 Send Email",
                    use_container_width=True,
                    on_click=send_compose_callback,
                )
            with c2:
                clear_clicked = st.form_submit_button(
                    "Clear Draft",
                    use_container_width=True,
                )

        if st.session_state.pop("compose_sent", False):
            st.success("Email sent successfully.")
        compose_error = st.session_state.pop("compose_error", None)
        if compose_error:
            st.error(compose_error)
        if clear_clicked:
            st.session_state["compose_result"] = None
            st.rerun()

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

# ---------- Inbox ----------
else:
    st.markdown('<div class="app-title">Inbox</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">AI-powered summaries and replies for your latest emails.</div>',
        unsafe_allow_html=True,
    )

    try:
        emails = fetch_emails(st.session_state["session_token"])
        emails = emails if isinstance(emails, list) else []
    except Exception as e:
        st.error(f"Failed to load emails: {e}")
        st.stop()

    # Top metrics
    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{len(emails)}</div>'
            '<div class="metric-label">Emails available</div></div>',
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{min(len(emails), 5)}</div>'
            '<div class="metric-label">Showing in inbox</div></div>',
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            '<div class="metric-card"><div class="metric-number">AI</div>'
            '<div class="metric-label">Summarization enabled</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

    # If an email is selected, show the reader
    selected_id = st.session_state.get("selected_email")

    if selected_id:
        try:
            email = fetch_email(selected_id)
        except Exception as e:
            st.error(f"Failed to open email: {e}")
            st.session_state["selected_email"] = None
            st.stop()

        if st.button("← Back to Inbox"):
            st.session_state["selected_email"] = None
            st.rerun()

        subject = email.get("subject", "(No subject)")
        from_addr = email.get("from", "Unknown")
        body = email.get("body", "")

        st.markdown(f"## {html.escape(subject)}")
        st.markdown(
            f'<div class="sender">From <b>{html.escape(from_addr)}</b></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">Email</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="email-body">{html.escape(body) if body else "No body found."}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">AI Reply</div>',
            unsafe_allow_html=True,
        )

        user_note = st.text_area(
            "Additional instructions",
            placeholder="e.g. Make it concise, sound professional, mention my availability tomorrow...",
            height=100,
            key=f"note_{selected_id}",
        )

        # Generate in the current Streamlit run instead of forcing an immediate
        # rerun. The rerun could leave the previous draft/action block visible
        # for a moment, which produced the duplicate Generated response section.
        if st.button("✦ Generate Reply", use_container_width=True):
            try:
                with st.spinner("Generating reply..."):
                    reply = generate_reply(selected_id, user_note)
                if reply:
                    st.session_state["drafts"][selected_id] = reply
                    st.success("Reply generated.")
                else:
                    st.warning("No reply was generated.")
            except Exception as e:
                st.error(f"Failed to generate reply: {e}")

        if st.session_state.pop("reply_sent", None) == selected_id:
            st.success("Reply sent successfully.")

        if selected_id in st.session_state["drafts"]:
            # Keep the draft editor and its actions inside one Streamlit form.
            # The form gives the editor/buttons a single stable widget tree,
            # preventing the transient duplicate action-row artifact during
            # reruns after Generate/Send/Clear actions.
            with st.form(key=f"reply_form_{selected_id}", clear_on_submit=False):
                draft = st.text_area(
                    "Generated response",
                    value=st.session_state["drafts"][selected_id],
                    height=260,
                    key=f"draft_editor_{selected_id}",
                )

                c1, c2 = st.columns([1, 1], vertical_alignment="bottom")

                with c1:
                    st.form_submit_button(
                        "📤 Send Reply",
                        use_container_width=True,
                        on_click=send_reply_callback,
                        args=(selected_id, from_addr, subject),
                    )

                with c2:
                    clear_clicked = st.form_submit_button(
                        "Clear Draft",
                        use_container_width=True,
                    )

            reply_error = st.session_state.pop("reply_error", None)
            if reply_error:
                st.error(reply_error)

            if clear_clicked:
                st.session_state["drafts"].pop(selected_id, None)
                st.rerun()

    else:
        visible_emails = emails[:5]

        if not visible_emails:
            st.markdown(
                '<div class="empty-state"><h3>Your inbox is empty</h3>'
                '<p>Refresh Gmail to fetch your latest emails.</p></div>',
                unsafe_allow_html=True,
            )
        else:
            for idx, email in enumerate(visible_emails):
                email_id = str(email.get("id", f"idx_{idx}"))
                from_addr = email.get("from", "Unknown")
                subject = email.get("subject", "(No subject)")
                summary = email.get("summary", "").strip() or "No summary available."

                # Use a real Streamlit bordered container so the card wraps
                # the content correctly. The previous HTML div approach could
                # render as an empty rounded bar because Streamlit separates
                # markdown blocks from widgets.
                with st.container(border=True):
                    left, right = st.columns([6.5, 1.2], vertical_alignment="center")

                    with left:
                        st.markdown(
                            f'<div class="email-meta">{html.escape(from_addr)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="email-subject">{html.escape(subject)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            '<div class="summary-label">AI Summary</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="email-summary">{html.escape(summary)}</div>',
                            unsafe_allow_html=True,
                        )

                    with right:
                        if st.button(
                            "Open  →",
                            key=f"open_{email_id}",
                            use_container_width=True,
                        ):
                            st.session_state["selected_email"] = email_id
                            st.rerun()
