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
    delete_deck,
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
        st.error("❌ Could not find deck in database.")
        return False
    try:
        cards_list = deck_doc["cards"]
        cards_list[index] = card.to_dict()
        db.decks.update_one({"_id": manage_deck}, {"$set": {"cards": cards_list}})
        return True
    except Exception as e:
        st.error(f"❌ Failed to save card: {e}")
        return False


def _rename_deck(old_name: str, new_name: str) -> tuple[bool, str]:
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

    new_doc = {**old_doc, "_id": new_name}
    db.decks.insert_one(new_doc)
    db.decks.delete_one({"_id": old_name})
    return True, f"Deck renamed to '{new_name}'."


def _deduplicate_deck(deck_name: str) -> tuple[int, int]:
    """
    Remove duplicate cards from a deck, keeping the first occurrence.
    Duplicates are matched on (question, answer) lowercased and stripped.
    Returns (cards_before, cards_after).
    """
    from data.db import get_database
    db = get_database()

    deck_doc = db.decks.find_one({"_id": deck_name})
    if not deck_doc:
        return 0, 0

    cards = deck_doc.get("cards", [])
    cards_before = len(cards)
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []

    for card in cards:
        key = (
            str(card.get("question", "")).strip().lower(),
            str(card.get("answer",   "")).strip().lower(),
        )
        if key not in seen:
            seen.add(key)
            unique.append(card)

    db.decks.update_one({"_id": deck_name}, {"$set": {"cards": unique}})
    return cards_before, len(unique)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _render_card_preview(cards: list):
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


def _save_cards_to_deck(deck_name: str, cards: list[dict]) -> bool:
    try:
        from data.db import get_database
        db = get_database()
        deck_doc = db.decks.find_one({"_id": deck_name})
        if deck_doc:
            existing = deck_doc.get("cards", [])
            existing.extend(cards)
            db.decks.update_one({"_id": deck_name}, {"$set": {"cards": existing}})
        else:
            db.decks.insert_one({"_id": deck_name, "cards": cards})
        return True
    except Exception as e:
        st.error(f"❌ Failed to save cards: {e}")
        return False


def _existing_questions(deck_name: str) -> set[str]:
    """Return a set of lowercased stripped questions already in the deck."""
    from data.db import get_database
    db = get_database()
    deck_doc = db.decks.find_one({"_id": deck_name})
    if not deck_doc:
        return set()
    return {
        str(c.get("question", "")).strip().lower()
        for c in deck_doc.get("cards", [])
    }


# ── Main tab ──────────────────────────────────────────────────────────────────

def render_manage_tab(username: str | None = None):
    try:
        st.subheader("🗂️ Manage Decks")

        if username and not require_feature("manage_decks", username):
            return

        manage_deck = st.selectbox(
            "Select deck to manage:",
            options=get_deck_names(),
            key="manage_deck_select",
        )

        indexed_cards = _cards_from_deck(manage_deck)

        is_admin = False
        if username:
            from data.user_store import get_user
            user_doc = get_user(username)
            is_admin = bool(user_doc.get("is_admin", False)) if user_doc else False

        manage_deck_tabs = [
            TabSpec("➕ Create Deck",    lambda: _render_create_deck(),                                admin_only=True),
            TabSpec("📤 Export",         lambda: _render_export(manage_deck, indexed_cards),           admin_only=True),
            TabSpec("📥 Import",         lambda: _render_import(manage_deck),                          admin_only=True),
            TabSpec("💡 AI Enrich Deck", lambda: render_ai_enrich_section(manage_deck, indexed_cards), admin_only=True),
            TabSpec("🔍 Duplicates",     lambda: _render_duplicates(manage_deck),                      admin_only=True),
            TabSpec("📋 Browse & Edit",  lambda: _render_browse(manage_deck, indexed_cards),           admin_only=True),
            TabSpec("✏️ Rename Deck",    lambda: _render_rename_deck(manage_deck, username),           admin_only=True),
            TabSpec("🗑️ Delete Deck",    lambda: _render_delete_deck(manage_deck),                     admin_only=True),
            TabSpec("👥 User Access",    lambda: _render_user_access(username),                        admin_only=True),
        ]

        render_tabs(manage_deck_tabs, is_admin=is_admin)

    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())


# ── Create Deck ───────────────────────────────────────────────────────────────

def _render_create_deck():
    st.subheader("➕ Create New Deck")
    with st.form("create_deck_form"):
        new_name = st.text_input(
            "Deck name",
            placeholder="e.g. Biology Chapter 5",
            max_chars=100,
        )
        submit = st.form_submit_button("Create Deck", type="primary")
        if submit:
            name = new_name.strip()
            if not name:
                st.error("Deck name cannot be empty.")
            elif name in get_deck_names():
                st.error(f"A deck named '{name}' already exists.")
            else:
                if create_deck(name):
                    st.success(f"Created deck: **{name}**")
                    st.rerun()
                else:
                    st.error("Failed to create deck.")


# ── Delete Deck ───────────────────────────────────────────────────────────────

def _render_delete_deck(manage_deck: str):
    st.subheader("🗑️ Delete Deck")

    from data.db import get_database
    db = get_database()
    deck_doc = db.decks.find_one({"_id": manage_deck})
    card_count = len(deck_doc.get("cards", [])) if deck_doc else 0

    st.error(
        f"⚠️ **Danger Zone** — This will permanently delete **{manage_deck}** "
        f"and all **{card_count} cards**. This cannot be undone."
    )

    st.write(f"Type the deck name **`{manage_deck}`** to confirm:")
    typed = st.text_input("Deck name confirmation", key="delete_deck_type_confirm", label_visibility="collapsed")

    name_matches = typed.strip() == manage_deck.strip()

    if not name_matches and typed:
        st.warning("Name doesn't match — check your spelling.")

    if st.button("🗑️ Permanently Delete Deck", type="primary", disabled=not name_matches, key="delete_deck_btn"):
        ok = delete_deck(manage_deck)
        if ok:
            st.success(f"Deleted deck: **{manage_deck}**")
            if "manage_deck_select" in st.session_state:
                del st.session_state["manage_deck_select"]
            if "delete_deck_type_confirm" in st.session_state:
                del st.session_state["delete_deck_type_confirm"]
            st.rerun()
        else:
            st.error("Failed to delete deck.")


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

        if not parsed:
            return

        # ── Duplicate detection ───────────────────────────────────────────────
        existing_qs = _existing_questions(manage_deck)
        new_cards    = [c for c in parsed if c.question.strip().lower() not in existing_qs]
        dupe_cards   = [c for c in parsed if c.question.strip().lower() in existing_qs]

        st.write(f"**{len(parsed)}** cards in file — "
                 f"**{len(new_cards)}** new, "
                 f"**{len(dupe_cards)}** already exist in deck")

        if dupe_cards:
            with st.expander(f"⚠️ {len(dupe_cards)} duplicate question(s) — will be skipped"):
                for c in dupe_cards[:10]:
                    st.caption(f"• {c.question[:80]}")
                if len(dupe_cards) > 10:
                    st.caption(f"...and {len(dupe_cards) - 10} more")

        if not new_cards:
            st.info("All cards already exist in this deck. Nothing to import.")
            return

        st.success(f"Ready to import {len(new_cards)} new card(s).")
        _render_card_preview(new_cards)

        if st.button("✅ Confirm Import", type="primary", key="confirm_import_json"):
            _save_cards_to_deck(manage_deck, [c.to_dict() for c in new_cards])
            st.success(f"✅ Imported {len(new_cards)} cards into '{manage_deck}'!")
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
                if _save_cards_to_deck(stored_deck, stored_cards):
                    st.toast(f"✅ Added {len(stored_cards)} cards to '{stored_deck}'!", icon="✅")
                    del st.session_state["ai_generated_cards"]
                    st.rerun()

        with save_col2:
            new_deck_name = st.text_input("Or save to new deck:", key="ai_new_deck_name")
            if new_deck_name.strip() and st.button("➕ Create & Save", key="ai_save_new_deck"):
                create_deck(new_deck_name.strip())
                if _save_cards_to_deck(new_deck_name.strip(), stored_cards):
                    st.toast(f"✅ Created deck '{new_deck_name}' with {len(stored_cards)} cards!", icon="✅")
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

    from data.db import get_database
    db = get_database()
    deck_doc = db.decks.find_one({"_id": manage_deck})
    card_count = len(deck_doc.get("cards", [])) if deck_doc else 0

    st.write(f"**{manage_deck}** — {card_count} cards total")

    # ── Auto-deduplicate ──────────────────────────────────────────────────────
    st.markdown("#### ⚡ Auto-Deduplicate")
    st.write("Instantly removes all duplicate cards, keeping the first occurrence of each.")

    confirm_dedup = st.checkbox(
        "I want to remove all duplicate cards automatically",
        key="dedup_confirm",
    )
    if st.button("Remove All Duplicates", type="primary", disabled=not confirm_dedup, key="dedup_btn"):
        before, after = _deduplicate_deck(manage_deck)
        removed = before - after
        if removed == 0:
            st.info("No duplicates found — deck is already clean.")
        else:
            st.success(f"✅ Removed {removed} duplicate card(s). Deck now has {after} cards.")
        st.rerun()

    st.divider()

    # ── Manual review ─────────────────────────────────────────────────────────
    st.markdown("#### 🔎 Review Duplicates Manually")
    if st.button("Find Duplicates", key="find_dupes_btn"):
        duplicates = find_duplicate_cards(manage_deck)
        if duplicates:
            st.warning(f"Found {len(duplicates)} duplicate card(s).")
            for dup in duplicates:
                with st.expander(f"Duplicate: {dup['question'][:60]}..."):
                    st.write(f"**Question:** {dup['question']}")
                    st.write(f"**Answer:** {dup['answer']}")
                    st.caption(f"Index {dup['index']} — duplicate of index {dup['original_index']}")
                    if st.button("Delete this duplicate", key=f"delete_dup_{dup['index']}"):
                        if delete_card(manage_deck, dup["index"]):
                            st.toast("✅ Duplicate deleted.", icon="✅")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete card.")
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
                            st.toast("🗑️ Card deleted.", icon="🗑️")
                            if "cards" in st.session_state:
                                del st.session_state["cards"]
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete card.")
                with col2:
                    if st.button("✗ Cancel", key=f"confirm_no_{idx}"):
                        st.session_state[f"confirm_delete_{idx}"] = False


# ── Rename Deck ───────────────────────────────────────────────────────────────

def _render_rename_deck(manage_deck: str, username: str | None):
    st.subheader("✏️ Rename Deck")

    if username:
        from data.user_store import get_user
        user_doc = get_user(username)
        if not user_doc or not user_doc.get("is_admin"):
            st.warning("Admin access required to rename decks.")
            return

    all_decks = get_deck_names()
    deck_to_rename = st.selectbox(
        "Choose deck to rename",
        all_decks,
        index=all_decks.index(manage_deck) if manage_deck in all_decks else 0,
        key="rename_deck_selector",
    )
    st.write(f"Current name: **{deck_to_rename}**")

    with st.form("rename_deck_form"):
        new_name = st.text_input(
            "New deck name",
            placeholder=deck_to_rename,
            help="Must be unique. This cannot be undone without renaming again.",
        )
        confirm = st.checkbox("I understand this will rename the deck for all users.")
        submit  = st.form_submit_button("✏️ Rename Deck", type="primary")

        if submit:
            if not confirm:
                st.warning("Please check the confirmation box to proceed.")
            else:
                ok, msg = _rename_deck(deck_to_rename, new_name)
                if ok:
                    st.success(f"✅ {msg}")
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