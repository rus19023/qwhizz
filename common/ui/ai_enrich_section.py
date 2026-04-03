# ui/ai_enrich_section.py
"""
Renders the '🤖 AI Enrich Deck' section inside manage_tab.
Call render_ai_enrich_section(manage_deck, indexed_cards) from render_manage_tab().
"""

from __future__ import annotations
import streamlit as st

from core.ai_deck_enricher import enrich_deck, apply_proposals, card_missing_fields
from core.ai_deck_generator import PROVIDERS, DEFAULT_MODELS


# Human-readable field labels
FIELD_LABELS = {
    "wrong_answers": "❌ Wrong answers / distractors",
    "explanation":   "📖 Explanation (shown after answering)",
    "feedback":      "💬 Feedback text",
}


def render_ai_enrich_section(manage_deck: str, indexed_cards: list):
    """
    Render the AI enrichment section for a deck.

    Args:
        manage_deck (str): The deck's _id.
        indexed_cards (list): List of (index, Card) tuples from _cards_from_deck().
    """
    st.subheader("🤖 AI Enrich Deck")

    if not indexed_cards:
        st.info("No cards to enrich.")
        return

    # ── Gap summary ───────────────────────────────────────────────────────────
    raw_cards = [{"index": idx, **card.to_dict()} for idx, card in indexed_cards]

    gap_counts = {"wrong_answers": 0, "explanation": 0, "feedback": 0}
    for card in raw_cards:
        for field in card_missing_fields(card):
            if field in gap_counts:
                gap_counts[field] += 1

    total_cards = len(raw_cards)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Missing distractors",  gap_counts["wrong_answers"],
                  help="Cards with no wrong_answers stored")
    with col2:
        st.metric("Missing explanations", gap_counts["explanation"],
                  help="Cards with no explanation field")
    with col3:
        st.metric("Missing feedback",     gap_counts["feedback"],
                  help="Cards with no feedback text")

    any_missing = any(v > 0 for v in gap_counts.values())
    if not any_missing:
        st.success("✅ All cards are fully enriched!")
        return

    # ── Configuration ─────────────────────────────────────────────────────────
    with st.expander("⚙️ Configure & Run Enrichment", expanded=True):

        st.write("**Select fields to fill in:**")
        selected_fields = []
        for field, label in FIELD_LABELS.items():
            missing = gap_counts[field]
            if missing > 0:
                if st.checkbox(f"{label}  ({missing} cards missing)", value=True, key=f"enrich_{field}"):
                    selected_fields.append(field)
            else:
                st.checkbox(f"{label}  ✅ all filled", value=False, disabled=True, key=f"enrich_{field}")

        st.write("**AI Provider:**")
        provider_label = st.selectbox(
            "Provider",
            options=list(PROVIDERS.keys()),
            key="enrich_provider",
            label_visibility="collapsed",
        )
        provider = PROVIDERS[provider_label]

        model = st.text_input(
            "Model (leave blank for default)",
            value="",
            placeholder=DEFAULT_MODELS.get(provider, ""),
            key="enrich_model",
        )
        model = model.strip() or None

        st.caption(
            f"⚠️ This will make one AI call per missing field per card. "
            f"Estimated calls: **{sum(gap_counts[f] for f in selected_fields)}**"
        )

        run_btn = st.button(
            "🚀 Generate Missing Content",
            type="primary",
            disabled=not selected_fields,
            key="enrich_run_btn",
        )

    # ── Run enrichment ────────────────────────────────────────────────────────
    if run_btn:
        if not selected_fields:
            st.warning("Select at least one field to fill.")
            return

        progress_bar  = st.progress(0)
        status_text   = st.empty()

        def on_progress(current, total, question):
            progress_bar.progress(current / total)
            status_text.caption(f"Processing {current}/{total}: {question[:60]}...")

        with st.spinner("Generating content..."):
            proposals = enrich_deck(
                deck_name=manage_deck,
                cards=raw_cards,
                fields_to_fill=selected_fields,
                provider=provider,
                model=model,
                progress_callback=on_progress,
            )

        progress_bar.empty()
        status_text.empty()

        if not proposals:
            st.success("✅ Nothing to fill — all selected fields are already populated!")
            return

        st.success(f"Generated content for **{len(proposals)}** card(s). Review below:")
        st.session_state["enrich_proposals"] = proposals

    # ── Preview & approve ─────────────────────────────────────────────────────
    proposals = st.session_state.get("enrich_proposals", [])
    if not proposals:
        return

    st.write("### 📋 Review Proposed Changes")
    st.caption("Uncheck any card you want to skip before saving.")

    approved_indices = []
    for i, proposal in enumerate(proposals):
        changes  = proposal["changes"]
        question = proposal["question"]

        with st.expander(f"Card #{proposal['index'] + 1}: {question[:60]}..."):
            approved = st.checkbox("✅ Approve this card", value=True, key=f"approve_{i}")
            if approved:
                approved_indices.append(i)

            for field, value in changes.items():
                label = FIELD_LABELS.get(field, field)
                st.markdown(f"**{label}:**")
                if isinstance(value, list):
                    for item in value:
                        st.markdown(f"- {item}")
                else:
                    st.markdown(value)

    if approved_indices:
        st.write(f"**{len(approved_indices)}** card(s) selected for saving.")

        if st.button("💾 Save Approved Changes", type="primary", key="enrich_save_btn"):
            approved_proposals = [proposals[i] for i in approved_indices]
            updated = apply_proposals(manage_deck, approved_proposals)
            st.success(f"✅ Saved enrichment for {updated} card(s)!")
            del st.session_state["enrich_proposals"]
            st.rerun()

        if st.button("🗑️ Discard All", key="enrich_discard_btn"):
            del st.session_state["enrich_proposals"]
            st.rerun()
            