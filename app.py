from openai import OpenAI
import streamlit as st
import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")

st.title("OAIwrapper")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Define file paths
SAVE_DIR = "chat_sessions"
SAVE_FILE = os.path.join(SAVE_DIR, "sessions.json")

# Load chat sessions from file
def load_chat_sessions():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            st.session_state.openai_model = data.get("selected_model", "gpt-3.5-turbo")  # Load model
            return data.get("sessions", {})
    return {}

# Save chat sessions to file
def save_chat_sessions():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    data = {
        "sessions": st.session_state.chat_sessions,
        "selected_model": st.session_state.openai_model,  # Save model
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Chat sessions saved. Current model: {st.session_state.openai_model}")

# Initialize chat sessions and other state variables
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = load_chat_sessions()
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"  # Default, but will be loaded from file

def select_chat(chat_name):
    st.session_state.current_chat = chat_name

def create_new_chat():
    new_chat_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
    st.session_state.chat_sessions[new_chat_name] = []
    st.session_state.current_chat = new_chat_name
    save_chat_sessions()  # Save immediately when creating a new chat

# Sidebar for chat session management and model switcher
with st.sidebar:
    st.subheader("Chat Sessions")
    for chat_name in st.session_state.chat_sessions:
        if st.button(chat_name):
            select_chat(chat_name)

    if st.button("New Chat"):
        create_new_chat()

    st.subheader("Model Switcher")
    selected_model = st.selectbox(
        "Choose the OpenAI model:",
        ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"],
        index=["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"].index(st.session_state.openai_model)
    )
    if selected_model != st.session_state.openai_model:
        st.session_state.openai_model = selected_model
        logger.info(f"Model switched to: {st.session_state.openai_model}")
        save_chat_sessions()  # Save session with the new model

# Display messages of the current chat session
if st.session_state.current_chat:
    st.subheader(f"Current Chat: {st.session_state.current_chat}")
    messages = st.session_state.chat_sessions[st.session_state.current_chat]

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Waiting for response..."):
            with st.chat_message("assistant"):
                response_container = st.empty()  # Placeholder for the response
                response = ""

                logger.info(f"Generating response using model: {st.session_state.openai_model}")
                for chunk in client.chat.completions.create(
                    model=st.session_state.openai_model,  # Use selected model
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in messages
                    ],
                    stream=True,
                ):
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        response += chunk.choices[0].delta.content
                        response_container.markdown(response)  # Update the response incrementally

        messages.append({"role": "assistant", "content": response})
        save_chat_sessions()  # Save chat session after receiving response
else:
    st.write("No chat session selected.")
