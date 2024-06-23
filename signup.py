#signup.py
import streamlit as st
import sqlite3
import bcrypt

# Register a new user
def register_user(username, name, password):
    try:
        conn = sqlite3.connect('data2/users.db')
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (username, name, password) VALUES (?, ?, ?)', (username, name, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
        return False
    except sqlite3.Error as e:
        st.error("Database error: " + str(e))
        return False

# Main signup function
def main_signup():
    print("main signup")
    st.header("Sign Up")
    new_username = st.text_input("Username", key="signup_username")
    new_name = st.text_input("Full Name", key="signup_name")
    new_password = st.text_input("Password", type="password", key="signup_password")
    new_password_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
    
    if st.button("Register"):
        if new_password == new_password_confirm:
            if new_username and new_name and new_password:
                if register_user(new_username, new_name, new_password):
                    st.success("Registration successful! You can now log in.")
                    st.info("Go to the login page to continue.")
                    st.query_params["page"] =" login"
                    st.rerun()
            else:
                st.error("All fields are required.")
        else:
            st.error("Passwords do not match")
    
    if st.button("Already have an account? Log in"):
        st.query_params["page"] = "login"
