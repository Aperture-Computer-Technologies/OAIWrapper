import openai
import streamlit as st
import json
import os
import logging
import sqlite3

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

# Ensure the title is always visible
st.title("OAIwrapper")

# Hide the sidebar if not authenticated
if "authentication_status" not in st.session_state or not st.session_state.authentication_status:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize SQLite database
def init_db():
    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error("Database error: " + str(e))
        st.error("Database initialization failed.")

# Call the function to initialize the database
init_db()

# User-specific chat session paths
def get_user_data_dir(username):
    return os.path.join("user_data", username)

def get_user_chat_file(username):
    return os.path.join(get_user_data_dir(username), "sessions.json")

# Load chat sessions for the logged-in user
def load_chat_sessions(username):
    save_file = get_user_chat_file(username)
    if os.path.exists(save_file):
        with open(save_file, "r") as f:
            data = json.load(f)
            st.session_state.openai_model = data.get("selected_model", "gpt-3.5-turbo")
            return data.get("sessions", {})
    return {}

# Save chat sessions for the logged-in user
def save_chat_sessions(username):
    save_file = get_user_chat_file(username)
    data = {
        "sessions": st.session_state.chat_sessions,
        "selected_model": st.session_state.openai_model,
    }
    if not os.path.exists(get_user_data_dir(username)):
        os.makedirs(get_user_data_dir(username))
    with open(save_file, "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Chat sessions saved for user {username}. Current model: {st.session_state.openai_model}")

# Initialize session state variables
def initialize_session_state():
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "name" not in st.session_state:
        st.session_state.name = None

# Main app logic
def main_app():
    st.write(f"Welcome {st.session_state.name}!")

    user_data_dir = get_user_data_dir(st.session_state.username)
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    # Initialize chat sessions and other state variables
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = load_chat_sessions(st.session_state.username)
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = None
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-3.5-turbo"

    def select_chat(chat_name):
        st.session_state.current_chat = chat_name

    def create_new_chat():
        new_chat_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
        st.session_state.chat_sessions[new_chat_name] = []
        st.session_state.current_chat = new_chat_name
        save_chat_sessions(st.session_state.username)

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
            save_chat_sessions(st.session_state.username)

        if st.button("Logout", key="logout"):
            st.session_state.authentication_status = None
            st.session_state.username = None
            st.session_state.name = None
            st.experimental_set_query_params(page="login")
            st.experimental_rerun()

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
                    response_container = st.empty()
                    response = ""

                    logger.info(f"Generating response using model: {st.session_state.openai_model}")
                    for chunk in client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in messages
                        ],
                        stream=True,
                    ):
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                            response += chunk.choices[0].delta.content
                            response_container.markdown(response)

            messages.append({"role": "assistant", "content": response})
            save_chat_sessions(st.session_state.username)
    else:
        st.write("No chat session selected.")
