# core/flashcard_logic.py
import streamlit as st

def flip_card():
    st.session_state.show_answer = not st.session_state.get("show_answer", False)

def next_card():
    cards = st.session_state.get("cards", [])
    if not cards:
        return
    st.session_state.current_card_index = (st.session_state.get("current_card_index", 0) + 1) % len(cards)
    st.session_state.show_answer = False