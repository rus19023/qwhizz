# ui/auth.py

import streamlit as st
from data.user_store import get_user, create_user
from streamlit_cookies_manager import EncryptedCookieManager


cookies = EncryptedCookieManager(
    prefix="qwhizz_",
    password=st.secrets["app"]["cookie_password"],
)

if not cookies.ready():
    st.stop()


def handle_authentication() -> str:
    """
    Renders auth UI in the when not logged in.
    Returns the logged-in username.
    Stops the app when user is not logged in.
    """
    if "user" not in st.session_state:
        st.session_state.user = None

    # If already logged in, show + return
    if st.session_state.user:
        show_user(st.session_state.user)
        return st.session_state.user

    # Restore from cookie
    cookie_user = (cookies.get("user") or "").strip()
    if not st.session_state.user and cookie_user:
        st.session_state.user = cookie_user
        st.rerun()

    # Header
    st.header(st.secrets["app"].get("title", "QWhizz"))
    subtitle = st.secrets["app"].get("subtitle", "")
    subheader = st.secrets["app"].get("subheader", "")
    if subtitle:
        st.subheader(subtitle)
    if subheader:
        st.caption(subheader)

    auth_mode = st.radio("Select Action", ["Login", "Register"], key="auth_mode")

    # ── Login ─────────────────────────────────────────────────────────────────
    if auth_mode == "Login":
        with st.form("login_form"):
            username  = st.text_input("Username", key="login_username")
            password  = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            username = (username or "").strip()
            password = (password or "").strip()
            if not username or not password:
                st.error("Please enter username and password")
            else:
                user = get_user(username)
                if user and user.get("password") == password:
                    st.session_state.user = username
                    cookies["user"] = username
                    cookies.save()
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    # ── Register ──────────────────────────────────────────────────────────────
    else:
        with st.form("register_form"):
            new_username     = st.text_input("Username", key="reg_username")
            real_name        = st.text_input("Full Name", key="reg_real_name")
            email            = st.text_input("Email", key="reg_email")
            new_password     = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            submitted        = st.form_submit_button("Register", type="primary", use_container_width=True)

        if submitted:
            new_username = (new_username or "").strip()
            new_password = (new_password or "").strip()
            real_name    = (real_name or "").strip()
            email        = (email or "").strip()

            if not new_username or not new_password:
                st.error("Please fill all required fields")
            elif new_password != confirm_password:
                st.error("Passwords don't match")
            elif get_user(new_username):
                st.error("Username already taken")
            else:
                create_user(new_username, new_password, real_name=real_name, email=email)
                st.session_state.auth_mode = "Login"
                st.rerun()

    st.info("Please login or register to continue.")
    st.stop()


def show_user(username: str) -> None:
    """Show the logged-in user's name and logout button in the."""
    user    = get_user(username)
    display = user.get("real_name") or username if user else username
    st.write(f"👤 **{display}**")

    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.user = None
        cookies["user"] = ""
        cookies.save()
        st.rerun()