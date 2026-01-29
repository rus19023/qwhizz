# ui/components.py

import streamlit as st
import time
from core.flashcard_logic import flip_card, next_card


def flashcard_box(text):
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
                use_container_width=True
            )
    with col2:
        st.button(
                "➡️ Next", 
                key="next_btn", 
                on_click=next_card, 
                use_container_width=True
            )


def answer_buttons(on_correct, on_incorrect, disabled=False):
    """Show Got it / Need practice buttons after flipping"""
    col1, col2 = st.columns(2)
    with col1:
        st.button(
                "✓ Got it!", 
                key="correct_btn", 
                on_click=on_correct, 
                use_container_width=True, 
                type="primary", 
                disabled=disabled
            )
    with col2:
        st.button(
                "✗ Need practice", 
                key="incorrect_btn", 
                on_click=on_incorrect, 
                use_container_width=True, 
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
                use_container_width=True, 
                type="primary"
            )
    with col2:
        st.button(
                "✗ I don't know", 
                key="dont_know_btn", 
                on_click=on_dont_know, 
                use_container_width=True
            )


def quiz_input(on_submit):
    """Quiz mode answer input"""
    with st.form("quiz_answer_form", clear_on_submit=True):
        user_answer = st.text_input("Your answer:", key="quiz_input")
        submitted = st.form_submit_button(
                "Submit Answer", 
                use_container_width=True, 
                type="primary"
            )   
        if submitted:
            on_submit(user_answer)


def timer_display(start_time, min_delay):
    """Display countdown timer"""
    elapsed = time.time() - start_time
    remaining = max(0, min_delay - elapsed)
    if remaining > 0:
        st.warning(
                f"⏳ Please wait {remaining:.1f} seconds before answering..."
            )
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
    verif_total = user_data.get(
            "verification_passed", 
            0
        ) + user_data.get("verification_failed", 0)
    if verif_total > 0:
        verif_accuracy = (
                user_data.get("verification_passed", 0) / verif_total * 100)
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
    st.dataframe(df, use_container_width=True, hide_index=True)


def mode_selector():
    """Study mode selector"""
    from core.study_modes import STUDY_MODES
    
    st.sidebar.subheader("Study Mode")
    
    mode_options = {key: config["name"] for key, config in STUDY_MODES.items()}
    
    selected_mode = st.sidebar.selectbox(
        "Select mode:",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        key="study_mode"
    )
    
    # Show mode description
    mode_config = STUDY_MODES[selected_mode]
    st.sidebar.caption(mode_config["description"])
    
    return selected_mode


# Add to ui/components.py

def multiple_choice_buttons(options, on_answer):
    """Display multiple choice buttons"""
    st.write("**Choose the correct answer:**")
    
    cols = st.columns(2)
    for idx, option in enumerate(options):
        with cols[idx % 2]:
            if st.button(
                f"{chr(65 + idx)}. {option}", 
                key=f"mc_option_{idx}",
                use_container_width=True
            ):
                on_answer(idx)


def true_false_buttons(on_answer):
    """Display true/false buttons"""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✓ TRUE", key="tf_true", use_container_width=True, type="primary"):
            on_answer(True)
    with col2:
        if st.button("✗ FALSE", key="tf_false", use_container_width=True):
            on_answer(False)


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
        - Multiple Choice: Full points
        - True/False: Full points
        - Typed answers: Full points + verification credit
        - Flashcard mode: Full points (honor system)
        
        **Tips for High Scores:**
        - Build streaks for massive bonuses! 🔥
        - Use quiz modes to prove your knowledge
        - Study consistently to maintain accuracy
        """)