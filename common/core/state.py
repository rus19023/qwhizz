# core/state.py
import random
import streamlit as st


INDEX_KEYS = ("current_card_index", "index")


def reset_study_state_on_mode_change(study_mode: str) -> None:
    if "last_study_mode" not in st.session_state:
        st.session_state.last_study_mode = study_mode
        return

    if st.session_state.last_study_mode != study_mode:
        st.session_state.last_study_mode = study_mode

        # Reset any known index keys so older code paths still behave
        for k in INDEX_KEYS:
            st.session_state[k] = 0

        st.session_state.show_answer = False
        
        for key in [
            "mc_options","mc_correct_index","mc_card_id","mc_answered","mc_user_answer",
            "ms_options","ms_correct_indices","ms_card_id","ms_answered","ms_user_answer",
            "tf_generated","tf_card_id","tf_answered","tf_user_answer","tf_correct",
            "quiz_answered","quiz_user_answer","quiz_similarity",
            "committed",
        ]:
            st.session_state.pop(key, None)


def init_state(cards, deck_name: str | None = None):
    """
    Initialize study state. Re-initializes when deck changes.
    """
    # Re-init if deck changed
    if deck_name is not None and st.session_state.get("active_deck") != deck_name:
        st.session_state.active_deck = deck_name
        st.session_state.cards = list(cards)
        random.shuffle(st.session_state.cards)
        st.session_state.current_card_index = 0
        st.session_state.show_answer = False
        return

    # First-time init
    if "cards" not in st.session_state:
        st.session_state.cards = list(cards)
        random.shuffle(st.session_state.cards)

    if "current_card_index" not in st.session_state:
        st.session_state.current_card_index = 0

    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False


def sync_index_keys() -> None:
    """
    Optional helper: call this after any action that changes index.
    Ensures index and current_card_index always match.
    """
    if "current_card_index" in st.session_state:
        st.session_state.index = st.session_state.current_card_index
    elif "index" in st.session_state:
        st.session_state.current_card_index = st.session_state.index