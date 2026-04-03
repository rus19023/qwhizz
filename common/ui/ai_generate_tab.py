# ui/ai_generate_tab.py
"""
AI-powered deck generation tab.

Supports:
  - Multiple file uploads (.pdf, .docx, .txt) — concatenated before generation
  - Web URL extraction
  - Raw text paste
  - Provider / model selection
  - Duplicate detection against the existing deck
  - Per-card approve/skip before saving
"""

from __future__ import annotations
import streamlit as st

from core.ai_deck_generator import (
    generate_from_file,
    generate_from_url,
    generate_from_text,
    PROVIDERS,
    DEFAULT_MODELS,
)
from data.deck_store import get_deck_names, get_deck, create_deck
from models.card import Card


# ── Duplicate detection ───────────────────────────────────────────────────────

def _is_duplicate(question: str, existing_questions: list[str], threshold: float = 0.85) -> bool:
    """
    Check if a question is a near-duplicate of any existing question.
    Uses simple normalised character overlap (no embeddings needed).

    Args:
        question (str): Candidate question text.
        existing_questions (list[str]): Lowercased existing questions.
        threshold (float): Similarity threshold (0-1). 0.85 works well in practice.

    Returns:
        bool: True if a near-duplicate exists.
    """
    from difflib import SequenceMatcher
    q = question.lower().strip()
    for existing in existing_questions:
        ratio = SequenceMatcher(None, q, existing).ratio()
        if ratio >= threshold:
            return True
    return False


# ── Main renderer ─────────────────────────────────────────────────────────────

def render_ai_generate_tab() -> None:
    """Render the AI deck generation tab."""
    st.subheader("🤖 Generate Cards with AI")

    # ── Deck selection ────────────────────────────────────────────────────────
    deck_option = st.radio(
        "Target deck:",
        ["Add to existing deck", "Create new deck"],
        horizontal=True,
        key="aigen_deck_option",
    )

    existing_decks = get_deck_names()
    deck_name = ""

    if deck_option == "Add to existing deck":
        if existing_decks:
            deck_name = st.selectbox(
                "Select deck:",
                options=existing_decks,
                key="aigen_deck_select",
            )
        else:
            st.warning("No decks yet — switch to 'Create new deck'.")
    else:
        new_name = st.text_input("New deck name:", key="aigen_new_deck_name")
        deck_name = new_name.strip()

    if not deck_name:
        st.info("Choose or name a deck above to continue.")
        return

    # ── Provider / model ──────────────────────────────────────────────────────
    st.write("**AI Provider:**")
    col_prov, col_model = st.columns([2, 3])
    with col_prov:
        provider_label = st.selectbox(
            "Provider",
            options=list(PROVIDERS.keys()),
            key="aigen_provider",
            label_visibility="collapsed",
        )
        provider = PROVIDERS[provider_label]

    with col_model:
        model_input = st.text_input(
            "Model (leave blank for default)",
            value="",
            placeholder=DEFAULT_MODELS.get(provider, ""),
            key="aigen_model",
        )
        model = model_input.strip() or None

    # ── Number of cards ───────────────────────────────────────────────────────
    num_cards = st.slider(
        "Approximate number of cards to generate",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
        key="aigen_num_cards",
    )

    # ── Source selection ──────────────────────────────────────────────────────
    st.write("**Source:**")
    source_type = st.radio(
        "Source type",
        ["📄 Files", "🌐 URL", "📝 Paste text"],
        horizontal=True,
        key="aigen_source_type",
        label_visibility="collapsed",
    )

    source_ready = False
    source_label = ""
    uploaded_files = []
    url_input      = ""
    pasted         = ""

    if source_type == "📄 Files":
        st.info(
            "Upload one or more files. Text will be concatenated before generation.\n\n"
            "Supported: **.pdf · .docx · .txt**"
        )
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="aigen_files",
        )
        if uploaded_files:
            st.caption(f"{len(uploaded_files)} file(s) selected: " +
                       ", ".join(f.name for f in uploaded_files))
            source_ready = True
            source_label = ", ".join(f.name for f in uploaded_files)

    elif source_type == "🌐 URL":
        url_input = st.text_input(
            "Web page URL",
            placeholder="https://example.com/article",
            key="aigen_url",
        )
        if url_input.strip():
            source_ready = True
            source_label = url_input.strip()

    else:  # Paste text
        pasted = st.text_area(
            "Paste study material here",
            height=200,
            key="aigen_paste",
        )
        if pasted.strip():
            source_ready = True
            source_label = "pasted text"

    # ── Generate button ───────────────────────────────────────────────────────
    if not source_ready:
        st.info("Add a source above to continue.")
        return

    if st.button("🚀 Generate Cards", type="primary", key="aigen_run_btn"):
        with st.spinner(f"Generating ~{num_cards} cards from {source_label}..."):
            try:
                if source_type == "📄 Files":
                    _, raw_cards = generate_from_file(
                        uploaded_files, num_cards, provider, model
                    )
                elif source_type == "🌐 URL":
                    _, raw_cards = generate_from_url(
                        url_input.strip(), num_cards, provider, model
                    )
                else:
                    _, raw_cards = generate_from_text(
                        pasted.strip(), num_cards, provider, model
                    )
            except Exception as e:
                st.error(f"Generation failed: {e}")
                return

        if not raw_cards:
            st.error("No cards were generated. Check your source content and API key.")
            return

        # ── Deduplicate against existing deck ─────────────────────────────────
        existing_cards  = get_deck(deck_name)
        existing_qs     = [c.get("question", "").lower().strip() for c in existing_cards]
        
        unique    = []
        dupes     = []
        batch_qs  = []  # track duplicates within the new batch itself

        for card in raw_cards:
            q = (card.get("question") or "").strip()
            if not q:
                continue
            if _is_duplicate(q, existing_qs + batch_qs):
                dupes.append(card)
            else:
                unique.append(card)
                batch_qs.append(q.lower())

        st.success(
            f"Generated **{len(raw_cards)}** cards · "
            f"**{len(unique)}** unique · "
            f"**{len(dupes)}** duplicate(s) removed"
        )

        if dupes:
            with st.expander(f"🔁 {len(dupes)} duplicate(s) skipped"):
                for d in dupes:
                    st.caption(f"• {d.get('question', '')[:80]}")

        if not unique:
            st.warning("All generated cards were duplicates of existing ones.")
            return

        st.session_state["aigen_proposals"] = unique
        st.session_state["aigen_deck_name"] = deck_name

    # ── Preview & approve ─────────────────────────────────────────────────────
    proposals = st.session_state.get("aigen_proposals", [])
    target    = st.session_state.get("aigen_deck_name", deck_name)

    if not proposals:
        return

    st.write(f"### 📋 Review {len(proposals)} Card(s) for '{target}'")
    st.caption("Uncheck any card you want to skip before saving.")

    approved_indices = []
    for i, card in enumerate(proposals):
        q = card.get("question", "")
        a = card.get("answer", "")
        with st.expander(f"Card {i+1}: {q[:60]}..."):
            approved = st.checkbox("✅ Include this card", value=True, key=f"aigen_approve_{i}")
            if approved:
                approved_indices.append(i)
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            card_type = card.get("type", "flashcard")
            if card_type != "flashcard":
                st.caption(f"Type: {card_type}")
            if card.get("options"):
                st.caption("Options: " + " · ".join(card["options"]))

    st.write(f"**{len(approved_indices)}** card(s) selected.")

    col_save, col_discard = st.columns(2)
    with col_save:
        if st.button(
            "💾 Save to Deck", type="primary",
            disabled=not approved_indices,
            key="aigen_save_btn",
        ):
            approved_cards = [proposals[i] for i in approved_indices]

            # Create deck if new
            if target not in get_deck_names():
                create_deck(target)

            from data.db import get_database
            db = get_database()
            db.decks.update_one(
                {"_id": target},
                {"$push": {"cards": {"$each": approved_cards}}},
                upsert=True,
            )

            st.success(f"✅ Saved {len(approved_cards)} card(s) to '{target}'!")
            st.balloons()
            del st.session_state["aigen_proposals"]
            del st.session_state["aigen_deck_name"]
            st.rerun()

    with col_discard:
        if st.button("🗑️ Discard All", key="aigen_discard_btn"):
            del st.session_state["aigen_proposals"]
            del st.session_state["aigen_deck_name"]
            st.rerun()