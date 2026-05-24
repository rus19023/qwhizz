#qwhizz.py

import sys
import traceback
from pathlib import Path

# ── Path setup — must come before any local imports ───────────────────────────
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# Page configuration MUST be first Streamlit call
st.set_page_config(
    page_title=st.secrets["app"]["title"],
    page_icon=st.secrets["app"]["icon"],
    layout=st.secrets["app"]["screen_width"],
    initial_sidebar_state="collapsed",   # sidebar now mostly empty — collapse it
)

if hasattr(st, "cache"):
    st.cache = st.cache_data

from theme_switcher import quick_theme_setup

from ui.router import TabSpec, render_tabs
from ui.styles import apply_global_css
from ui.layout import render_header
from ui.auth import handle_authentication
from ui.components import leaderboard, mode_selector
from ui.study_tab import render_study_tab
from ui.stats_tab import render_stats_tab
from ui.admin_tab import render_admin_tab
from ui.manage_tab import render_manage_tab, _render_user_access
from ui.add_card_tab import render_add_card_tab
from ui.add_deck_tab import render_add_deck_tab
from ui.ai_generate_tab import render_ai_generate_tab
from qwhizz_forge.app import render_forge_tab

from core.state import init_state, reset_study_state_on_mode_change
from data.deck_store import get_deck_names, get_deck, create_deck
from data.user_store import get_user, get_leaderboard


st.markdown("""
<style>
.main .block-container {
    max-width: 1200px;
    padding-left: 1rem;
    padding-right: 1rem;
}
</style>
""", unsafe_allow_html=True)


def render_top_controls(logged_in_user: str) -> tuple[str, str]:
    """
    Render deck selector + mode selector as a compact top row.
    Returns (deck_name, study_mode).
    Also shows user info + logout inline.
    """
    deck_names = get_deck_names()

    col_deck, col_mode, col_user = st.columns([2, 2, 1])

    with col_deck:
        if not deck_names:
            st.warning("No decks yet.")
            new_deck = st.text_input("Create first deck:", key="new_deck_name")
            if st.button("Create", type="primary", key="create_first_deck"):
                try:
                    create_deck(new_deck)
                    st.toast(f"✅ Created deck: {new_deck.strip()}", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            st.stop()

        deck_name = st.selectbox(
            "Deck",
            options=deck_names,
            index=len(deck_names) - 1,
            key="top_deck_select",
            label_visibility="collapsed",
        )

    with col_mode:
        study_mode = mode_selector(inline=True)

    with col_user:
        st.markdown(
            f"<div style='text-align:right;padding-top:6px;font-size:0.85em'>"
            f"👤 {logged_in_user}</div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪", key="top_logout", help="Logout", use_container_width=True):
            st.query_params.clear()
            st.rerun()

    return deck_name, study_mode


def main() -> None:
    apply_global_css()
    quick_theme_setup(default_theme=st.secrets["app"]["theme"])

    logged_in_user = handle_authentication()
    render_header()

    deck_name, study_mode = render_top_controls(logged_in_user)

    reset_study_state_on_mode_change(study_mode)

    current_user = get_user(logged_in_user)
    if not current_user:
        st.error("User not found")
        st.stop()

    is_admin = bool(current_user.get("is_admin", False))

    main_tabs = [
        TabSpec("📚 Study",        lambda: render_study_tab(get_deck(deck_name), deck_name, logged_in_user, study_mode, init_state)),
        TabSpec("📊 Stats",        lambda: render_stats_tab(current_user)),
        TabSpec("🏆 Leaderboard",  lambda: leaderboard(get_leaderboard(limit=10))),
        TabSpec("🛡️ Admin",        lambda: render_admin_tab(),                          admin_only=True),
        TabSpec("🔨 Forge",        lambda: render_forge_tab(deck_name, logged_in_user), admin_only=True),
        TabSpec("🗂️ Manage Decks", lambda: render_manage_tab(username=logged_in_user),  admin_only=True),
        TabSpec("🤖 AI Generate",  lambda: render_ai_generate_tab(),                    admin_only=True),
        TabSpec("👥 User Access",  lambda: _render_user_access(logged_in_user),         admin_only=True),
    ]
    render_tabs(main_tabs, is_admin=is_admin)


if __name__ == "__main__":
    main()