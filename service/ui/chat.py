from typing import Dict, List, Generator, Any
import os
import re
import streamlit as st
import requests
from dataclasses import dataclass

from service.api.auth import AuthConfig


@dataclass
class ChatMessage:
    role: str
    content: str


class ChatClient:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.expert_id = os.getenv("CHAT_EXPERT_ID")
        self.auth = AuthConfig()

    def send_message(
        self, question: str, history: List[ChatMessage], stream: bool = False
    ) -> Dict[str, Any]:
        payload = {
            "question": question,
            "expert_id": self.expert_id,
            "conversation_history": [
                {"role": msg.role, "content": msg.content} for msg in history
            ],
            "stream": stream,
        }
        response = requests.post(self.api_url, json=payload, headers=self.auth.headers)
        return response.json()


def init_chat_state():
    """Initialize chat-related session state variables"""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_visible" not in st.session_state:
        st.session_state.chat_visible = False


# def stream_response(response: requests.Response) -> Generator[str, None, None]:
#     """Convert API stream response to generator for st.write_stream"""
#     first_chunk = True
#     for line in response.iter_lines():
#         if line:
#             # Skip first chunk (metadata) that we stored
#             if first_chunk:
#                 first_chunk = False
#                 continue

#             # Parse JSON chunk
#             chunk = line.decode("utf-8")
#             try:
#                 data = json.loads(chunk)
#                 if data.get("type") == "text" and data.get("content"):
#                     yield data["content"]
#             except json.JSONDecodeError:
#                 continue


def render_chat_widget():
    """Render the chat interface"""
    init_chat_state()

    # add a top spacer using a horizontal rule
    st.markdown("---")

    # Chat toggle button with conditional label
    chat_label = (
        "👋 Chat schließen" if st.session_state.chat_visible else "💬 Chat Support"
    )
    if st.button(chat_label):
        st.session_state.chat_visible = not st.session_state.chat_visible
        st.rerun()

    if st.session_state.chat_visible:
        with st.container():
            st.subheader("Chat Support")
            st.info(
                "Hier können Sie weitere Fragen stellen, wenn Sie auf Probleme bei der Fehlerbehebung stoßen."
            )

            # Create a container for chat messages
            chat_container = st.container()

            # Display all messages in the container
            with chat_container:
                for msg in st.session_state.chat_messages:
                    with st.chat_message(msg.role):
                        st.write(msg.content)

            # Create the input at the bottom
            prompt = st.chat_input("Ihre Frage...")

            if prompt:
                user_msg = ChatMessage(role="user", content=prompt)
                st.session_state.chat_messages.append(user_msg)

                with chat_container:
                    with st.chat_message("user"):
                        st.write(prompt)

                    client = ChatClient(os.getenv("CHAT_API_URL"))
                    with st.chat_message("assistant"):
                        try:
                            response_data = client.send_message(
                                prompt, st.session_state.chat_messages, stream=False
                            )

                            # Store metadata in session state
                            st.session_state.last_response_metadata = {
                                "query_keywords": response_data.get("query_keywords"),
                                "used_context": response_data.get("used_context"),
                                "relevant_quotes": response_data.get("relevant_quotes"),
                                "question_id": response_data.get("question_id"),
                                "created_on": response_data.get("created_on"),
                            }

                            # Display answer
                            answer = response_data.get("answer", "No answer received")
                            # process the answer
                            answer = _postprocess_answer(answer)
                            st.write(answer)

                            # Display sources immediately after the answer
                            if response_data.get("used_context"):
                                unique_docs = {
                                    doc["document_name"]
                                    for doc in response_data["used_context"]
                                }
                                if unique_docs:
                                    st.markdown("**Quellen:**")
                                    cols = st.columns(len(unique_docs))
                                    for idx, doc in enumerate(unique_docs):
                                        with cols[idx]:
                                            st.markdown(
                                                f"<div style='background-color: #f0f2f6; padding: 5px 10px; border-radius: 15px; display: inline-block; font-size: 0.8em;'>{doc}</div>",
                                                unsafe_allow_html=True,
                                            )

                            # Add to chat history
                            assistant_msg = ChatMessage(
                                role="assistant", content=answer
                            )
                            st.session_state.chat_messages.append(assistant_msg)

                        except Exception as e:
                            st.error(f"Fehler bei der Kommunikation: {str(e)}")


def _postprocess_answer(answer: str) -> str:
    """Postprocess the chatbot answer:
    - remove reasoning: content between <res></res> tags, including the tags
    - remove <ans> and </ans> tags
    - remove citation markers (e.g. <<1>>, <<2>>, etc.)
    - if answer is none, replace with default message
    """
    if not answer:
        return "Leider konnte keine Antwort gefunden werden. Bitte versuchen Sie es mit einer anderen Frage erneut."
    # Remove reasoning
    answer = re.sub(r"<res>.*?</res>", "", answer)
    # Remove <ans> and </ans> tags
    answer = re.sub(r"<ans>|</ans>", "", answer)
    # Remove citation markers
    answer = re.sub(r"<<\d+>>", "", answer)
    return answer
