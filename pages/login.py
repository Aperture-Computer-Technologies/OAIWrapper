import streamlit as st
import sqlite3
import bcrypt

# Fetch user data for authentication
def fetch_users():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, name, password FROM users')
    users = cursor.fetchall()
    conn.close()
    return {user[0]: {"name": user[1], "password": user[2]} for user in users}

# Authentication setup
def authenticate_user(username, password):
    users = fetch_users()
    if username in users:
        stored_password = users[username]["password"]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return users[username]["name"]
    return None

# Initialize session state variables
def initialize_session_state():
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "name" not in st.session_state:
        st.session_state.name = None

# Initialize session state before usage
initialize_session_state()

st.header("Login")
username = st.text_input("Username", key="login_username")
password = st.text_input("Password", type="password", key="login_password")
if st.button("Login"):
    name = authenticate_user(username, password)
    if name:
        st.session_state.authentication_status = True
        st.session_state.username = username
        st.session_state.name = name
        st.query_params.update(page="main")  # Redirect to main app
        st.experimental_rerun()  # Rerun to reflect the authenticated state
    else:
        st.session_state.authentication_status = False
        st.error("Username or password is incorrect")
if st.button("New user? Sign up"):
    st.query_params.update(page="signup")  # Redirect to signup page
