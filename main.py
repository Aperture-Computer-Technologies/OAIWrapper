import streamlit as st
import login
import signup
import app

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

if not st.query_params.get_all("page"):
    st.query_params["page"] = "login"
    st.rerun()

# Determine the page to load
page = st.query_params.get_all("page")[0]

# Render the appropriate page
if st.session_state.authentication_status:
    if st.query_params["page"] == "signup":
        st.query_params["page"] ="app"
        st.rerun()
    app.main_app()
else:
    if st.query_params["page"] == "signup":
        signup.main_signup()
    else:
        login.main_login()
