import os
import sys
from pathlib import Path
import streamlit as st
import pymongo
import subprocess
token = st.secrets["GITHUB_TOKEN"]
subprocess.run([f"pip install git+https://{token}@github.com/rus19023/theme_switcher.git"], shell=True)


# Page configuration MUST be first
st.set_page_config(
    page_title="Study Gamified",
    page_icon="🗝🗝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force sidebar to always be visible
st.markdown("""
<style>
/* Force sidebar open */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: translateX(0) !important;
    margin-left: 0 !important;
}

/* Make toggle button visible */
button[kind="header"],
[data-testid="collapsedControl"] {
    background: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #000000 !important;
    padding: 8px !important;
    visibility: visible !important;
    display: block !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}
</style>
""", unsafe_allow_html=True)


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


from theme_switcher import quick_theme_setup

quick_theme_setup(default_theme='retro')
#quick_theme_setup(default_theme='dragons')


# ----------------------------
# Authentication
# ----------------------------
logged_in_user = handle_authentication()


if not logged_in_user:
    #st.title("🧬 Flashcard Study Mode")
    st.info("Please login or register in the sidebar to continue.")
    st.rerun()

# Render header after login
render_header()

# Show user info in sidebar
show_user_sidebar(logged_in_user)

# Study mode selector
# Line ~50 - after study_mode = mode_selector()
study_mode = mode_selector()

# Reset card state when mode changes
if 'last_study_mode' not in st.session_state:
    st.session_state.last_study_mode = study_mode

if st.session_state.last_study_mode != study_mode:
    # Mode changed - reset card state
    st.session_state.last_study_mode = study_mode
    if 'current_card_index' in st.session_state:
        st.session_state.current_card_index = 0
    if 'show_answer' in st.session_state:
        st.session_state.show_answer = False
    st.rerun()
    
# Deck selection
deck_names = get_deck_names()

if not deck_names:
    st.sidebar.warning("No decks found yet. Create your first deck:")
    new_deck = st.sidebar.text_input("New deck name", key="new_deck_name")
    if st.sidebar.button("Create deck", type="primary"):
        from data.db import get_database
        db = get_database()
        db.decks.update_one({"_id": new_deck.strip()}, {"$set": {"cards": []}}, upsert=True)
        st.rerun()
    st.stop()

deck_name = st.sidebar.selectbox("Choose a deck", options=deck_names)


# ----------------------------
# Main Page
# ----------------------------
st.header(study_mode)

current_user = get_user(logged_in_user)

if not current_user:
    st.error("User not found")
    st.rerun()

cards = get_deck(deck_name)

# ----------------------------
# Tabs
# ----------------------------
# ----------------------------
# Tabs
# ----------------------------
tabs = ["📚 Study", "📊 Stats", "🏆 Leaderboard"]

is_admin = current_user.get("is_admin", False)
if is_admin:
    tabs += ["🛡️ Admin", "🗂️ Manage Decks", "➕ Add Card"]

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

# Admin-only tabs
if is_admin:
    with tab_objects[3]:
        render_admin_tab()

    with tab_objects[4]:
        render_manage_tab()

    with tab_objects[5]:
        render_add_card_tab()
