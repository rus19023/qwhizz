# ui/auth.py

import streamlit as st
from data.user_store import get_user, create_user


def handle_authentication():
    """
        Handle login/register in sidebar and return logged-in username or None
    """
    
    # Check query params for auto-login
    if "user" in st.query_params:
        username = st.query_params["user"]
        if get_user(username):
            return username
    
    st.sidebar.title("🧬 DNA Study")
    
    # Login/Register toggle
    auth_mode = st.sidebar.radio("", ["Login", "Register"])

    if auth_mode == "Login":
        username = st.sidebar.text_input(
            "Username",
            key="login_username"
        )
        password = st.sidebar.text_input(
                "Password", type="password",
                key="login_password"
            )
        
        if st.sidebar.button(
                "Login", 
                type="primary", 
                use_container_width=True
                ):
            if username.strip() and password.strip():
                user = get_user(username.strip())
                if user and user.get("password") == password:
                    # Set query param to persist login
                    st.query_params["user"] = username.strip()
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password")
            else:
                st.sidebar.error("Please enter username and password")

    else:  # Register
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
                ey="reg_confirm"
            )
        
        if st.sidebar.button(
                    "Register",
                    type="primary",
                    use_container_width=True
                ):
            if new_username.strip() and new_password.strip():
                if new_password != confirm_password:
                    st.sidebar.error("Passwords don't match")
                elif get_user(new_username.strip()):
                    st.sidebar.error("Username already exists")
                else:
                    create_user(new_username.strip(), new_password)
                    st.sidebar.success(
                        f"User '{new_username}' created! Please login."
                    )
            else:
                st.sidebar.error("Please fill all fields")
 
    return None


def show_user_sidebar(username):
    """Show logged-in user info and logout button"""
    st.sidebar.write(f"👤 **{username}**")
  
    if st.sidebar.button(
                "🚪 Logout", 
                use_container_width=True,
                type="secondary"
            ):
        # Clear query param
        st.query_params.clear()
        st.rerun()