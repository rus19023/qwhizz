# ui/manage_tab.py

import traceback
import streamlit as st

from data.deck_store import (
    get_deck_names,
    find_duplicate_cards,
    delete_card,
    get_all_cards_with_indices
)


def render_manage_tab():
    try:
        """Render the manage decks tab"""
        st.subheader("🗂️ Manage Decks")
        
        manage_deck = st.selectbox(
            "Select deck to manage:",
            options=get_deck_names(),
            key="manage_deck_select"
        )

        all_cards = get_all_cards_with_indices(manage_deck)
        
        # Duplicate Detection
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
                        
                        if st.button(f"Delete this duplicate", key=f"delete_dup_{dup['index']}"):
                            if delete_card(manage_deck, dup['index']):
                                st.success("Duplicate deleted!")
                            else:
                                st.error("Failed to delete card")
            else:
                st.success("No duplicates found!")
        
        # Card Browser & Deletion
        st.subheader("📋 Browse & Edit Cards")
        all_cards = get_all_cards_with_indices(manage_deck)
        
        if all_cards:
            st.write(f"Total cards in '{manage_deck}': {len(all_cards)}")
            
            # Search/filter
            search_term = st.text_input("Search cards:", key="card_search")
            
            filtered_cards = all_cards
            if search_term:
                filtered_cards = [
                    card for card in all_cards
                    if search_term.lower() in (card.get("question") or "").lower() 
                    or search_term.lower() in (card.get("answer") or "").lower()
                ]
            
            st.write(f"Showing {len(filtered_cards)} card(s)")
            
            for card in filtered_cards:
                question = card.get("question") or ""
                answer = card.get("answer") or ""
                with st.expander(f"Card #{card['index'] + 1}: {question[:60]}..."):
                    st.write(f"**Question:** {question}")
                    st.write(f"**Answer:** {answer}")
                    
                    # Show existing feedback if present
                    feedback = card.get("feedback", {})
                    if feedback:
                        st.caption("💬 Feedback: " + feedback.get("text", "")[:80])

                    # ── EDIT CARD BUTTON ──────────────────────────────────────
                    card_edit_key = f"editing_card_{card['index']}"
                    if st.button("✏️ Edit Card", key=f"card_edit_btn_{card['index']}"):
                        st.session_state[card_edit_key] = not st.session_state.get(card_edit_key, False)

                    if st.session_state.get(card_edit_key, False):
                        with st.form(key=f"card_edit_form_{card['index']}"):
                            st.markdown("**Edit Card Fields**")

                            new_question = st.text_area(
                                "Question",
                                value=card.get("question", ""),
                                height=80,
                                key=f"ce_q_{card['index']}"
                            )
                            new_answer = st.text_input(
                                "✅ Correct Answer",
                                value=card.get("answer", ""),
                                key=f"ce_a_{card['index']}"
                            )

                            # Handle wrong answers / distractors
                            # They may be stored as a list in various field names
                            wrong_answers = (
                                card.get("wrong_answers")
                                or card.get("distractors")
                                or card.get("incorrect_answers")
                                or []
                            )
                            # Detect which field name is actually used
                            if card.get("wrong_answers") is not None:
                                wrong_field = "wrong_answers"
                            elif card.get("distractors") is not None:
                                wrong_field = "distractors"
                            elif card.get("incorrect_answers") is not None:
                                wrong_field = "incorrect_answers"
                            else:
                                wrong_field = "wrong_answers"  # default for new cards

                            st.markdown("**❌ Wrong Answers / Distractors**")

                            # Always show at least 4 distractor slots
                            num_slots = max(4, len(wrong_answers))
                            new_wrong = []
                            for wi in range(num_slots):
                                existing_val = wrong_answers[wi] if wi < len(wrong_answers) else ""
                                val = st.text_input(
                                    f"Wrong Answer {wi + 1}",
                                    value=existing_val,
                                    key=f"ce_w_{card['index']}_{wi}"
                                )
                                new_wrong.append(val)

                            # Optional extra fields
                            new_hint = st.text_input(
                                "💡 Hint (optional)",
                                value=card.get("hint", ""),
                                key=f"ce_hint_{card['index']}"
                            )
                            new_tags_raw = st.text_input(
                                "🏷️ Tags (comma-separated, optional)",
                                value=", ".join(card.get("tags", [])),
                                key=f"ce_tags_{card['index']}"
                            )

                            save_card_btn = st.form_submit_button("💾 Save Card", type="primary")
                            if save_card_btn:
                                from data.db import get_database
                                db = get_database()
                                deck_doc = db.decks.find_one({"_id": manage_deck})
                                if deck_doc:
                                    cards_list = deck_doc["cards"]
                                    target = cards_list[card['index']]

                                    # Apply edits
                                    target["question"] = new_question.strip()
                                    target["answer"] = new_answer.strip()

                                    # Save non-empty distractors only
                                    cleaned_wrong = [w.strip() for w in new_wrong if w.strip()]
                                    target[wrong_field] = cleaned_wrong

                                    if new_hint.strip():
                                        target["hint"] = new_hint.strip()
                                    elif "hint" in target:
                                        target.pop("hint")

                                    new_tags = [t.strip() for t in new_tags_raw.split(",") if t.strip()]
                                    if new_tags:
                                        target["tags"] = new_tags
                                    elif "tags" in target:
                                        target.pop("tags")

                                    cards_list[card['index']] = target
                                    db.decks.update_one(
                                        {"_id": manage_deck},
                                        {"$set": {"cards": cards_list}}
                                    )
                                    st.session_state[card_edit_key] = False
                                    st.success("✅ Card saved!")
                                else:
                                    st.error("Could not find deck in database.")

                    # ── EDIT FEEDBACK BUTTON ──────────────────────────────────
                    edit_key = f"editing_{card['index']}"
                    if st.button("✏️ Edit Feedback", key=f"edit_btn_{card['index']}"):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                    if st.session_state.get(edit_key, False):
                        with st.form(key=f"feedback_form_{card['index']}"):
                            st.markdown("**Edit Feedback**")
                            existing_text = feedback.get("text", "")
                            existing_images = "\n".join(feedback.get("images", []))
                            existing_links = feedback.get("links", [])

                            new_text = st.text_area("Explanation / Feedback", value=existing_text, height=100, key=f"fb_text_{card['index']}")
                            new_images_raw = st.text_area("Image URLs (one per line)", value=existing_images, height=70, key=f"fb_images_{card['index']}")

                            st.write("**Reference Links** (up to 3):")
                            new_links = []
                            for li in range(3):
                                ex_label = existing_links[li]["label"] if li < len(existing_links) else ""
                                ex_url = existing_links[li]["url"] if li < len(existing_links) else ""
                                lc1, lc2 = st.columns([2, 3])
                                with lc1:
                                    ll = st.text_input(f"Label {li+1}", value=ex_label, key=f"fb_ll_{card['index']}_{li}")
                                with lc2:
                                    lu = st.text_input(f"URL {li+1}", value=ex_url, key=f"fb_lu_{card['index']}_{li}")
                                if lu.strip():
                                    new_links.append({"label": ll.strip(), "url": lu.strip()})

                            save_btn = st.form_submit_button("💾 Save Feedback", type="primary")
                            if save_btn:
                                from data.db import get_database
                                new_feedback = {}
                                if new_text.strip():
                                    new_feedback["text"] = new_text.strip()
                                imgs = [u.strip() for u in new_images_raw.splitlines() if u.strip()]
                                if imgs:
                                    new_feedback["images"] = imgs
                                if new_links:
                                    new_feedback["links"] = new_links

                                db = get_database()
                                deck_doc = db.decks.find_one({"_id": manage_deck})
                                if deck_doc:
                                    cards_list = deck_doc["cards"]
                                    cards_list[card['index']]["feedback"] = new_feedback
                                    db.decks.update_one({"_id": manage_deck}, {"$set": {"cards": cards_list}})
                                    st.session_state[edit_key] = False
                                    st.success("✅ Feedback saved!")

                    # ── DELETE ────────────────────────────────────────────────
                    if f"confirm_delete_{card['index']}" not in st.session_state:
                        st.session_state[f"confirm_delete_{card['index']}"] = False
                    
                    if not st.session_state[f"confirm_delete_{card['index']}"]:
                        if st.button("🗑️ Delete", key=f"delete_btn_{card['index']}"):
                            st.session_state[f"confirm_delete_{card['index']}"] = True
                    else:
                        st.warning("⚠️ Are you sure you want to delete this card?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✓ Yes, delete", key=f"confirm_yes_{card['index']}", type="primary"):
                                if delete_card(manage_deck, card['index']):
                                    st.session_state[f"confirm_delete_{card['index']}"] = False
                                    st.success("Card deleted!")
                                    if "cards" in st.session_state:
                                        del st.session_state["cards"]
                                else:
                                    st.error("Failed to delete card")
                        with col2:
                            if st.button("✗ Cancel", key=f"confirm_no_{card['index']}"):
                                st.session_state[f"confirm_delete_{card['index']}"] = False
        else:
            st.info("No cards in this deck")

    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())