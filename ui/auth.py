import streamlit as st
from data.user_store import get_user, create_user


def handle_authentication():
    """
    Handle login/register in sidebar and return logged-in username or None
    """

    if "user" not in st.session_state:
        st.session_state.user = None

    # If already logged in
    if st.session_state.user:
        return st.session_state.user

    st.header(st.secrets['app']['title'])
    st.subheader(st.secrets['app']['subtitle'])
    st.write(st.secrets['app']['subheader'])

    auth_mode = st.sidebar.radio(
        "Select Action",
        ["Login", "Register"],
        key="auth_mode"
    )

    if auth_mode == "Login":
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.sidebar.button("Login", type="primary"):
            if username.strip() and password.strip():
                user = get_user(username.strip())
                if user and user.get("password") == password:
                    st.session_state.user = username.strip()
                    #st.rerun()
                else:
                    st.sidebar.error("Invalid username or password")
            else:
                st.sidebar.error("Please enter username and password")

    else:
        new_username = st.sidebar.text_input(
            "Choose Username",
            key="reg_username"
        )
        new_password = st.sidebar.text_input(
            "Choose Password",
            type="password",
            key="reg_password"
        )
        confirm_password = st.sidebar.text_input(
            "Confirm Password",
            type="password",
            key="reg_confirm"
        )

        if st.sidebar.button("Register", type="primary"):
            if new_username.strip() and new_password.strip():
                if new_password != confirm_password:
                    st.sidebar.error("Passwords don't match")
                elif get_user(new_username.strip()):
                    st.sidebar.error("Username already exists")
                else:
                    create_user(new_username.strip(), new_password)
                    st.sidebar.success("User created! Please login.")
            else:
                st.sidebar.error("Please fill all fields")

    return None


def show_user_sidebar(username):
    st.sidebar.write(f"👤 **{username}**")

    if st.sidebar.button("🚪 Logout", type="secondary"):
        st.session_state.user = None
       #st.rerun()