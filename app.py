import streamlit as st

from core.state import init_state
from core.scoring import calculate_points
from ui.layout import render_header
from ui.components import flashcard_box, controls, answer_buttons, user_stats, leaderboard

PAGE_TITLE = "🧬 DNA Study App"


from data.deck_store import (
    get_deck_names, 
    get_deck, 
    add_card,
    find_duplicate_cards,
    delete_card,
    get_all_cards_with_indices
)

from data.user_store import (
    get_user,
    create_user,
    update_user_score,
    get_leaderboard
)

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🧬",  # You can use an emoji or path to an image file
    layout="wide"  # Optional: makes the app use full width
)

render_header()
    
from core.state import init_state
from ui.auth import handle_authentication, show_user_sidebar
from ui.components import leaderboard, mode_selector
from ui.study_tab import render_study_tab
from ui.stats_tab import render_stats_tab
from ui.add_card_tab import render_add_card_tab
from ui.manage_tab import render_manage_tab
from ui.admin_tab import render_admin_tab
from data.deck_store import get_deck_names, get_deck
from data.user_store import get_user, get_leaderboard


# ----------------------------
# Authentication
# ----------------------------
logged_in_user = handle_authentication()


# ----------------------------
# Sidebar: User Login/Registration
# ----------------------------
#st.sidebar.title("🧬 Flashcard Study")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# Show login/register only if NOT logged in
if not st.session_state.logged_in_user:
    # Login/Register toggle
    auth_mode = st.sidebar.radio("", ["Login", "Register"])

    if auth_mode == "Login":
        username = st.sidebar.text_input("Username", key="login_username", value="fff")
        password = st.sidebar.text_input("Password", type="password", key="login_password",value="dragon")
        
        if st.sidebar.button("Login"):
            if username.strip() and password.strip():
                user = get_user(username.strip())
                if user and user.get("password") == password:
                    st.session_state.logged_in_user = username.strip()
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password")
            else:
                st.sidebar.error("Please enter username and password")

    else:  # Register
        new_username = st.sidebar.text_input("Choose Username", label="username", key="reg_username")
        new_password = st.sidebar.text_input("Choose Password", label="password", type="password", key="reg_password")
        confirm_password = st.sidebar.text_input("Confirm Password", label="password2", type="password", key="reg_confirm")
        
        if st.sidebar.button("Register"):
            if new_username.strip() and new_password.strip():
                if new_password != confirm_password:
                    st.sidebar.error("Passwords don't match")
                elif get_user(new_username.strip()):
                    st.sidebar.error("Username already exists")
                else:
                    create_user(new_username.strip(), new_password)
                    st.sidebar.success(f"User '{new_username}' created! Please login.")
            else:
                st.sidebar.error("Please fill all fields")


    # Stop if not logged in
    # st.title("🧬 Flashcard Study App")
    st.info("Please login or register to continue.")
    st.stop()

# Show logout and deck selection only if logged in
else:
    st.sidebar.write(f"👤 Logged in as: **{st.session_state.logged_in_user}**")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()



# Study mode selector
study_mode = mode_selector()
st.sidebar.divider()


# Deck selection
deck_names = get_deck_names()
if not deck_names:
    st.error("No decks found in database.")
    st.stop()

deck_name = st.sidebar.selectbox("Choose a deck", options=deck_names)
st.sidebar.divider()






# ----------------------------
# Main Page
# ----------------------------
st.title("🧬 Flashcard Study App")

current_user = get_user(logged_in_user)

if not current_user:
    st.error("User not found")
    st.stop()
    if "cards" in st.session_state:
        del st.session_state.cards


cards = get_deck(deck_name)


# ----------------------------
# Tabs
# ----------------------------
tabs = ["📚 Study", "📊 Stats", "🏆 Leaderboard", "➕ Add Card", "🗂️ Manage Decks"]
if current_user.get("is_admin", False):
    tabs.append("🛡️ Admin")

tab_objects = st.tabs(tabs)


# Tab 1: Study
with tab_objects[0]:
    render_study_tab(cards, deck_name, logged_in_user, study_mode, init_state)

# Tab 2: Stats
with tab_objects[1]:
    render_stats_tab(current_user)

# Tab 3: Leaderboard
with tab_objects[2]:

    top_users = get_leaderboard(limit=10)
    leaderboard(top_users)

# Tab 4: Add Card
with tab_objects[3]:
    render_add_card_tab()


# Tab 5: Manage Decks
with tab_objects[4]:
    render_manage_tab()

# Tab 6: Admin (if user is admin)
if current_user.get("is_admin", False):
    with tab_objects[5]:
        render_admin_tab()



    
    # st.title("Test 1: Streamlit works!")
    # st.write("If you see this, basic Streamlit is working.")


try:
    # st.set_page_config(
    #     page_title="Debug Test",
    #     page_icon="🧬",
    # )
    
    # Test MongoDB secrets
    st.write("Test 2: Checking secrets...")
    if "mongo" in st.secrets:
        st.success("✓ MongoDB secrets found")
        st.write(f"URI starts with: {st.secrets['mongo']['uri'][:20]}...")
    else:
        st.error("✗ MongoDB secrets missing!")
    
    # Test MongoDB connection
    st.write("Test 3: Connecting to MongoDB...")
    from pymongo import MongoClient
    client = MongoClient(st.secrets["mongo"]["uri"])
    db = client[st.secrets["mongo"]["db_name"]]
    count = db.users.count_documents({})
    st.success(f"✓ MongoDB connected! Found {count} users")
    
except Exception as e:
    import traceback
    st.error("CRASH ERROR:")
    st.code(traceback.format_exc())










