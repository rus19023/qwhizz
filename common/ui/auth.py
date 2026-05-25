import streamlit as st
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from data.user_store import get_user, create_user
from streamlit_cookies_manager import EncryptedCookieManager

# Session timeout (24 hours for cookie persistence)
SESSION_TIMEOUT_MINUTES = 24 * 60


def init_cookies() -> EncryptedCookieManager:
    """Initialize cookies with app-level password."""
    cookies = EncryptedCookieManager(
        prefix="qwhizz_",
        password=st.secrets["app"]["cookie_password"],
    )
    if not cookies.ready():
        st.stop()
    return cookies


def init_session() -> None:
    """Initialize session state with unique session ID and timeout tracking."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.session_start = datetime.now()
    
    if "user" not in st.session_state:
        st.session_state.user = None
    
    if "user_token" not in st.session_state:
        st.session_state.user_token = None


def generate_token(username: str) -> str:
    """Generate a secure token for a user (includes timestamp salt)."""
    salt = str(datetime.now().timestamp())
    token = hmac.new(
        st.secrets["app"]["cookie_password"].encode(),
        f"{username}:{salt}".encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{token}:{salt}"


def validate_token(username: str, token: str) -> bool:
    """Validate a user token (check signature)."""
    try:
        stored_token, salt = token.split(":")
        expected_token = hmac.new(
            st.secrets["app"]["cookie_password"].encode(),
            f"{username}:{salt}".encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(stored_token, expected_token)
    except (ValueError, AttributeError):
        return False


def is_session_expired() -> bool:
    """Check if the current session has timed out."""
    if "session_start" not in st.session_state:
        return True
    
    elapsed = datetime.now() - st.session_state.session_start
    return elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


def invalidate_session() -> None:
    """Clear all user session data."""
    cookies = init_cookies()
    st.session_state.user = None
    st.session_state.user_token = None
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_start = datetime.now()
    cookies["user"] = ""
    cookies["token"] = ""
    cookies.save()


def is_mobile() -> bool:
    """Check if viewing on mobile via query parameter."""
    return st.query_params.get("mobile", ["false"])[0].lower() == "true"


def handle_authentication() -> str:
    """
    Handles authentication flow with mobile-aware UI.
    Returns the logged-in username.
    Stops the app if user is not logged in or session expired.
    
    - Desktop: sidebar auth
    - Mobile: main screen auth
    """
    # Auto-detect mobile and redirect if needed
    st.markdown("""
        <script>
            const isMobile = window.innerWidth < 768;
            const urlParams = new URLSearchParams(window.location.search);
            if (isMobile && !urlParams.has('mobile')) {
                window.location.search = '?mobile=true';
            } else if (!isMobile && urlParams.has('mobile')) {
                window.location.search = '';
            }
        </script>
    """, unsafe_allow_html=True)
    
    cookies = init_cookies()
    init_session()
    
    # Check for session timeout
    if st.session_state.user and is_session_expired():
        invalidate_session()
        st.warning("Your session has expired. Please log in again.")
        st.stop()
    
    # If already logged in in this session, show sidebar + return
    if st.session_state.user and st.session_state.user_token:
        show_user_sidebar(st.session_state.user)
        return st.session_state.user
    
    # Try to restore from cookie
    cookie_user = (cookies.get("user") or "").strip()
    cookie_token = (cookies.get("token") or "").strip()
    
    if cookie_user and cookie_token:
        # Validate the token (prevents cookie tampering)
        user_data = get_user(cookie_user)
        if user_data and validate_token(cookie_user, cookie_token):
            st.session_state.user = cookie_user
            st.session_state.user_token = cookie_token
            st.session_state.session_start = datetime.now()
            show_user_sidebar(st.session_state.user)
            return st.session_state.user
        else:
            # Token invalid or user doesn't exist: clear cookies
            cookies["user"] = ""
            cookies["token"] = ""
            cookies.save()

    # Not logged in: show auth UI
    st.header(st.secrets["app"].get("title", "QWhizz"))
    subtitle = st.secrets["app"].get("subtitle", "")
    subheader = st.secrets["app"].get("subheader", "")
    if subtitle:
        st.subheader(subtitle)
    if subheader:
        st.caption(subheader)

    mobile = is_mobile()

    if mobile:
        # Mobile: main screen layout
        auth_mode = st.radio("Select Action", ["Login", "Register"], key="auth_mode")

        if auth_mode == "Login":
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", type="primary", use_container_width=True):
                username = (username or "").strip()
                password = (password or "").strip()

                if not username or not password:
                    st.error("Please enter username and password")
                else:
                    user = get_user(username)
                    if user and user.get("password") == password:
                        token = generate_token(username)
                        st.session_state.user = username
                        st.session_state.user_token = token
                        st.session_state.session_start = datetime.now()
                        cookies["user"] = username
                        cookies["token"] = token
                        cookies.save()
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

        else:  # Register
            new_username = st.text_input("Choose Username", key="reg_username")
            new_password = st.text_input("Choose Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

            if st.button("Register", type="primary", use_container_width=True):
                new_username = (new_username or "").strip()
                new_password = (new_password or "").strip()

                if not new_username or not new_password:
                    st.error("Please fill all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                elif get_user(new_username):
                    st.error("Username already exists")
                else:
                    create_user(new_username, new_password)
                    st.success("User created! Switch to Login to continue.")

    else:
        # Desktop: sidebar layout
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
                        token = generate_token(username)
                        st.session_state.user = username
                        st.session_state.user_token = token
                        st.session_state.session_start = datetime.now()
                        cookies["user"] = username
                        cookies["token"] = token
                        cookies.save()
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

    st.info("Please login or register to continue.")
    st.stop()


def show_user_sidebar(username: str) -> None:
    """Display user info and logout button in sidebar."""
    if is_mobile():
        # Mobile: show in main area
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"👤 **{username}**")
        with col2:
            if st.button("🚪 Logout", key="logout_btn"):
                invalidate_session()
                st.rerun()
    else:
        # Desktop: show in sidebar
        st.sidebar.write(f"👤 **{username}**")
        
        if "session_start" in st.session_state:
            elapsed = datetime.now() - st.session_state.session_start
            remaining = SESSION_TIMEOUT_MINUTES - int(elapsed.total_seconds() / 60)
            if 0 < remaining <= 60:
                st.sidebar.info(f"Session expires in {remaining}m")

        if st.sidebar.button("🚪 Logout", key="logout_btn"):
            invalidate_session()
            st.rerun()