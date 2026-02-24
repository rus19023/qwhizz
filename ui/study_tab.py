# ui/study_tab.py

import streamlit as st
import random
from core.study_modes import get_mode_config, is_game_mode
from core.game_mode_logic import (
    generate_multiple_choice_options,
    generate_multi_select_options,
    check_multiple_choice_answer,
    check_multi_select_answer,
    check_true_false_answer,
    check_typed_answer
)
from ui.components import (
    flashcard_box,
    controls,
    answer_buttons,
    commit_buttons,
    quiz_input,
    multiple_choice_buttons,
    multi_select_checkboxes,
    true_false_buttons,
    display_question_with_image,
    points_info,
    user_stats
)
from data.card_format import get_card_type
from data.user_store import update_user_score
from data.ponder_store import submit_ponder_response, get_user_response_for_card
from core.quiz_generator import generate_true_false_statement


def render_study_tab(cards, deck_name, username, study_mode, init_state):
    """
    Main study tab rendering function
    
    Args:
        cards: List of flashcard dicts
        deck_name: Name of current deck
        username: Logged in username
        study_mode: Current study mode key
        init_state: Function to initialize session state
    """
    
    if not cards:
        st.warning("No cards in this deck. Add some cards to get started!")
        return
    
    # Initialize state
    init_state(cards, deck_name=deck_name)

    # Canonical card list + index
    session_cards = st.session_state.cards
    current_idx = st.session_state.get("current_card_index", 0) % len(session_cards)
    st.session_state.current_card_index = current_idx
    current_card = session_cards[current_idx]

    card_type = get_card_type(current_card)
    
    if card_type == "essay":
        render_essay_mode(current_card, username)
        return

    
    # Get mode configuration
    mode_config = get_mode_config(study_mode)
    st.caption(mode_config.get("description", ""))
    
    # Display points info
    points_info()
    
    # Progress bar
    st.progress((current_idx + 1) / len(session_cards))
    st.caption(f"Card {current_idx + 1} of {len(session_cards)}")

    # === ROUTE TO APPROPRIATE STUDY MODE ===
    
    if card_type == "ponder":
        render_ponder_mode(current_card, current_idx, deck_name, username)
        return

    if study_mode == "flashcard":
        render_flashcard_mode(current_card, username)
    
    elif study_mode == "multiple_choice":
        render_multiple_choice_mode(current_card, session_cards, username)
    
    elif study_mode == "multi_select":
        render_multi_select_mode(current_card, session_cards, username)
    
    elif study_mode == "true_false":
        render_true_false_mode(current_card, username)
    
    elif study_mode == "quiz":
        render_quiz_mode(current_card, username)
    
    elif study_mode == "commit":
        render_commit_mode(current_card, username)
    
    elif study_mode == "hardcore":
        render_hardcore_mode(current_card, username)
    
    else:
        st.error(f"Unknown study mode: {study_mode}")


# ============================================================================
# MODE RENDERERS
# ============================================================================

def render_flashcard_mode(card, username):
    """Traditional flashcard with flip"""
    
    # Display question (with optional image)
    image_url = card.get("image_url")
    if image_url:
        display_question_with_image(card["question"], image_url)
    else:
        flashcard_box(card["question"])
    
    # Show answer if flipped
    if st.session_state.get("show_answer", False):
        st.success("**Answer:**")
        flashcard_box(card["answer"])
        
        # Answer buttons
        answer_buttons(
            on_correct=lambda: handle_answer(True, username),
            on_incorrect=lambda: handle_answer(False, username)
        )
    else:
        # Control buttons
        controls()


def render_multiple_choice_mode(card, all_cards, username):
    """Multiple choice mode (single correct answer)"""
    
    # Initialize game state for this card if needed
    if "mc_options" not in st.session_state or st.session_state.get("mc_card_id") != id(card):
        options, correct_idx = generate_multiple_choice_options(card, all_cards, num_options=4)
        st.session_state.mc_options = options
        st.session_state.mc_correct_index = correct_idx
        st.session_state.mc_card_id = id(card)
        st.session_state.mc_answered = False
        st.session_state.mc_user_answer = None
    
    # Display question
    image_url = card.get("image_url")
    if image_url:
        display_question_with_image(card["question"], image_url)
    else:
        st.markdown(f"### {card['question']}")
    
    # Show options
    def on_answer(selected_idx):
        st.session_state.mc_user_answer = selected_idx
        st.session_state.mc_answered = True
        is_correct = check_multiple_choice_answer(
            st.session_state.mc_correct_index,
            selected_idx
        )
        handle_answer(is_correct, username)
    
    multiple_choice_buttons(
        options=st.session_state.mc_options,
        on_answer=on_answer,
        correct_index=st.session_state.mc_correct_index if st.session_state.mc_answered else None,
        show_result=st.session_state.mc_answered
    )
    
    # Show result and next button
    if st.session_state.mc_answered:
        if st.session_state.mc_user_answer == st.session_state.mc_correct_index:
            st.success("✓ Correct!")
        else:
            st.error(f"✗ Incorrect. The correct answer was: {st.session_state.mc_options[st.session_state.mc_correct_index]}")
        
        st.info(f"**Full answer:** {card['answer']}")
        
        if st.button("Next Card →", key="mc_next", type="primary"):
            advance_to_next_card()


def render_multi_select_mode(card, all_cards, username):
    """Multi-select mode (multiple correct answers)"""
    
    # Initialize game state
    if "ms_options" not in st.session_state or st.session_state.get("ms_card_id") != id(card):
        options, correct_indices = generate_multi_select_options(card, all_cards, num_options=6)
        
        # Fallback if card doesn't have multi-select data
        if not options:
            st.warning("This card doesn't have multi-select data. Using flashcard mode instead.")
            render_flashcard_mode(card, username)
            return
        
        st.session_state.ms_options = options
        st.session_state.ms_correct_indices = correct_indices
        st.session_state.ms_card_id = id(card)
        st.session_state.ms_answered = False
        st.session_state.ms_user_answer = None
    
    # Display question
    image_url = card.get("image_url")
    if image_url:
        display_question_with_image(card["question"], image_url)
    else:
        st.markdown(f"### {card['question']}")
    
    st.info(f"💡 Select exactly {len(st.session_state.ms_correct_indices)} correct answer(s)")
    
    # Show checkboxes
    def on_submit(selected_indices):
        st.session_state.ms_user_answer = selected_indices
        st.session_state.ms_answered = True
        is_correct = check_multi_select_answer(
            st.session_state.ms_correct_indices,
            selected_indices
        )
        handle_answer(is_correct, username)
    
    multi_select_checkboxes(
        options=st.session_state.ms_options,
        on_submit=on_submit,
        correct_indices=st.session_state.ms_correct_indices if st.session_state.ms_answered else None,
        show_result=st.session_state.ms_answered
    )
    
    # Show result
    if st.session_state.ms_answered:
        if set(st.session_state.ms_user_answer) == set(st.session_state.ms_correct_indices):
            st.success("✓ Correct! You selected all the right answers.")
        else:
            st.error("✗ Incorrect selection.")
            correct_options = [st.session_state.ms_options[i] for i in st.session_state.ms_correct_indices]
            st.write(f"**Correct answers were:** {', '.join(correct_options)}")
        
        st.info(f"**Explanation:** {card['answer']}")
        
        if st.button("Next Card →", key="ms_next", type="primary"):
            advance_to_next_card()


def render_true_false_mode(card, username):
    """True/False mode"""

    # If this isn't a true/false card, generate one dynamically
    if get_card_type(card) != "true_false":
        if "tf_generated" not in st.session_state or st.session_state.get("tf_card_id") != id(card):
            is_true = random.random() > 0.5
            statement = generate_true_false_statement(
                card["question"],
                card["answer"],
                is_true=is_true
            )

            st.session_state.tf_generated = {
                "question": statement,
                "answer": card["answer"],
                "correct_answer": is_true
            }

        card = st.session_state.tf_generated

    # Initialize state
    if "tf_answered" not in st.session_state or st.session_state.get("tf_card_id") != id(card):
        st.session_state.tf_card_id = id(card)
        st.session_state.tf_answered = False
        st.session_state.tf_user_answer = None
        st.session_state.tf_correct = card["correct_answer"]

    # Display question
    st.markdown(f"### {card['question']}")

    def on_answer(user_answer):
        st.session_state.tf_user_answer = user_answer
        st.session_state.tf_answered = True
        is_correct = (user_answer == st.session_state.tf_correct)
        handle_answer(is_correct, username)

    true_false_buttons(
        on_answer=on_answer,
        correct_answer=st.session_state.tf_correct if st.session_state.tf_answered else None,
        show_result=st.session_state.tf_answered
    )

    if st.session_state.tf_answered:
        if st.session_state.tf_user_answer == st.session_state.tf_correct:
            st.success("✓ Correct!")
        else:
            st.error(
                f"✗ Incorrect. The correct answer was: "
                f"{'TRUE' if st.session_state.tf_correct else 'FALSE'}"
            )

        st.info(f"**Explanation:** {card['answer']}")

        if st.button("Next Card →", key="tf_next", type="primary"):
            advance_to_next_card()



def render_quiz_mode(card, username):
    """Quiz mode - type your answer"""
    
    # Display question
    image_url = card.get("image_url")
    if image_url:
        display_question_with_image(card["question"], image_url)
    else:
        flashcard_box(card["question"])
    
    # Show input or result
    if not st.session_state.get("quiz_answered", False):
        def on_submit(user_answer):
            is_correct, similarity = check_typed_answer(card["answer"], user_answer)
            st.session_state.quiz_answered = True
            st.session_state.quiz_user_answer = user_answer
            st.session_state.quiz_similarity = similarity
            handle_answer(is_correct, username)
        
        quiz_input(on_submit)
    else:
        st.write(f"**Your answer:** {st.session_state.quiz_user_answer}")
        st.write(f"**Correct answer:** {card['answer']}")
        st.write(f"**Similarity:** {st.session_state.quiz_similarity*100:.1f}%")
        
        if st.session_state.quiz_similarity >= 0.8:
            st.success("✓ Correct!")
        else:
            st.error("✗ Not quite right")
        
        if st.button("Next Card →", '', type="primary"):
            st.session_state.quiz_answered = False
            advance_to_next_card()


def render_commit_mode(card, username):
    """Commit mode - commit before seeing answer"""
    
    flashcard_box(card["question"])
    
    if not st.session_state.get("committed", False):
        commit_buttons(
            on_know=lambda: commit_answer(True, username),
            on_dont_know=lambda: commit_answer(False, username)
        )
    else:
        st.success("**Answer:**")
        flashcard_box(card["answer"])
        
        if st.button("Next Card →", ''):
            st.session_state.committed = False
            advance_to_next_card()


def render_hardcore_mode(card, username):
    """Hardcore mode - all features enabled"""
    # Similar to quiz + commit mode
    st.info("🔥 Hardcore Mode: Type your answer AND commit time!")
    render_quiz_mode(card, username)

def render_essay_mode(card, username):
    """Essay mode: user writes response, then can reveal rubric/expected points."""
    st.markdown(f"### {card['question']}")
    st.caption("✍️ Write your response below. This is self-graded (rubric shown after).")

    user_text = st.text_area("Your answer", key=f"essay_{id(card)}", height=180)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I wrote an answer", '', type="primary"):
            # Give participation points (optional). If you prefer no points, remove this.
            handle_answer(True, username)

    with col2:
        if st.button("Show rubric", ''):
            st.info(f"**Rubric / key ideas:** {card.get('answer', '')}")

    if st.button("Next Card →", ''):
        advance_to_next_card()




def render_ponder_mode(card, card_index, deck_name, username):
    """Ponder mode — reflection with optional sharing."""
    question = card.get("question", "")
    seed_thought = card.get("seed_thought", card.get("answer", ""))

    st.markdown(f"### {question}")

    if seed_thought:
        st.markdown(
            f'''<div style="border-left:3px solid #2e6da4; padding:8px 14px;
            background:#f0f4ff; border-radius:4px; margin-bottom:12px; color:#333;">
            <em>{seed_thought}</em></div>''',
            unsafe_allow_html=True
        )

    # Check if user already responded
    existing = get_user_response_for_card(deck_name, card_index, username)

    if existing:
        st.success("✅ You have already reflected on this question.")
        st.markdown(f"**Your response:** {existing['response_text']}")
        st.caption(f"Shared: {'Yes (anonymous)' if existing['anonymous'] else 'Yes' if not existing['anonymous'] else 'Privately'}")
        if st.button("Next Card →", key="ponder_next", type="primary", use_container_width=True):
            advance_to_next_card()
        return

    with st.form(key=f"ponder_study_form_{card_index}"):
        response_text = st.text_area(
            "Your reflection:",
            height=150,
            placeholder="Write your thoughts here…"
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            share = st.checkbox("Share with the group")
        with col2:
            anon = st.checkbox("Post anonymously", disabled=not share)

        submitted = st.form_submit_button("Submit & Continue", type="primary", use_container_width=True)

        if submitted:
            if response_text.strip():
                submit_ponder_response(
                    deck_name=deck_name,
                    card_index=card_index,
                    question=question,
                    response_text=response_text,
                    username=username,
                    anonymous=anon if share else True,
                )
                advance_to_next_card()
            else:
                st.warning("Please write a reflection before continuing.")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def handle_answer(is_correct, username):
    """Handle answer and update score"""
    from core.scoring import calculate_points
    
    # Calculate points
    points = calculate_points(is_correct)
    
    # Update score
    update_user_score(username, points, is_correct)
    
    # Update streak
    if is_correct:
        st.session_state.current_streak = st.session_state.get("current_streak", 0) + 1
    else:
        st.session_state.current_streak = 0


def commit_answer(knew_it, username):
    """Handle commit action"""
    st.session_state.committed = True
    handle_answer(knew_it, username)


def advance_to_next_card():
    """Move to next card and reset state"""
    cards = st.session_state.get("cards", [])
    if not cards:
        return

    st.session_state.current_card_index = (st.session_state.get("current_card_index", 0) + 1) % len(cards)
    st.session_state.show_answer = False

    # Clear per-mode state so next card doesn't inherit old answers
    for key in [
        "mc_options", "mc_correct_index", "mc_card_id", "mc_answered", "mc_user_answer",
        "ms_options", "ms_correct_indices", "ms_card_id", "ms_answered", "ms_user_answer",
        "tf_generated", "tf_card_id", "tf_answered", "tf_user_answer", "tf_correct",
        "quiz_answered", "quiz_user_answer", "quiz_similarity",
        "committed",
    ]:
        if key in st.session_state:
            del st.session_state[key]
