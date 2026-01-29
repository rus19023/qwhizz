# core/logic.py
import streamlit as st
    

def flip_card():
    #st.write("DEBUG: flip_card called")  # Debug line
    #st.write(f"DEBUG: show_answer before: {st.session_state.show_answer}")  # Debug
    st.session_state.show_answer = not st.session_state.show_answer
    #st.write(f"DEBUG: show_answer after: {st.session_state.show_answer}")  # Debug


def next_card():
    #st.write("DEBUG: next_card called")  # Debug line
    st.session_state.index = (st.session_state.index + 1) % len(st.session_state.cards)
    st.session_state.show_answer = False