"""
Streamlit demo frontend cho Financial RAG Chatbot.
Gọi sang backend FastAPI qua BACKEND_URL (set trong docker-compose.yml).
"""

import os
import uuid

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Financial RAG Chatbot", page_icon="💬")
st.title("💬 Financial RAG Chatbot")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

query = st.chat_input("Hỏi về báo cáo tài chính, hợp đồng tín dụng, bản cáo bạch...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"session_id": st.session_state.session_id, "query": query},
                timeout=30,
            )
            resp.raise_for_status()
            answer = resp.json().get("answer", "Không nhận được câu trả lời.")
        except requests.exceptions.RequestException as e:
            answer = f"Lỗi kết nối tới backend: {e}"

        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})