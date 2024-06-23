#app.py
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

# st.set_page_config(layout="wide")

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

# Access environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")

# Use the API key with OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Initialize SQLite database
def init_db():
    try:
        conn = sqlite3.connect('data/users.db')
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
    return os.path.join("data/user_data", username)

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

    def delete_chat(chat_name):
        if chat_name in st.session_state.chat_sessions:
            del st.session_state.chat_sessions[chat_name]
            save_chat_sessions(st.session_state.username)
            if st.session_state.current_chat == chat_name:
                st.session_state.current_chat = None

    def rename_chat(old_name, new_name):
        if old_name in st.session_state.chat_sessions and new_name:
            st.session_state.chat_sessions[new_name] = st.session_state.chat_sessions.pop(old_name)
            if st.session_state.current_chat == old_name:
                st.session_state.current_chat = new_name
            save_chat_sessions(st.session_state.username)

    if 'chat_to_rename' not in st.session_state:
        st.session_state.chat_to_rename = None

    def trigger_rename(chat_name):
        st.session_state.chat_to_rename = chat_name

    # Function to render the rename input
    def render_rename_input():
        if st.session_state.chat_to_rename:
            with st.form(key='rename_form'):
                new_name = st.text_input(f"Rename `{st.session_state.chat_to_rename}` to", st.session_state.chat_to_rename)
                col1, col2 = st.columns([1, 1])
                with col1:
                    submit_button = st.form_submit_button(label='Rename')
                with col2:
                    cancel_button = st.form_submit_button(label='Cancel')

                if submit_button:
                    rename_chat(st.session_state.chat_to_rename, new_name)
                    st.session_state.chat_to_rename = None  # Reset the variable
                    st.experimental_rerun()  # Refresh the page to reflect changes

                if cancel_button:
                    st.session_state.chat_to_rename = None
                    st.experimental_rerun()

    def render_rename_input():
        if st.session_state.chat_to_rename:
            with st.form(key='rename_form'):
                new_name = st.text_input(f"Rename `{st.session_state.chat_to_rename}` to", st.session_state.chat_to_rename)
                col1, col2 = st.columns([1, 1])
                with col1:
                    submit_button = st.form_submit_button(label='Rename')
                with col2:
                    cancel_button = st.form_submit_button(label='Cancel')

                if submit_button:
                    rename_chat(st.session_state.chat_to_rename, new_name)
                    st.session_state.chat_to_rename = None  # Reset the variable
                    st.experimental_rerun()  # Refresh the page to reflect changes

                if cancel_button:
                    st.session_state.chat_to_rename = None
                    st.experimental_rerun()

    # Sidebar for chat session management and model switcher
    with st.sidebar:
        st.subheader("Chat Sessions")

        for chat_name in list(st.session_state.chat_sessions.keys()):  # Convert to list to avoid size change issues
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                if st.button(chat_name):
                    select_chat(chat_name)
            with col2:
                if st.button("🗑️", key=f"delete_{chat_name}"):
                    delete_chat(chat_name)
            with col3:
                if st.button("✏️", key=f"rename_{chat_name}"):
                    trigger_rename(chat_name)

        if st.button("New Chat"):
            create_new_chat()
            st.rerun()

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
            st.query_params["page"] = "login"
            st.rerun()

    # Render the rename input section if needed
    render_rename_input()

    # Display messages of the current chat session
    if st.session_state.current_chat:
        st.subheader(f"Current Chat: {st.session_state.current_chat}")
        messages = st.session_state.chat_sessions[st.session_state.current_chat]

        for message in messages:
            if message["role"] == "user":
                with st.chat_message(message["role"]):
                    st.text(message["content"])  # Render user's message as plain text
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])  # Render bot's message as markdown

        if prompt := st.chat_input("What is up?"):
            messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.text(prompt)  # Render user's input as plain text

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
                            response_container.markdown(response)  # Render bot's response as markdown

            messages.append({"role": "assistant", "content": response})
            save_chat_sessions(st.session_state.username)
    else:
        st.write("No chat session selected.")