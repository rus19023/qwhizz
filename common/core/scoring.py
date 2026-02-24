# core/scoring.py

import streamlit as st


BASE_POINTS = 10
STREAK_BONUS = 5
WRONG_PENALTY = -3


def calculate_points(correct):
    """Calculate points for an answer"""
    if correct:
        streak = st.session_state.get("current_streak", 0)
        return BASE_POINTS + (streak * STREAK_BONUS)
    else:
        return WRONG_PENALTY
    
