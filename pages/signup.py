import streamlit as st
import sqlite3
import bcrypt

# Register a new user
def register_user(username, name, password):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
    INSERT INTO users (username, name, password) VALUES (?, ?, ?)
    ''', (username, name, hashed_password.decode('utf-8')))
    conn.commit()
    conn.close()

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

st.header("Sign Up")
new_username = st.text_input("Username", key="signup_username")
new_name = st.text_input("Full Name", key="signup_name")
new_password = st.text_input("Password", type="password", key="signup_password")
new_password_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
if st.button("Register"):
    if new_password == new_password_confirm:
        if new_username and new_name and new_password:
            register_user(new_username, new_name, new_password)
            st.success("Registration successful! You can now log in.")
            st.info("Go to the login page to continue.")
            st.query_params.update(page="login")  # Redirect to login page
        else:
            st.error("All fields are required.")
    else:
        st.error("Passwords do not match")
if st.button("Already have an account? Log in"):
    st.query_params.update(page="login")  # Redirect to login page
