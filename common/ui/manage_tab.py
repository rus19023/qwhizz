# ui/manage_tab.py

import traceback
import json
import csv
import io
from pathlib import Path
import streamlit as st
from ui.ai_enrich_section import render_ai_enrich_section

from data.deck_store import (
    get_deck_names,
    find_duplicate_cards,
    delete_card,
    get_all_cards_with_indices,
    create_deck,
)
from ui.router import TabSpec, render_tabs
from models.card import Card, CardFeedback, CardLink
from core.paywall import require_feature, has_access


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cards_from_deck(manage_deck: str) -> list[tuple[int, Card]]:
    raw = get_all_cards_with_indices(manage_deck)
    return [(c["index"], Card.from_dict(c)) for c in raw]


def _save_card(manage_deck: str, index: int, card: Card) -> bool:
    from data.db import get_database
    db = get_database()
    deck_doc = db.decks.find_one({"_id": manage_deck})
    if not deck_doc:
        st.error("Could not find deck in database.")
        return False
    cards_list = deck_doc["cards"]
    cards_list[index] = card.to_dict()
    db.decks.update_one({"_id": manage_deck}, {"$set": {"cards": cards_list}})
    return True


def _rename_deck(old_name: str, new_name: str) -> tuple[bool, str]:
    """
    Rename a deck by inserting a new document with the new _id,
    copying all cards, then deleting the old document.
    Returns (success, message).
    """
    from data.db import get_database
    db = get_database()

    if not new_name.strip():
        return False, "New name cannot be empty."
    new_name = new_name.strip()
    if new_name == old_name:
        return False, "New name is the same as the current name."
    if db.decks.find_one({"_id": new_name}):
        return False, f"A deck named '{new_name}' already exists."

    old_doc = db.decks.find_one({"_id": old_name})
    if not old_doc:
        return False, f"Deck '{old_name}' not found."

    # Insert under new _id, then remove old
    new_doc = {**old_doc, "_id": new_name}
    db.decks.insert_one(new_doc)
    db.decks.delete_one({"_id": old_name})
    return True, f"Deck renamed to '{new_name}'."


# ── Shared helpers ────────────────────────────────────────────────────────────

def _render_card_preview(cards: list):
    """Show a preview of cards (Card models or dicts)."""
    with st.expander("👁️ Preview cards"):
        preview = cards[:5]
        for c in preview:
            if isinstance(c, dict):
                st.write(f"**Q:** {c.get('question', '')}")
                st.write(f"**A:** {c.get('answer', '')}")
            else:
                st.write(f"**Q:** {c.question}")
                st.write(f"**A:** {c.answer}")
                if c.wrong_answers:
                    st.caption("Wrong: " + ", ".join(c.wrong_answers))
            st.divider()
        if len(cards) > 5:
            st.caption(f"...and {len(cards) - 5} more")


def _save_cards_to_deck(deck_name: str, cards: list[dict]):
    """Append a list of card dicts to a deck in MongoDB."""
    from data.db import get_database
    db = get_database()
    deck_doc = db.decks.find_one({"_id": deck_name})
    if deck_doc:
        existing = deck_doc.get("cards", [])
        existing.extend(cards)
        db.decks.update_one({"_id": deck_name}, {"$set": {"cards": existing}})
    else:
        db.decks.insert_one({"_id": deck_name, "cards": cards})


# ── Main tab ──────────────────────────────────────────────────────────────────

def render_manage_tab(username: str | None = None):
    """
    Args:
        username: logged-in username — used for access control.
                  Pass None to disable gating (legacy callers).
    """
    
    try:
        st.subheader("🗂️ Manage Decks")

        # ── Access control ────────────────────────────────────────────────────
        if username and not require_feature("manage_decks", username):
            return

        manage_deck = st.selectbox(
            "Select deck to manage:",
            options=get_deck_names(),
            key="manage_deck_select",
        )

        indexed_cards = _cards_from_deck(manage_deck)
        
        # Determine is_admin from username
        is_admin = False
        if username:
            from data.user_store import get_user
            user_doc = get_user(username)
            is_admin = bool(user_doc.get("is_admin", False)) if user_doc else False
            
            
        manage_deck_tabs = [            
            TabSpec("📤 Export", lambda: _render_export(manage_deck, indexed_cards), admin_only=True),
            TabSpec("📥 Import", lambda: _render_import(manage_deck), admin_only=True),
            TabSpec("💡 AI Enrich Deck", lambda: render_ai_enrich_section(manage_deck, indexed_cards), admin_only=True),
            TabSpec("🔍 Duplicates", lambda: _render_duplicates(manage_deck), admin_only=True),
            TabSpec("📋 Browse & Edit", lambda: _render_browse(manage_deck, indexed_cards), admin_only=True),
            TabSpec("✏️ Rename Deck", lambda: _render_rename_deck(manage_deck, username), admin_only=True),
            TabSpec("👥 User Access", lambda: _render_user_access(username), admin_only=True),
        ]


        # ── Tabs ──────────────────────────────────────────────────────────────
        
        render_tabs(manage_deck_tabs, is_admin=is_admin)

    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())


# ── Export ────────────────────────────────────────────────────────────────────

def _render_export(manage_deck: str, indexed_cards):
    st.subheader("📤 Export Deck")

    export_cards = [card for _, card in indexed_cards]
    if not export_cards:
        st.info("No cards to export.")
        return

    json_bytes = json.dumps(
        [c.to_dict() for c in export_cards], indent=2, default=str
    ).encode("utf-8")

    flat_rows = [c.to_export_row() for c in export_cards]
    all_fields = list(flat_rows[0].keys()) if flat_rows else []
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=all_fields)
    writer.writeheader()
    writer.writerows(flat_rows)
    csv_bytes = buf.getvalue().encode("utf-8")

    col_json, col_csv = st.columns(2)
    with col_json:
        st.download_button(
            label="⬇️ Download JSON",
            data=json_bytes,
            file_name=f"{manage_deck}.json",
            mime="application/json",
            width='stretch',
        )
    with col_csv:
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"{manage_deck}.csv",
            mime="text/csv",
            width='stretch',
        )

    with st.expander("💾 Save to local folder"):
        save_path = st.text_input(
            "Folder path",
            value=str(Path.home()),
            key="export_save_path",
        )
        col_sj, col_sc = st.columns(2)
        with col_sj:
            if st.button("💾 Save JSON", key="save_json_local", width='stretch'):
                try:
                    dest = Path(save_path) / f"{manage_deck}.json"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(json_bytes)
                    st.success(f"Saved to {dest}")
                except Exception as e:
                    st.error(f"Could not save: {e}")
        with col_sc:
            if st.button("💾 Save CSV", key="save_csv_local", width='stretch'):
                try:
                    dest = Path(save_path) / f"{manage_deck}.csv"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(csv_bytes)
                    st.success(f"Saved to {dest}")
                except Exception as e:
                    st.error(f"Could not save: {e}")


# ── Import ────────────────────────────────────────────────────────────────────

def _render_import(manage_deck: str):
    st.subheader("📥 Import Cards")
    uploaded = st.file_uploader("Upload JSON file", type=["json"], key="import_upload")
    if not uploaded:
        return

    try:
        raw_import = json.loads(uploaded.read().decode("utf-8"))
        if not isinstance(raw_import, list):
            st.error("JSON must be a list of card objects.")
            return

        parsed: list[Card] = []
        errors = []
        for i, item in enumerate(raw_import):
            try:
                parsed.append(Card.from_dict(item))
            except Exception as e:
                errors.append(f"Row {i+1}: {e}")

        if errors:
            st.warning(f"{len(errors)} card(s) had errors and were skipped:")
            for err in errors:
                st.caption(err)

        if parsed:
            st.success(f"Ready to import {len(parsed)} card(s).")
            _render_card_preview(parsed)

            if st.button("✅ Confirm Import", type="primary", key="confirm_import_json"):
                _save_cards_to_deck(manage_deck, [c.to_dict() for c in parsed])
                st.success(f"✅ Imported {len(parsed)} cards into '{manage_deck}'!")
                st.rerun()

    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")


# ── AI Deck Generator ─────────────────────────────────────────────────────────

def _render_ai_generator(manage_deck: str, username: str | None):
    st.subheader("🤖 AI Deck Generator")

    if username and not require_feature("ai_deck_gen", username):
        return

    st.info(
        "Upload a document or enter a URL and Claude will generate flashcards automatically. "
        "Review the preview before saving to the deck."
    )

    num_cards = st.slider("Target number of cards", min_value=5, max_value=40, value=15, key="ai_num_cards")

    source_type = st.radio(
        "Source type:",
        ["📄 PDF / Word / Text file", "🌐 Web URL", "✏️ Paste text"],
        horizontal=True,
        key="ai_source_type",
    )

    source_text = ""
    cards: list[dict] = []

    if source_type == "📄 PDF / Word / Text file":
        uploaded = st.file_uploader(
            "Upload file",
            type=["pdf", "docx", "txt"],
            key="ai_file_upload",
        )
        if uploaded and st.button("🚀 Generate Cards", type="primary", key="ai_gen_file"):
            with st.spinner("Extracting text and generating cards…"):
                from core.ai_deck_generator import generate_from_file
                source_text, cards = generate_from_file(uploaded, num_cards)

    elif source_type == "🌐 Web URL":
        url = st.text_input("Enter URL:", placeholder="https://example.com/study-guide", key="ai_url")
        if url and st.button("🚀 Generate Cards", type="primary", key="ai_gen_url"):
            with st.spinner("Fetching page and generating cards…"):
                from core.ai_deck_generator import generate_from_url
                source_text, cards = generate_from_url(url, num_cards)

    elif source_type == "✏️ Paste text":
        pasted = st.text_area("Paste your study material here:", height=200, key="ai_paste")
        if pasted.strip() and st.button("🚀 Generate Cards", type="primary", key="ai_gen_text"):
            with st.spinner("Generating cards…"):
                from core.ai_deck_generator import generate_from_text
                source_text, cards = generate_from_text(pasted, num_cards)

    # Store generated cards in session state so they persist across reruns
    if cards:
        st.session_state["ai_generated_cards"] = cards
        st.session_state["ai_generated_for_deck"] = manage_deck

    stored_cards = st.session_state.get("ai_generated_cards", [])
    stored_deck  = st.session_state.get("ai_generated_for_deck", manage_deck)

    if stored_cards:
        st.success(f"✅ Generated {len(stored_cards)} cards.")

        with st.expander("👁️ Preview all generated cards", expanded=True):
            for i, card in enumerate(stored_cards):
                st.markdown(f"**Card {i+1}** — `{card.get('type', 'flashcard')}`")
                st.write(f"**Q:** {card.get('question', '')}")
                st.write(f"**A:** {card.get('answer', '')}")
                if card.get("options"):
                    for j, opt in enumerate(card["options"]):
                        prefix = "✅" if j == card.get("correct_index") else "⬜"
                        st.write(f"  {prefix} {opt}")
                if card.get("correct_answer") is not None:
                    st.write(f"  Correct: {'TRUE' if card['correct_answer'] else 'FALSE'}")
                st.divider()

        st.markdown("### 💾 Save Options")
        save_col1, save_col2, save_col3 = st.columns(3)

        with save_col1:
            if st.button(f"✅ Add to '{stored_deck}'", type="primary", key="ai_save_deck"):
                _save_cards_to_deck(stored_deck, stored_cards)
                st.success(f"✅ Added {len(stored_cards)} cards to '{stored_deck}'!")
                del st.session_state["ai_generated_cards"]
                st.rerun()

        with save_col2:
            new_deck_name = st.text_input("Or save to new deck:", key="ai_new_deck_name")
            if new_deck_name.strip() and st.button("➕ Create & Save", key="ai_save_new_deck"):
                create_deck(new_deck_name.strip())
                _save_cards_to_deck(new_deck_name.strip(), stored_cards)
                st.success(f"✅ Created deck '{new_deck_name}' with {len(stored_cards)} cards!")
                del st.session_state["ai_generated_cards"]
                st.rerun()

        with save_col3:
            json_bytes = json.dumps(stored_cards, indent=2).encode("utf-8")
            st.download_button(
                "⬇️ Download JSON",
                data=json_bytes,
                file_name="generated_deck.json",
                mime="application/json",
                width='stretch',
                key="ai_download_json",
            )
            if stored_cards:
                buf = io.StringIO()
                fields = ["question", "answer", "type"]
                writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(stored_cards)
                st.download_button(
                    "⬇️ Download CSV",
                    data=buf.getvalue().encode("utf-8"),
                    file_name="generated_deck.csv",
                    mime="text/csv",
                    width='stretch',
                    key="ai_download_csv",
                )

        if st.button("🗑️ Discard & start over", key="ai_discard"):
            del st.session_state["ai_generated_cards"]
            st.rerun()


# ── Duplicate Detection ───────────────────────────────────────────────────────

def _render_duplicates(manage_deck: str):
    st.subheader("🔍 Duplicate Detection")
    if st.button("Find Duplicates"):
        duplicates = find_duplicate_cards(manage_deck)
        if duplicates:
            st.warning(f"Found {len(duplicates)} duplicate card(s)!")
            for dup in duplicates:
                with st.expander(f"Duplicate: {dup['question'][:50]}..."):
                    st.write(f"**Question:** {dup['question']}")
                    st.write(f"**Answer:** {dup['answer']}")
                    st.write(f"**Index:** {dup['index']} (original at index {dup['original_index']})")
                    if st.button("Delete this duplicate", key=f"delete_dup_{dup['index']}"):
                        if delete_card(manage_deck, dup["index"]):
                            st.success("Duplicate deleted!")
                        else:
                            st.error("Failed to delete card")
        else:
            st.success("No duplicates found!")


# ── Browse & Edit ─────────────────────────────────────────────────────────────

def _render_browse(manage_deck: str, indexed_cards):
    st.subheader("📋 Browse & Edit Cards")

    if not indexed_cards:
        st.info("No cards in this deck")
        return

    st.write(f"Total cards in '{manage_deck}': {len(indexed_cards)}")

    search_term = st.text_input("Search cards:", key="card_search")
    filtered = indexed_cards
    if search_term:
        s = search_term.lower()
        filtered = [
            (idx, card) for idx, card in indexed_cards
            if s in card.question.lower() or s in card.answer.lower()
        ]
    st.write(f"Showing {len(filtered)} card(s)")

    for idx, card in filtered:
        with st.expander(f"Card #{idx + 1}: {card.question[:60]}..."):
            st.write(f"**Question:** {card.question}")
            st.write(f"**Answer:** {card.answer}")
            if not card.feedback.is_empty():
                st.caption("💬 " + (card.feedback.text or "")[:80])

            # ── Edit full card ────────────────────────────────────────────────
            card_edit_key = f"editing_card_{idx}"
            if st.button("✏️ Edit Card", key=f"card_edit_btn_{idx}"):
                st.session_state[card_edit_key] = not st.session_state.get(card_edit_key, False)

            if st.session_state.get(card_edit_key, False):
                with st.form(key=f"card_edit_form_{idx}"):
                    st.markdown("**Edit Card Fields**")
                    new_question    = st.text_area("Question", value=card.question, height=80)
                    new_answer      = st.text_input("✅ Correct Answer", value=card.answer)

                    st.markdown("**❌ Wrong Answers / Distractors**")
                    num_slots = max(4, len(card.wrong_answers))
                    new_wrong = []
                    for wi in range(num_slots):
                        val = st.text_input(
                            f"Wrong Answer {wi + 1}",
                            value=card.wrong_answers[wi] if wi < len(card.wrong_answers) else "",
                            key=f"ce_w_{idx}_{wi}",
                        )
                        new_wrong.append(val)

                    new_hint        = st.text_input("💡 Hint (optional)", value=card.hint or "")
                    new_tags_raw    = st.text_input("🏷️ Tags (comma-separated)", value=", ".join(card.tags))
                    new_image_url   = st.text_input("🖼️ Image URL (optional)", value=card.image_url or "")
                    new_explanation = st.text_area("📖 Explanation", value=card.explanation or "", height=80)

                    save_card_btn = st.form_submit_button("💾 Save Card", type="primary")
                    if save_card_btn:
                        updated = None
                        if not (new_question or "").strip():
                            st.error("❌ Question cannot be empty.")
                        elif not (new_answer or "").strip():
                            st.error("❌ Answer cannot be empty.")
                        else:
                            updated = Card(
                                question=new_question or "",
                                answer=new_answer or "",
                                wrong_answers=[w for w in new_wrong if w.strip()],
                                hint=new_hint.strip() or None,
                                tags=[t.strip() for t in new_tags_raw.split(",") if t.strip()],
                                image_url=new_image_url.strip() or None,
                                explanation=new_explanation.strip() or None,
                                feedback=card.feedback,
                            )
                            if _save_card(manage_deck, idx, updated):
                                st.session_state[card_edit_key] = False
                                st.success("✅ Card saved!")

            # ── Edit feedback only ────────────────────────────────────────────
            edit_key = f"editing_{idx}"
            if st.button("✏️ Edit Feedback", key=f"edit_btn_{idx}"):
                st.session_state[edit_key] = not st.session_state.get(edit_key, False)

            if st.session_state.get(edit_key, False):
                fb = card.feedback
                with st.form(key=f"feedback_form_{idx}"):
                    st.markdown("**Edit Feedback**")
                    new_text       = st.text_area("Explanation / Feedback", value=fb.text or "", height=100)
                    new_images_raw = st.text_area(
                        "Image URLs (one per line)",
                        value="\n".join(fb.images),
                        height=70,
                    )
                    st.write("**Reference Links** (up to 3):")
                    new_links = []
                    for li in range(3):
                        ex_label = fb.links[li].label if li < len(fb.links) else ""
                        ex_url   = fb.links[li].url   if li < len(fb.links) else ""
                        lc1, lc2 = st.columns([2, 3])
                        with lc1:
                            ll = st.text_input(f"Label {li+1}", value=ex_label, key=f"fb_ll_{idx}_{li}")
                        with lc2:
                            lu = st.text_input(f"URL {li+1}", value=ex_url, key=f"fb_lu_{idx}_{li}")
                        if lu.strip():
                            new_links.append(CardLink(label=ll.strip(), url=lu.strip()))

                    save_btn = st.form_submit_button("💾 Save Feedback", type="primary")
                    if save_btn:
                        updated_feedback = CardFeedback(
                            text=new_text.strip() or None,
                            images=[u.strip() for u in new_images_raw.splitlines() if u.strip()],
                            links=new_links,
                        )
                        updated_card = card.model_copy(update={"feedback": updated_feedback})
                        if _save_card(manage_deck, idx, updated_card):
                            st.session_state[edit_key] = False
                            st.success("✅ Feedback saved!")

            # ── Delete with confirmation ───────────────────────────────────────
            if f"confirm_delete_{idx}" not in st.session_state:
                st.session_state[f"confirm_delete_{idx}"] = False

            if not st.session_state[f"confirm_delete_{idx}"]:
                if st.button("🗑️ Delete", key=f"delete_btn_{idx}"):
                    st.session_state[f"confirm_delete_{idx}"] = True
            else:
                st.warning("⚠️ Are you sure you want to delete this card?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Yes, delete", key=f"confirm_yes_{idx}", type="primary"):
                        if delete_card(manage_deck, idx):
                            st.session_state[f"confirm_delete_{idx}"] = False
                            st.success("Card deleted!")
                            if "cards" in st.session_state:
                                del st.session_state["cards"]
                        else:
                            st.error("Failed to delete card")
                with col2:
                    if st.button("✗ Cancel", key=f"confirm_no_{idx}"):
                        st.session_state[f"confirm_delete_{idx}"] = False


# ── Rename Deck ───────────────────────────────────────────────────────────────

def _render_rename_deck(manage_deck: str, username: str | None):
    st.subheader("✏️ Rename Deck")

    # Admin-only gate
    if username:
        from data.user_store import get_user
        user_doc = get_user(username)
        if not user_doc or not user_doc.get("is_admin"):
            st.warning("Admin access required to rename decks.")
            return

    st.write(f"Current name: **{manage_deck}**")

    with st.form("rename_deck_form"):
        new_name = st.text_input(
            "New deck name",
            placeholder=manage_deck,
            help="Must be unique. This cannot be undone without renaming again.",
        )
        confirm = st.checkbox("I understand this will rename the deck for all users.")
        submit = st.form_submit_button("✏️ Rename Deck", type="primary")

        if submit:
            if not confirm:
                st.warning("Please check the confirmation box to proceed.")
            else:
                ok, msg = _rename_deck(manage_deck, new_name)
                if ok:
                    st.success(f"✅ {msg}")
                    # Clear selectbox cache so the new name appears immediately
                    if "manage_deck_select" in st.session_state:
                        del st.session_state["manage_deck_select"]
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ── User Access Management ────────────────────────────────────────────────────

def _render_user_access(username: str | None):
    st.subheader("👥 User Access Management")

    if not username:
        st.info("Pass username to manage_tab to enable access management.")
        return

    from data.user_store import get_user
    current = get_user(username)
    if not current or not current.get("is_admin"):
        st.warning("Admin access required.")
        return

    from data.user_store import get_all_usernames
    from core.paywall import grant_pro, revoke_pro

    st.markdown("Grant or revoke **Pro** access for users.")

    all_users = get_all_usernames()
    target = st.selectbox("Select user:", all_users, key="access_target_user")

    if target:
        target_doc = get_user(target)
        is_pro   = target_doc.get("is_pro", False)   if target_doc else False
        is_admin = target_doc.get("is_admin", False) if target_doc else False

        st.write(f"**Current tier:** {'Admin' if is_admin else 'Pro' if is_pro else 'Free'}")

        col1, col2 = st.columns(2)
        with col1:
            if not is_pro and not is_admin:
                if st.button("⬆️ Grant Pro", key="grant_pro_btn", type="primary"):
                    if grant_pro(target):
                        st.success(f"✅ Granted Pro to {target}")
                        st.rerun()
        with col2:
            if is_pro:
                if st.button("⬇️ Revoke Pro", key="revoke_pro_btn"):
                    if revoke_pro(target):
                        st.success(f"✅ Revoked Pro from {target}")
                        st.rerun()