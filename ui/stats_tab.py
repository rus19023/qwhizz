# ui/stats_tab.py

import streamlit as st
from ui.components import user_stats


def render_stats_tab(user_data):
    """Render the stats tab"""
    st.subheader("Your Statistics")
    user_stats(user_data)
    
    st.divider()
    st.write("### Additional Stats")
    
    total = user_data["cards_studied"]
    if total > 0:
        st.write(f"**Best Streak:** {user_data.get('best_streak', 0)} 🔥")
        st.write(f"**Total Cards Studied:** {total}")
        st.write(f"**Correct Answers:** {user_data['correct_answers']}")
        st.write(f"**Incorrect Answers:** {user_data['incorrect_answers']}")
        
        # Verification stats
        verif_total = user_data.get("verification_passed", 0) + user_data.get("verification_failed", 0)
        if verif_total > 0:
            verif_accuracy = (user_data.get("verification_passed", 0) / verif_total * 100)
            st.write(f"**Verification Accuracy:** {verif_accuracy:.1f}% ({user_data.get('verification_passed', 0)}/{verif_total})")
    else:
        st.info("Start studying to see your stats!")