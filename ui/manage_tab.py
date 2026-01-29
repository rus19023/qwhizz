# ui/manage_tab.py

import streamlit as st
from data.deck_store import (
    get_deck_names,
    find_duplicate_cards,
    delete_card,
    get_all_cards_with_indices
)


def render_manage_tab():
    """Render the manage decks tab"""
    st.subheader("🗂️ Manage Decks")
    
    manage_deck = st.selectbox(
        "Select deck to manage:",
        options=get_deck_names(),
        key="manage_deck_select"
    )
    
    st.divider()
    
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
                            st.rerun()
                        else:
                            st.error("Failed to delete card")
        else:
            st.success("No duplicates found!")
    
    st.divider()
    
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
                if search_term.lower() in card["question"].lower() 
                or search_term.lower() in card["answer"].lower()
            ]
        
        st.write(f"Showing {len(filtered_cards)} card(s)")
        
        for card in filtered_cards:
            with st.expander(f"Card #{card['index'] + 1}: {card['question'][:60]}..."):
                st.write(f"**Question:** {card['question']}")
                st.write(f"**Answer:** {card['answer']}")
                
                # Deletion with confirmation
                if f"confirm_delete_{card['index']}" not in st.session_state:
                    st.session_state[f"confirm_delete_{card['index']}"] = False
                
                if not st.session_state[f"confirm_delete_{card['index']}"]:
                    if st.button("🗑️ Delete", key=f"delete_btn_{card['index']}"):
                        st.session_state[f"confirm_delete_{card['index']}"] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Are you sure you want to delete this card?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Yes, delete", key=f"confirm_yes_{card['index']}", type="primary"):
                            if delete_card(manage_deck, card['index']):
                                st.session_state[f"confirm_delete_{card['index']}"] = False
                                st.success("Card deleted!")
                                # Clear deck state to reload
                                if "cards" in st.session_state:
                                    del st.session_state["cards"]
                                st.rerun()
                            else:
                                st.error("Failed to delete card")
                    with col2:
                        if st.button("✗ Cancel", key=f"confirm_no_{card['index']}"):
                            st.session_state[f"confirm_delete_{card['index']}"] = False
                            st.rerun()
    else:
        st.info("No cards in this deck")