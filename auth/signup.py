import streamlit as st

def signup_page():

    st.title("Create Account")

    role = st.selectbox("Signup as", ["Patient", "Doctor"])

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        if not email or not password:
            st.error("Email and password cannot be empty")
        else:
            st.success("Account created successfully")
            st.session_state.page = "login"
            st.rerun()