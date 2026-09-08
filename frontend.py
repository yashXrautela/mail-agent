import streamlit as st
import requests
import html
from datetime import timedelta

API_BASE = "http://127.0.0.1:8000"  # adjust if your backend runs elsewhere

# ---------- Page setup ----------
st.set_page_config(page_title="📧 AI Mail Agent", layout="wide")

# Minimal styling for nicer cards
st.markdown("""
<style>
.email-card {
    border: 1px solid #e6e6e6;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 8px rgba(0,0,0,0.04);
    background: #fff;
}
.email-header {
    display:flex; align-items:center; gap:.75rem; justify-content:space-between;
}
.email-meta {
    font-size: 1.1rem;
    color: #FFFFFF;
    font-weight: 500;
}
.email-actions {display:flex; gap:.5rem; flex-wrap:wrap;}
.email-body {
    background:#fafafa; border:1px solid #eee; border-radius:10px; padding:0.75rem; margin-top:.5rem;
    white-space:pre-wrap;
}
.textarea-wrap textarea {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers & state ----------
def init_state():
    st.session_state.setdefault("expanded", {})   # {email_id: bool}
    st.session_state.setdefault("drafts", {})     # {email_id: str}

def toggle_expand(email_id: str):
    st.session_state["expanded"][email_id] = not st.session_state["expanded"].get(email_id, False)

@st.cache_data(ttl=timedelta(seconds=30).total_seconds(), show_spinner=False)
def fetch_emails(force_refresh=False):
    """Fetch emails with optional force refresh"""
    if force_refresh:
        # Clear the cache for this function
        fetch_emails.clear()
    r = requests.get(f"{API_BASE}/emails", timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_email(email_id: str):
    r = requests.get(f"{API_BASE}/emails/{email_id}", timeout=30)
    r.raise_for_status()
    return r.json()

def generate_reply_for(email_id: str, body: str):
    """
    Prefer POST /emails/{id}/generate-response if you created it.
    If your backend uses a different route, update here.
    """
    # Try REST path version:
    url = f"{API_BASE}/emails/{email_id}/generate-response"
    try:
        r = requests.post(url, timeout=30)
        if r.status_code == 200:
            return r.json().get("response", "")
    except Exception:
        pass

    # Fallback to a generic body-based endpoint if you have one:
    r = requests.post(f"{API_BASE}/generate_response", json={"email_body": body}, timeout=30)
    r.raise_for_status()
    return r.json().get("response", "")

def send_email(to: str, subject: str, body: str):
    payload = {"to": to, "subject": subject, "body": body}
    r = requests.post(f"{API_BASE}/send_email", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

init_state()

st.title("📧 AI Mail Agent")
top_col1, top_col2 = st.columns([1,3])
with top_col1:
    if st.button("🔄 Refresh"):
        try:
            with st.spinner("Fetching new emails..."):
                # Call the refresh endpoint
                r = requests.post(f"{API_BASE}/refresh", timeout=30)
                r.raise_for_status()
                result = r.json()
                # Clear the emails cache
                fetch_emails.clear()
                st.success(f"✅ Retrieved {result['count']} emails!")
                st.rerun()  # Using the new st.rerun() instead of experimental_rerun
        except Exception as e:
            st.error(f"Failed to refresh: {e}")
with top_col2:
    st.caption("Showing top 5 emails • Expand to read, then generate and send a response.")

# ---------- Load emails ----------
try:
    emails = fetch_emails()
except Exception as e:
    st.error(f"Failed to load emails: {e}")
    st.stop()

emails = emails[:5] if isinstance(emails, list) else []

# ---------- Render emails ----------
for idx, email in enumerate(emails):
    email_id = str(email.get("id", f"idx_{idx}"))
    from_addr = email.get("from", "Unknown")
    subject = email.get("subject", "(No subject)")
    summary = email.get("summary", "").strip() or "—"
    is_expanded = st.session_state["expanded"].get(email_id, False)

    with st.container():
        st.markdown('<div class="email-card">', unsafe_allow_html=True)

        # Header row
        hcol1, hcol2 = st.columns([6, 1])
        with hcol1:
            st.markdown(f"### {subject}")
            st.markdown(f"<div class='email-meta'>From: <b>{html.escape(from_addr)}</b></div>",unsafe_allow_html=True)
        with hcol2:
            st.button(("Collapse" if is_expanded else "Expand") + " 📜",
                      key=f"btn_expand_{email_id}",
                      on_click=toggle_expand, args=(email_id,))

        # Summary
        st.markdown("**Summary:**")
        st.write(summary if summary else "No summary available.")

        # Expanded area (inline, directly beneath summary)
        if is_expanded:
            # Load full email
            try:
                full_email = fetch_email(email_id)
                body = full_email.get("body", "")
            except Exception as e:
                st.error(f"Failed to fetch this email: {e}")
                body = ""

            st.markdown("<div class='email-body'>", unsafe_allow_html=True)
            st.write(body if body else "No body found.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Actions inside the expanded area
            ac1, ac2, ac3 = st.columns([1,1,6])
            with ac1:
                user_note = st.text_area("Additional instructions (optional)", 
                                       key=f"note_{email_id}",
                                       placeholder="E.g., 'Make it formal' or 'Include meeting availability'",
                                       height=100)
                if st.button("✍️ Generate Response", key=f"gen_{email_id}"):
                    try:
                        # Update API call to include user_note
                        payload = {"user_note": user_note}
                        r = requests.post(f"{API_BASE}/emails/{email_id}/generate-response", 
                                        json=payload, timeout=30)
                        r.raise_for_status()
                        reply = r.json().get("response", "")
                        if reply:
                            st.session_state["drafts"][email_id] = reply
                            st.success("Draft generated.")
                        else:
                            st.warning("No response generated.")
                    except Exception as e:
                        st.error(f"Failed to generate response: {e}")

            # Draft editor + Send button (only after generation)
            if email_id in st.session_state["drafts"]:
                st.markdown("**✍️ Draft Response**")
                st.session_state["drafts"][email_id] = st.text_area(
                    label=f"draft_{email_id}",
                    value=st.session_state['drafts'][email_id],
                    height=200,
                    label_visibility="collapsed",
                    key=f"ta_{email_id}"
                )

                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.button("📤 Send Response", key=f"send_{email_id}"):
                        try:
                            send_email(
                                to=from_addr,
                                subject=f"Re: {subject}",
                                body=st.session_state['drafts'][email_id]
                            )
                            st.success("Email sent! ✅")
                        except Exception as e:
                            st.error(f"Failed to send email: {e}")
                with b2:
                    if st.button("🗑️ Clear Draft", key=f"clear_{email_id}"):
                        st.session_state["drafts"].pop(email_id, None)
                        st.info("Draft cleared.")

        st.markdown('</div>', unsafe_allow_html=True)
