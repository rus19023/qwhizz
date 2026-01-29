# ui/admin_tab.py

import streamlit as st
from data.user_store import (
    get_suspicious_users,
    flag_user,
    unflag_user,
    reset_user_score,
    get_user
)


def render_admin_tab():
    """Render the admin dashboard tab"""
    st.subheader("🛡️ Admin Dashboard")
    
    st.write("### Suspicious Activity")
    suspicious = get_suspicious_users()
    
    if suspicious:
        for item in suspicious:
            severity_color = "🔴" if item["severity"] == "high" else "🟡"
            with st.expander(
                    f"{severity_color} {item['username']} - {item['reason']}"):
                user = get_user(item['username'])
                
                st.write(f"**Total Score:** {user.get('total_score', 0)}")
                st.write(f"**Cards Studied:** {user.get('cards_studied', 0)}")
                st.write(f"**Accuracy:** {(user.get('correct_answers', 0) / user.get('cards_studied', 1) * 100):.1f}%")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🚩 Flag User", key=f"flag_{item['username']}"):
                        flag_user(item['username'])
                        st.success("User flagged!")
                        st.rerun()
                with col2:
                    if st.button("✓ Clear Flag", key=f"unflag_{item['username']}"):
                        unflag_user(item['username'])
                        st.success("Flag cleared!")
                        st.rerun()
                with col3:
                    if st.button("🔄 Reset Score", key=f"reset_{item['username']}"):
                        reset_user_score(item['username'])
                        st.success("Score reset!")
                        st.rerun()
    else:
        st.success("No suspicious activity detected!")