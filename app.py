import streamlit as st

# Page configuration MUST be first
st.set_page_config(
    page_title="🧬 DNA Study Gamified",
    page_icon="🧬🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme setup (package handles its own paths automatically)
from theme_switcher import quick_theme_setup
quick_theme_setup(default_theme='retro')

# Core functionality
from core.state import init_state
from core.scoring import calculate_points

# UI components
from ui.layout import render_header
from ui.auth import handle_authentication, show_user_sidebar
from ui.components import leaderboard, mode_selector
from ui.study_tab import render_study_tab
from ui.stats_tab import render_stats_tab
from ui.add_card_tab import render_add_card_tab
from ui.manage_tab import render_manage_tab
from ui.admin_tab import render_admin_tab

# Data stores
from data.deck_store import get_deck_names, get_deck
from data.user_store import get_user, get_leaderboard

# ----------------------------
# Authentication
# ----------------------------
logged_in_user = handle_authentication()

if not logged_in_user:
    #st.title("🧬 Flashcard Study Mode")
    st.info("Please login or register in the sidebar to continue.")
    st.stop()

# Render header after login
render_header()

# Show user info in sidebar
show_user_sidebar(logged_in_user)

# Study mode selector
study_mode = mode_selector()

# Deck selection
deck_names = get_deck_names()
if not deck_names:
    st.error("No decks found in database.")
    st.stop()

deck_name = st.sidebar.selectbox("Choose a deck", options=deck_names)

# ----------------------------
# Main Page
# ----------------------------
st.header(study_mode)

current_user = get_user(logged_in_user)

if not current_user:
    st.error("User not found")
    st.stop()

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
