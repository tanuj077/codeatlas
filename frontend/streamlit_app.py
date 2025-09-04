import os
from dotenv import load_dotenv
import streamlit as st

import requests

st.set_page_config(page_title="CodeAtlas Chat", page_icon="🧭")

st.title("🧠 Chat with CodeAtlas")

load_dotenv()
backend_url = os.getenv("CODEATLAS_BACKEND_URL", "")

# ---- Repo Selection ----
try:
    res = requests.get(f"{backend_url}/repos")
    repo_list = res.json().get("repos", [])
except Exception:
    repo_list = []

if not repo_list:
    st.error("No repositories indexed yet.")
    st.stop()

selected_repo = st.sidebar.selectbox("📁 Choose a repository", repo_list)

# ---- Chat History ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- Display Chat Messages ----
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# ---- User Chat Input ----
user_input = st.chat_input("Ask a question about your codebase...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    # ---- Graceful API Call ----
    try:
        response = requests.post(
            f"{backend_url}/chat?repo_name={selected_repo}",
            json={"query": user_input},
            timeout=240,  
        )
        response.raise_for_status()
        answer = response.json().get("answer", "🤖 No answer returned.")
    except requests.exceptions.ConnectionError:
        answer = (
            "🚫 Could not connect to CodeAtlas backend. "
            "Please ensure the FastAPI server is running at `localhost:8000`."
        )
    except requests.exceptions.Timeout:
        answer = "⏳ The server took too long to respond. Try again later."
    except requests.exceptions.HTTPError as http_err:
        answer = f"⚠️ Server returned an error: {http_err.response.status_code}"
    except Exception as e:
        answer = f"❌ Unexpected error: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.chat_history.append(("assistant", answer))
