# ui/stats_tab.py

import streamlit as st
from ui.components import user_stats
from data.user_store import get_deck_stats_for_user


def render_stats_tab(user_data):
    """Render the stats tab with overall and per-deck stats"""
    st.subheader("📊 Your Statistics")

    # ── Overall stats ─────────────────────────────────────────────────────────
    user_stats(user_data)

    st.markdown("---")
    st.markdown("### 📈 Additional Stats")

    total = user_data.get("cards_studied", 0)
    if total > 0:
        st.write(f"**Best Streak:** {user_data.get('best_streak', 0)} 🔥")
        st.write(f"**Total Cards Studied:** {total}")
        st.write(f"**Correct Answers:** {user_data.get('correct_answers', 0)}")
        st.write(f"**Incorrect Answers:** {user_data.get('incorrect_answers', 0)}")

        verif_total = (
            user_data.get("verification_passed", 0)
            + user_data.get("verification_failed", 0)
        )
        if verif_total > 0:
            verif_accuracy = user_data.get("verification_passed", 0) / verif_total * 100
            st.write(
                f"**Verification Accuracy:** {verif_accuracy:.1f}% "
                f"({user_data.get('verification_passed', 0)}/{verif_total})"
            )
    else:
        st.info("Start studying to see your stats!")
        return

    # ── Per-deck stats ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🗂️ Progress by Deck")

    username = user_data.get("_id") or user_data.get("username", "")
    deck_stats = get_deck_stats_for_user(username)

    if not deck_stats:
        st.info("No deck activity yet. Start studying a deck to track progress!")
        return

    # Summary table
    import pandas as pd

    rows = []
    for d in deck_stats:
        last = d["last_studied"]
        last_str = last.strftime("%b %d, %Y") if last else "—"
        rows.append({
            "Deck":         d["deck_name"],
            "Cards Studied": d["total"],
            "Correct":      d["correct"],
            "Incorrect":    d["incorrect"],
            "Accuracy":     f"{d['accuracy']}%",
            "Last Studied": last_str,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # ── Per-deck detail expanders ─────────────────────────────────────────────
    st.markdown("#### Deck Details")

    for d in deck_stats:
        accuracy = d["accuracy"]
        icon = "🟢" if accuracy >= 80 else "🟡" if accuracy >= 50 else "🔴"

        with st.expander(f"{icon} {d['deck_name']} — {accuracy}% accuracy"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Cards Studied", d["total"])
            with col2:
                st.metric("Correct", d["correct"])
            with col3:
                st.metric("Incorrect", d["incorrect"])
            with col4:
                st.metric("Accuracy", f"{accuracy}%")

            # Progress bar
            st.progress(accuracy / 100)

            last = d["last_studied"]
            if last:
                st.caption(f"Last studied: {last.strftime('%B %d, %Y at %I:%M %p')}")