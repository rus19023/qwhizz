# ui/manage_tab.py

import traceback
import streamlit as st

from data.deck_store import (
    get_deck_names,
    find_duplicate_cards,
    delete_card,
    get_all_cards_with_indices
)


#st.error("DEBUG: manage_tab loaded")

def render_manage_tab():
    #st.error("DEBUG: render_manage_tab started")
    try:
        """Render the manage decks tab"""
        st.subheader("🗂️ Manage Decks")
        
        manage_deck = st.selectbox(
            "Select deck to manage:",
            options=get_deck_names(),
            key="manage_deck_select"
        )

        st.error(f"DEBUG: manage_deck = {manage_deck}")
        all_cards = get_all_cards_with_indices(manage_deck)
        st.error(f"DEBUG: got {len(all_cards)} cards")
        
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
                               #st.rerun()
                            else:
                                st.error("Failed to delete card")
            else:
                st.success("No duplicates found!")
        
        # Card Browser & Deletion
        st.subheader("📋 Browse & Delete Cards")
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

                    edit_key = f"editing_{card['index']}"
                    if st.button("✏️ Edit Feedback", key=f"edit_btn_{card['index']}"):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                       #st.rerun()

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
                                   #st.rerun()

                    # Deletion with confirmation
                    if f"confirm_delete_{card['index']}" not in st.session_state:
                        st.session_state[f"confirm_delete_{card['index']}"] = False
                    
                    if not st.session_state[f"confirm_delete_{card['index']}"]:
                        if st.button("🗑️ Delete", key=f"delete_btn_{card['index']}"):
                            st.session_state[f"confirm_delete_{card['index']}"] = True
                           #st.rerun()
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
                                   #st.rerun()
                                else:
                                    st.error("Failed to delete card")
                        with col2:
                            if st.button("✗ Cancel", key=f"confirm_no_{card['index']}"):
                                st.session_state[f"confirm_delete_{card['index']}"] = False
                               #st.rerun()
        else:
            st.info("No cards in this deck")

    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())