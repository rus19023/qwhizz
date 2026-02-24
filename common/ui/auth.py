import streamlit as st
from data.user_store import get_user, create_user


def handle_authentication() -> str:
    """
    Renders auth UI in the sidebar when not logged in.
    Returns the logged-in username.
    Stops the app when user is not logged in.
    """
    # Initialize
    if "user" not in st.session_state:
        st.session_state.user = None

    # If already logged in, show sidebar + return
    if st.session_state.user:
        show_user_sidebar(st.session_state.user)
        return st.session_state.user

    # Not logged in: show auth UI (sidebar)
    st.sidebar.header(st.secrets["app"].get("title", "QWhizz"))
    subtitle = st.secrets["app"].get("subtitle", "")
    subheader = st.secrets["app"].get("subheader", "")
    if subtitle:
        st.sidebar.subheader(subtitle)
    if subheader:
        st.sidebar.caption(subheader)

    auth_mode = st.sidebar.radio("Select Action", ["Login", "Register"], key="auth_mode")

    if auth_mode == "Login":
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login", type="primary"):
            username = (username or "").strip()
            password = (password or "").strip()

            if not username or not password:
                st.sidebar.error("Please enter username and password")
            else:
                user = get_user(username)
                if user and user.get("password") == password:
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password")

    else:  # Register
        new_username = st.sidebar.text_input("Choose Username", key="reg_username")
        new_password = st.sidebar.text_input("Choose Password", type="password", key="reg_password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="reg_confirm")

        if st.sidebar.button("Register", type="primary"):
            new_username = (new_username or "").strip()
            new_password = (new_password or "").strip()

            if not new_username or not new_password:
                st.sidebar.error("Please fill all fields")
            elif new_password != confirm_password:
                st.sidebar.error("Passwords don't match")
            elif get_user(new_username):
                st.sidebar.error("Username already exists")
            else:
                create_user(new_username, new_password)
                st.sidebar.success("User created! Switch to Login to continue.")

    # Main panel message + stop the app here
    st.info("Please login or register in the sidebar to continue.")
    st.stop()


def show_user_sidebar(username: str) -> None:
    st.sidebar.write(f"👤 **{username}**")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()