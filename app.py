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
        conn = sqlite3.connect('/home/appuser/data/users.db')
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
    return os.path.join("/home/appuser/data/user_data", username)

def get_user_chat_file(username):
    return os.path.join(get_user_data_dir(username), "sessions.json")

# Load chat sessions for the logged-in user
def load_chat_sessions(username):
    save_file = get_user_chat_file(username)
    if os.path.exists(save_file):
        with open(save_file, "r") as f:
            sessions = json.load(f).get("sessions", {})

            # Ensure each session has the correct structure
            for chat_name, session in sessions.items():
                if not isinstance(session, dict):
                    sessions[chat_name] = {"messages": session, "selected_model": "gpt-3.5-turbo"}
                elif "messages" not in session or "selected_model" not in session:
                    sessions[chat_name] = {
                        "messages": session.get("messages", []) if isinstance(session.get("messages", []), list) else [],
                        "selected_model": session.get("selected_model", "gpt-3.5-turbo")
                    }
            return sessions
    return {}

# Save chat sessions for the logged-in user
def save_chat_sessions(username):
    save_file = get_user_chat_file(username)
    data = {
        "sessions": st.session_state.chat_sessions,
    }
    if not os.path.exists(get_user_data_dir(username)):
        os.makedirs(get_user_data_dir(username))
    with open(save_file, "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Chat sessions saved for user {username}.")

# Initialize session state variables
def initialize_session_state():
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "name" not in st.session_state:
        st.session_state.name = None
    if "stop_generation" not in st.session_state:
        st.session_state.stop_generation = False
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = None
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-3.5-turbo"
    if "chat_to_rename" not in st.session_state:
        st.session_state.chat_to_rename = None
    if "temperature" not in st.session_state:
        st.session_state.temperature = 1.0
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 256
    if "top_p" not in st.session_state:
        st.session_state.top_p = 1.0
    if "frequency_penalty" not in st.session_state:
        st.session_state.frequency_penalty = 0.0

initialize_session_state()

# Callbacks for chat session actions
def select_chat(chat_name):
    st.session_state.current_chat = chat_name
    chat_data = st.session_state.chat_sessions.get(chat_name, {})
    st.session_state.selected_model = chat_data.get("selected_model", "gpt-3.5-turbo")

def create_new_chat():
    new_chat_name = f"Chat {len(st.session_state.chat_sessions) + 1}"
    st.session_state.chat_sessions[new_chat_name] = {
        "messages": [],
        "selected_model": "gpt-3.5-turbo"
    }
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
            if cancel_button:
                st.session_state.chat_to_rename = None

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
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-3.5-turbo"

    # Sidebar for chat session management and model switcher
    with st.sidebar:
        st.subheader("Chat Sessions")

        for chat_name in list(st.session_state.chat_sessions.keys()):  # Convert to list to avoid size change issues
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.button(chat_name, on_click=select_chat, args=(chat_name,))
            with col2:
                st.button("🗑️", key=f"delete_{chat_name}", on_click=delete_chat, args=(chat_name,))
            with col3:
                st.button("✏️", key=f"rename_{chat_name}", on_click=trigger_rename, args=(chat_name,))

        st.button("New Chat", on_click=create_new_chat)

        st.subheader("Model Switcher")
        selected_model = st.selectbox(
            "Choose the OpenAI model:",
            ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"],
            index=["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"].index(st.session_state.selected_model)
        )
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            # Update the selected model for the current chat session
            if st.session_state.current_chat:
                st.session_state.chat_sessions[st.session_state.current_chat]["selected_model"] = selected_model
                save_chat_sessions(st.session_state.username)

        if st.button("Logout", key="logout"):
            st.session_state.authentication_status = None
            st.session_state.username = None
            st.session_state.name = None

        # Advanced options expander
        with st.expander("Advanced Options"):
            st.subheader("Model Parameters")
            st.session_state.temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.get("temperature", 1.0),
                step=0.01
            )
            st.session_state.max_tokens = st.slider(
                "Maximum Tokens",
                min_value=1,
                max_value=4095,
                value=st.session_state.get("max_tokens", 256),
                step=1
            )
            st.session_state.top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("top_p", 1.0),
                step=0.01
            )
            st.session_state.frequency_penalty = st.slider(
                "Frequency Penalty",
                min_value=-2.0,
                max_value=2.0,
                value=st.session_state.get("frequency_penalty", 0.0),
                step=0.01
            )
    # Render the rename input section if needed
    render_rename_input()

    # Display messages of the current chat session
    if st.session_state.current_chat:
        st.subheader(f"Current Chat: {st.session_state.current_chat}")
        messages = st.session_state.chat_sessions[st.session_state.current_chat]["messages"]

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

                    # Add stop button
                    stop_button_pressed = False

                    def stop_button_callback():
                        nonlocal stop_button_pressed
                        stop_button_pressed = True

                    st.button("Stop", key="stop_button", on_click=stop_button_callback)

                    logger.info(f"Generating response using model: {st.session_state.selected_model}")

                    for chunk in client.chat.completions.create(
                        model=st.session_state.selected_model,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in messages
                        ],
                        # Parameters are passed here from session state
                        temperature=st.session_state.get("temperature", 1.0),
                        max_tokens=st.session_state.get("max_tokens", 256),
                        top_p=st.session_state.get("top_p", 1.0),
                        frequency_penalty=st.session_state.get("frequency_penalty", 0),
                        stream=True,
                    ):
                        if stop_button_pressed:
                            logger.info("Generation stopped by user.")
                            stop_button_pressed = False  # Reset the state for next use
                            break

                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                            response += chunk.choices[0].delta.content
                            response_container.markdown(response)  # Render bot's response as markdown

            # Save the response (partially or fully generated) if it exists
            if response:
                messages.append({"role": "assistant", "content": response})
                save_chat_sessions(st.session_state.username)
    else:
        st.write("No chat session selected.")

if __name__ == "__app__":
    initialize_session_state()
    if st.session_state.authentication_status:
        main_app()
    else:
        st.write("Please log in to access the chat.")