#qwhizz.py

import traceback
import streamlit as st

# Page configuration MUST be first
st.set_page_config(
    page_title=st.secrets["app"]["title"],
    page_icon=st.secrets["app"]["icon"],
    layout=st.secrets["app"]["screen_width"],
    initial_sidebar_state=st.secrets["app"]["start_sidebar_state"]
)

from theme_switcher import quick_theme_setup
from ui.styles import apply_global_css
from ui.layout import render_header
from ui.auth import handle_authentication, show_user_sidebar
from ui.components import leaderboard, mode_selector
from ui.study_tab import render_study_tab
from ui.stats_tab import render_stats_tab
from ui.admin_tab import render_admin_tab
from ui.manage_tab import render_manage_tab
from ui.add_card_tab import render_add_card_tab
from ui.router import TabSpec, render_tabs

from core.state import init_state, reset_study_state_on_mode_change
from data.deck_store import get_deck_names, get_deck, create_deck
from data.user_store import get_user, get_leaderboard


def require_deck_selection() -> str:
    deck_names = get_deck_names()

    if not deck_names:
        st.sidebar.warning("No decks found yet. Create your first deck:")
        new_deck = st.sidebar.text_input("New deck name", key="new_deck_name")

        if st.sidebar.button("Create deck", type="primary"):
            try:
                create_deck(new_deck)
                st.success(f"Created deck: {new_deck.strip()}")
                st.rerun()
            except Exception as e:
                st.sidebar.error(str(e))

        st.stop()

    return st.sidebar.selectbox("Choose a deck", options=deck_names)


def main() -> None:
    apply_global_css()
    quick_theme_setup(default_theme=st.secrets["app"]["theme"])

    logged_in_user = handle_authentication()
    render_header()

    study_mode = mode_selector()
    reset_study_state_on_mode_change(study_mode)

    deck_name = require_deck_selection()

    st.header(study_mode)

    current_user = get_user(logged_in_user)
    if not current_user:
        st.error("User not found")
        st.stop()

    
    is_admin = bool(current_user.get("is_admin", False))

    tabs = [
        TabSpec(
            "📚 Study",
            lambda: render_study_tab(get_deck(deck_name), deck_name, logged_in_user, study_mode, init_state)
        ),
        TabSpec("📊 Stats", lambda: render_stats_tab(current_user)),
        TabSpec("🏆 Leaderboard", lambda: leaderboard(get_leaderboard(limit=10))),
        TabSpec("🛡️ Admin", lambda: render_admin_tab(), admin_only=True),
        TabSpec("🗂️ Manage Decks", lambda: render_manage_tab(), admin_only=True),
        TabSpec("➕ Add Card", lambda: render_add_card_tab(), admin_only=True),
    ]

    render_tabs(tabs, is_admin=is_admin)


if __name__ == "__main__":
    main()