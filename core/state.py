# core/state.py
import streamlit as st
import random


def init_state(cards):
    # Use deck name from selectbox as the stable identifier, not id(cards)
    if "cards" not in st.session_state:
        st.session_state.cards = list(cards)
        random.shuffle(st.session_state.cards)
        st.session_state.index = 0
        st.session_state.show_answer = False