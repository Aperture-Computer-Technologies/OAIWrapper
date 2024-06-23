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

# Determine the page to load
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["login"])[0]

# Render the appropriate page
if st.session_state.authentication_status:
    if page == "signup":
        st.experimental_set_query_params(page="app")
        st.experimental_rerun()
    app.main_app()
else:
    if page == "signup":
        signup.main_signup()
    else:
        login.main_login()
