# ui/study_tab.py

import streamlit as st
import time
import random
from core.study_modes import get_mode_config
from core.scoring import calculate_points
from core.answer_checking import check_answer
from ui.components import (
    flashcard_box, controls, answer_buttons, commit_buttons,
    quiz_input, timer_display
)
from data.user_store import update_user_score, log_study_session


def render_study_tab(cards, deck_name, username, study_mode, init_state_func):
    """Render the study flashcards tab"""
    
    if not cards:
        st.warning(f"The deck is empty. Add some cards in the 'Add Card' tab!")
        return
    
    init_state_func(cards)
    mode_config = get_mode_config(study_mode)
    
    # Initialize session variables
    if "session_streak" not in st.session_state:
        st.session_state.session_streak = 0
    if "card_start_time" not in st.session_state:
        st.session_state.card_start_time = time.time()
    if "committed_answer" not in st.session_state:
        st.session_state.committed_answer = None
    if "is_verification" not in st.session_state:
        st.session_state.is_verification = random.random() < mode_config["verification_rate"]

    card = st.session_state.cards[st.session_state.index]
    
    # Show verification badge
    if st.session_state.is_verification:
        st.info("🔍 This is a verification question - answer will be checked!")
    
    # Display question
    if not st.session_state.show_answer:
        flashcard_box(card["question"])
        
        if mode_config["requires_commit"]:
            _handle_commit_mode()
        elif mode_config["requires_typing"] or st.session_state.is_verification:
            _handle_quiz_mode(card, deck_name, username, study_mode)
        else:
            controls()
    else:
        _handle_answer_display(card, deck_name, username, study_mode, mode_config)

    st.write(f"Card {st.session_state.index + 1} of {len(st.session_state.cards)}")
    st.write(f"Session Streak: {st.session_state.session_streak} 🔥")


def _handle_commit_mode():
    """Handle commit-before-reveal mode"""
    if st.session_state.committed_answer is None:
        def commit_know():
            st.session_state.committed_answer = True
            st.session_state.card_start_time = time.time()
        
        def commit_dont_know():
            st.session_state.committed_answer = False
            st.session_state.show_answer = True
        
        commit_buttons(on_know=commit_know, on_dont_know=commit_dont_know)
    else:
        if st.button("🔄 Reveal Answer", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()


def _handle_quiz_mode(card, deck_name, username, study_mode):
    """Handle quiz/typing mode"""
    def handle_quiz_submit(user_answer):
        response_time = time.time() - st.session_state.card_start_time
        is_correct, similarity = check_answer(user_answer, card["answer"])
        
        points = calculate_points(is_correct)
        update_user_score(username, points, correct=is_correct, verified=st.session_state.is_verification)
        log_study_session(username, deck_name, card["question"], response_time, is_correct, study_mode)
        
        st.session_state.session_streak = st.session_state.session_streak + 1 if is_correct else 0
        st.session_state.quiz_result = {"correct": is_correct, "similarity": similarity, "user_answer": user_answer}
        st.session_state.show_answer = True
    
    quiz_input(on_submit=handle_quiz_submit)


def _handle_answer_display(card, deck_name, username, study_mode, mode_config):
    """Handle answer display and scoring"""
    flashcard_box(card["answer"])
    
    if "quiz_result" in st.session_state:
        _show_quiz_result()
    elif mode_config["requires_commit"]:
        _handle_commit_verification(card, deck_name, username, study_mode, mode_config)
    else:
        _handle_regular_mode(card, deck_name, username, study_mode)


def _show_quiz_result():
    """Show quiz mode results"""
    result = st.session_state.quiz_result
    if result["correct"]:
        st.success(f"✓ Correct! (Match: {result['similarity']*100:.0f}%)")
    else:
        st.error(f"✗ Incorrect. You answered: {result['user_answer']}")
    
    if st.button("➡️ Next Card", use_container_width=True):
        _next_card()


def _handle_commit_verification(card, deck_name, username, study_mode, mode_config):
    """Handle commit mode verification"""
    elapsed = time.time() - st.session_state.card_start_time
    can_answer = elapsed >= mode_config["min_delay"]
    
    if not can_answer:
        timer_display(st.session_state.card_start_time, mode_config["min_delay"])
    
    if st.session_state.committed_answer:
        st.info("✓ You said you knew this - were you right?")
    else:
        st.warning("✗ You said you didn't know this")
    
    def handle_was_correct():
        _record_answer(card, deck_name, username, study_mode, st.session_state.committed_answer)
        _next_card()
    
    def handle_was_incorrect():
        _record_answer(card, deck_name, username, study_mode, False)
        _next_card()
    
    answer_buttons(on_correct=handle_was_correct, on_incorrect=handle_was_incorrect, disabled=not can_answer)


def _handle_regular_mode(card, deck_name, username, study_mode):
    """Handle regular flashcard mode"""
    def handle_correct():
        _record_answer(card, deck_name, username, study_mode, True)
        _next_card()
    
    def handle_incorrect():
        _record_answer(card, deck_name, username, study_mode, False)
        _next_card()
    
    answer_buttons(on_correct=handle_correct, on_incorrect=handle_incorrect)


def _record_answer(card, deck_name, username, study_mode, correct):
    """Record answer and update score"""
    response_time = time.time() - st.session_state.card_start_time
    points = calculate_points(correct)
    update_user_score(username, points, correct=correct, verified=st.session_state.is_verification)
    log_study_session(username, deck_name, card["question"], response_time, correct, study_mode)
    
    if correct:
        st.session_state.session_streak += 1
    else:
        st.session_state.session_streak = 0


def _next_card():
    """Move to next card and reset state"""
    st.session_state.index = (st.session_state.index + 1) % len(
        st.session_state.cards)
    st.session_state.show_answer = False
    st.session_state.card_start_time = time.time()
    st.session_state.committed_answer = None
    from core.study_modes import get_mode_config, STUDY_MODES
    mode_key = st.session_state.get("study_mode", "flashcard")
    mode_config = get_mode_config(mode_key)
    st.session_state.is_verification = random.random() < mode_config[
        "verification_rate"]
    
    if "quiz_result" in st.session_state:
        del st.session_state.quiz_result
    st.rerun()