# ui/components.py

import streamlit as st
import time
from core.flashcard_logic import flip_card, next_card


def flashcard_box(text, image_url=None):
    """Display flashcard with optional image"""
    if image_url:
        st.image(image_url, width='stretch')
        st.markdown("---")
    
    st.markdown(
        f"""
        <div style="
            font-size:24px;
            padding:20px;
            border-radius:10px;
            border:2px solid #ddd;
            text-align:center;
            min-height:200px;
            display:flex;
            align-items:center;
            justify-content:center;">
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )


def controls():
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "🔄 Flip", 
            key="flip_btn", 
            on_click=flip_card, 
            width='stretch'
        )
    with col2:
        st.button(
            "➡️ Next", 
            key="next_btn", 
            on_click=next_card, 
            width='stretch'
        )


def answer_buttons(on_correct, on_incorrect, disabled=False):
    """Show Got it / Need practice buttons after flipping"""
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "✓ Got it!", 
            key="correct_btn", 
            on_click=on_correct, 
            width='stretch', 
            type="primary", 
            disabled=disabled
        )
    with col2:
        st.button(
            "✗ Need practice", 
            key="incorrect_btn", 
            on_click=on_incorrect, 
            width='stretch', 
            disabled=disabled
        )


def commit_buttons(on_know, on_dont_know):
    """Commit before revealing answer"""
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "✓ I know this", 
            key="know_btn", 
            on_click=on_know, 
            width='stretch', 
            type="primary"
        )
    with col2:
        st.button(
            "✗ I don't know", 
            key="dont_know_btn", 
            on_click=on_dont_know, 
            width='stretch'
        )


def quiz_input(on_submit):
    """Quiz mode answer input"""
    with st.form("quiz_answer_form", clear_on_submit=True):
        user_answer = st.text_input("Your answer:", key="quiz_input")
        submitted = st.form_submit_button(
            "Submit Answer", 
            width='stretch', 
            type="primary"
        )   
        if submitted:
            on_submit(user_answer)


def timer_display(start_time, min_delay):
    """Display countdown timer"""
    elapsed = time.time() - start_time
    remaining = max(0, min_delay - elapsed)
    if remaining > 0:
        st.warning(f"⏳ Please wait {remaining:.1f} seconds before answering...")
        return False
    else:
        st.success("✅ You can answer now")
        return True


def user_stats(user_data):
    """Display user statistics"""
    col1, col2, col3, col4 = st.columns(4)
    total = user_data["cards_studied"]
    accuracy = (user_data["correct_answers"] / total * 100) if total > 0 else 0
    with col1:
        st.metric("Total Score", user_data["total_score"])
    with col2:
        st.metric("Cards Studied", total)
    with col3:
        st.metric("Accuracy", f"{accuracy:.1f}%")
    with col4:
        st.metric("Current Streak", user_data["current_streak"])
    
    # Verification stats if available
    verif_total = user_data.get("verification_passed", 0) + user_data.get("verification_failed", 0)
    if verif_total > 0:
        verif_accuracy = (user_data.get("verification_passed", 0) / verif_total * 100)
        st.caption(
            f"Verification Accuracy: {verif_accuracy:.1f}% "
            f"({user_data.get('verification_passed', 0)}/{verif_total})"
        )


def leaderboard(users_list):
    """Display leaderboard with detailed stats in table format"""
    st.subheader("🏆 Leaderboard")
    if not users_list:
        st.info("No users yet. Be the first to study!")
        return
    
    # Prepare data for table
    leaderboard_data = []
    for idx, user in enumerate(users_list, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else str(idx)
        total = user.get("cards_studied", 0)
        accuracy = (user.get("correct_answers", 0) / total * 100) if total > 0 else 0   
        verif_total = user.get("verification_passed", 0) + user.get("verification_failed", 0)
        verif_accuracy = (user.get("verification_passed", 0) / verif_total * 100) if verif_total > 0 else 0
        
        leaderboard_data.append({
            "Rank": medal,
            "Username": user['_id'],
            "Score": user.get("total_score", 0),
            "Cards": total,
            "Accuracy": f"{accuracy:.1f}%",
            "Streak": user.get("current_streak", 0),
            "Best Streak": user.get("best_streak", 0),
            "Verified": f"{verif_accuracy:.0f}%" if verif_total > 0 else "N/A"
        })
    
    # Display as dataframe
    import pandas as pd
    df = pd.DataFrame(leaderboard_data)
    st.dataframe(df, width='stretch', hide_index=True)


def mode_selector():
    """Study mode selector"""
    from core.study_modes import STUDY_MODES
    
    st.sidebar.subheader("Study Mode")
    
    mode_options = {key: config["name"] for key, config in STUDY_MODES.items()}
    
    selected_mode = st.sidebar.selectbox(
        "Select mode:",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        key="study_mode_selector"
    )
    
    # Show mode description
    mode_config = STUDY_MODES[selected_mode]
    st.sidebar.caption(mode_config["description"])
    
    return selected_mode


def multiple_choice_buttons(options, on_answer, correct_index=None, show_result=False):
    """
    Display multiple choice buttons (up to 10 options)
    
    Args:
        options: List of option strings (up to 10)
        on_answer: Callback function(selected_index)
        correct_index: Index of correct answer (for showing results)
        show_result: Whether to show if answer was correct/incorrect
    """
    st.write("**Choose the correct answer:**")
    
    # Support up to 10 options
    num_options = min(len(options), 10)
    
    # Use 2 columns for clean layout
    cols = st.columns(2)
    
    for idx in range(num_options):
        with cols[idx % 2]:
            button_label = f"{chr(65 + idx)}. {options[idx]}"
            
            # Determine button type based on result
            button_type = "secondary"
            if show_result and correct_index is not None:
                if idx == correct_index:
                    button_type = "primary"
                    button_label += " ✓"
            
            if st.button(
                button_label,
                key=f"mc_option_{idx}",
                width='stretch',
                type=button_type,
                disabled=show_result
            ):
                on_answer(idx)


def multi_select_checkboxes(options, on_submit, correct_indices=None, show_result=False):
    """
    Display multi-select checkboxes for questions with multiple correct answers
    
    Args:
        options: List of option strings (up to 10)
        on_submit: Callback function(selected_indices_list)
        correct_indices: List of correct answer indices (for showing results)
        show_result: Whether to show if answers were correct/incorrect
    """
    st.write("**Select ALL correct answers:**")
    
    with st.form("multi_select_form", clear_on_submit=False):
        selected = []
        
        num_options = min(len(options), 10)
        
        for idx in range(num_options):
            label = f"{chr(65 + idx)}. {options[idx]}"
            
            # Add indicators if showing results
            if show_result and correct_indices is not None:
                if idx in correct_indices:
                    label += " ✓"
            
            if st.checkbox(label, key=f"ms_option_{idx}", disabled=show_result):
                selected.append(idx)
        
        submitted = st.form_submit_button(
            "Submit Answer",
            width='stretch',
            type="primary",
            disabled=show_result
        )
        
        if submitted and not show_result:
            on_submit(selected)


def true_false_buttons(on_answer, correct_answer=None, show_result=False):
    """
    Display true/false buttons
    
    Args:
        on_answer: Callback function(True/False)
        correct_answer: The correct answer (True/False) for showing results
        show_result: Whether to show if answer was correct/incorrect
    """
    col1, col2 = st.columns(2)
    
    with col1:
        true_type = "primary" if show_result and correct_answer else "secondary"
        true_label = "✓ TRUE"
        if show_result and correct_answer:
            true_label += " ✓"
        
        if st.button(
            true_label,
            key="tf_true",
            width='stretch',
            type=true_type,
            disabled=show_result
        ):
            on_answer(True)
    
    with col2:
        false_type = "primary" if show_result and not correct_answer else "secondary"
        false_label = "✗ FALSE"
        if show_result and not correct_answer:
            false_label += " ✓"
        
        if st.button(
            false_label,
            key="tf_false",
            width='stretch',
            type=false_type,
            disabled=show_result
        ):
            on_answer(False)


def display_question_with_image(question_text, image_url=None):
    """
    Display question with optional image (chart, table, diagram, etc.)
    
    Args:
        question_text: The question text
        image_url: URL or file path to image
    """
    if image_url:
        try:
            st.image(image_url, caption="Question Image", width='stretch')
            st.markdown("---")
        except Exception as e:
            st.warning(f"Could not load image: {e}")
    
    st.markdown(f"### {question_text}")


def points_info():
    """Show point system in an expandable section"""
    with st.expander("ℹ️ How Points Work"):
        st.write("""
        **Base Points:**
        - ✓ Correct answer: **+10 points**
        - ✗ Wrong answer: **-3 points**
        
        **Streak Bonus:**
        - Each card in your streak: **+5 bonus points**
        - Example: 3-card streak = 10 + (3 × 5) = **25 points!**
        
        **Game Modes:**
        - Multiple Choice: Full points (single correct answer)
        - Multi-Select: Full points (all correct answers required)
        - True/False: Full points
        - Typed answers: Full points + verification credit
        - Flashcard mode: Full points (honor system)
        
        **Tips for High Scores:**
        - Build streaks for massive bonuses! 🔥
        - Use quiz modes to prove your knowledge
        - Study consistently to maintain accuracy
        """)
