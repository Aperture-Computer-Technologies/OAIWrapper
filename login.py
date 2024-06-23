#login.py
import streamlit as st
import sqlite3
import bcrypt

# Fetch user data for authentication
def fetch_users():
    try:
        conn = sqlite3.connect('/home/appuser/data/users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, name, password FROM users')
        users = cursor.fetchall()
        conn.close()
        return {user[0]: {"name": user[1], "password": user[2]} for user in users}
    except sqlite3.Error as e:
        st.error("Database error: " + str(e))
        return {}

# Authentication setup
def authenticate_user(username, password):
    users = fetch_users()
    if username in users:
        stored_password = users[username]["password"]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return users[username]["name"]
    return None

# Main login function
def main_login():
    st.header("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        name = authenticate_user(username, password)
        if name:
            st.session_state.authentication_status = True
            st.session_state.username = username
            st.session_state.name = name
            st.query_params["page"] = "app"
            st.rerun()
        else:
            st.session_state.authentication_status = False
            st.error("Username or password is incorrect")
    
    if st.button("New user? Sign up"):
        st.query_params["page"] = "signup"