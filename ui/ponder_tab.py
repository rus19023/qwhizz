# ui/ponder_tab.py
"""
Ponder tab — displays all ponder/essay cards for the selected deck
and shows a feed of shared responses from other users.
"""

import streamlit as st
from data.deck_store import get_deck
from data.ponder_store import (
    get_all_responses_for_deck,
    get_user_response_for_card,
    delete_ponder_response,
    submit_ponder_response,
)
from data.card_format import get_card_type


def render_ponder_tab(deck_name, username):
    """Main ponder tab renderer."""
    st.subheader("💭 Ponder")
    st.caption("Reflect on open-ended questions and read how others have responded.")

    cards = get_deck(deck_name)
    if not cards:
        st.info("No cards in this deck yet.")
        return

    # Find ponder and essay cards only
    ponder_cards = [
        (i, c) for i, c in enumerate(cards)
        if get_card_type(c) in ("ponder", "essay")
    ]

    if not ponder_cards:
        st.info("This deck has no ponder or essay questions yet. Add some in the Admin tab!")
        return

    # Load all responses for the deck at once (efficient — one DB call)
    all_responses = get_all_responses_for_deck(deck_name)

    for card_index, card in ponder_cards:
        question = card.get("question", "")
        seed_thought = card.get("seed_thought", card.get("answer", ""))
        responses = all_responses.get(card_index, [])
        other_responses = [r for r in responses if r["username"] != username]
        user_response = next((r for r in responses if r["username"] == username), None)

        with st.expander(
            f"💭 {question[:80]}{'...' if len(question) > 80 else ''}  "
            f"({''+str(len(other_responses))+' response' + ('s' if len(other_responses) != 1 else '') if other_responses else 'no responses yet'})",
            expanded=False
        ):
            # Question
            st.markdown(f"### {question}")

            # Seed thought / prompt
            if seed_thought:
                st.markdown(
                    f"""<div style="border-left:3px solid #2e6da4; padding:8px 14px;
                    background:#f0f4ff; border-radius:4px; margin-bottom:12px; color:#333;">
                    <em>{seed_thought}</em></div>""",
                    unsafe_allow_html=True
                )

            st.markdown("---")

            # ── User's own response ──
            st.markdown("**Your response:**")
            if user_response:
                st.markdown(
                    f"""<div style="border:1px solid #28a745; background:#1a2e1a;
                    padding:10px 14px; border-radius:6px; margin-bottom:8px;">
                    {user_response['response_text']}</div>""",
                    unsafe_allow_html=True
                )
                st.caption(
                    f"Posted {'anonymously' if user_response['anonymous'] else 'as ' + username}"
                )
                if st.button("🗑️ Delete my response", key=f"del_ponder_{card_index}"):
                    delete_ponder_response(deck_name, card_index, username)
                    st.success("Response deleted.")
                    st.rerun()
            else:
                _render_submit_form(deck_name, card_index, question, username)

            # ── Others' responses ──
            if other_responses:
                st.markdown("---")
                st.markdown(f"**{len(other_responses)} response{'s' if len(other_responses) != 1 else ''} from others:**")
                for resp in other_responses:
                    _render_response_card(resp)
            else:
                st.caption("No responses from others yet. Be the first to share!")


def _render_submit_form(deck_name, card_index, question, username):
    """Inline submit form for sharing a ponder response."""
    with st.form(key=f"ponder_form_{card_index}"):
        response_text = st.text_area(
            "Write your reflection:",
            height=120,
            key=f"ponder_input_{card_index}",
            placeholder="Share your thoughts…"
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            share = st.checkbox("Share with the group", key=f"ponder_share_{card_index}")
        with col2:
            anon = st.checkbox("Post anonymously", key=f"ponder_anon_{card_index}", disabled=not share)

        submitted = st.form_submit_button("Submit", type="primary", use_container_width=True)

        if submitted:
            if not response_text.strip():
                st.warning("Please write a response before submitting.")
            else:
                submit_ponder_response(
                    deck_name=deck_name,
                    card_index=card_index,
                    question=question,
                    response_text=response_text,
                    username=username,
                    anonymous=anon if share else True,
                )
                if share:
                    st.success("✅ Response saved and shared!")
                else:
                    st.success("✅ Response saved privately.")
                st.rerun()


def _render_response_card(resp):
    """Render a single response card from another user."""
    display = resp.get("display_name", "Anonymous")
    ts = resp.get("timestamp")
    time_str = ts.strftime("%b %d, %Y") if ts else ""

    st.markdown(
        f"""<div style="border:1px solid #444; background:#1e1e2e;
        padding:10px 14px; border-radius:6px; margin-bottom:8px;">
        <div style="font-size:12px; color:#888; margin-bottom:6px;">
            {display} · {time_str}
        </div>
        <div style="color:#ddd;">{resp['response_text']}</div>
        </div>""",
        unsafe_allow_html=True
    )
