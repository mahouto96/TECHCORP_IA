import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
CHAT_URL = f"{API_URL}/api/chat"

st.set_page_config(page_title="DevAssist-GPT", page_icon="🤖")
st.title("DevAssist-GPT")
st.caption("Assistant local pour Python, FastAPI, les API REST, Git et Docker.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pose ta question technique..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("DevAssist-GPT réfléchit..."):
            try:
                response = requests.post(
                    CHAT_URL,
                    json={"messages": st.session_state.messages[-20:]},
                    timeout=(5, 310),
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(
                    payload.get("answer"), str
                ):
                    raise ValueError("Le champ 'answer' est absent.")
                answer = payload["answer"]
            except requests.RequestException as exc:
                st.error(
                    "Impossible de joindre l'API. Vérifie que les services sont "
                    f"démarrés. Détail : {exc}"
                )
            except (ValueError, KeyError) as exc:
                st.error(f"La réponse de l'API est invalide. Détail : {exc}")
            else:
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
