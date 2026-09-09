import streamlit as st
import requests

API_BASE = "https://mail-agent-k3sk.onrender.com"


def api_headers():
    token = st.session_state.get("session_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


if not st.session_state.get("session_token"):
    st.link_button("Sign in with Google", f"{API_BASE}/auth/google")
    st.stop()
st.set_page_config(page_title="✍️ Compose Email", layout="wide")

st.title("✍️ Compose New Email")
to_address = st.text_input("To", key="compose_to", placeholder="recipient@example.com")
idea = st.text_area("Brief mail idea", key="compose_idea", placeholder="E.g. Schedule a meeting for next week", height=80)
generate_clicked = st.button("Generate ✨", key="compose_generate")
subject = st.session_state.get("compose_subject", "")
body = st.session_state.get("compose_body", "")
if generate_clicked:
    if not to_address or not idea:
        st.error("Please enter both recipient and idea.")
    else:
        try:
            with st.spinner("Generating email..."):
                r = requests.post(f"{API_BASE}/compose", json={"to": to_address, "idea": idea}, headers=api_headers(), timeout=30)
                r.raise_for_status()
                result = r.json()
                st.session_state["compose_subject"] = result.get("subject", "")
                st.session_state["compose_body"] = result.get("body", "")
                subject = st.session_state["compose_subject"]
                body = st.session_state["compose_body"]
                st.success("Draft generated!")
        except Exception as e:
            st.error(f"Failed to generate: {e}")
if subject or body:
    subject = st.text_input("Subject", value=subject, key="compose_subject_input")
    body = st.text_area("Body", value=body, key="compose_body_input", height=180)
    if st.button("Send 📤", key="compose_send"):
        if not to_address or not subject or not body:
            st.error("Please fill all fields before sending.")
        else:
            try:
                payload = {"to": to_address, "subject": subject, "body": body}
                r = requests.post(f"{API_BASE}/send_email", json=payload, headers=api_headers(), timeout=30)
                r.raise_for_status()
                st.success("Email sent! ✅")
                for k in ["compose_subject", "compose_body", "compose_to", "compose_idea"]:
                    if k in st.session_state:
                        del st.session_state[k]
            except Exception as e:
                st.error(f"Failed to send: {e}")
