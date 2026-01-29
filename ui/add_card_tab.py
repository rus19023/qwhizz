# ui/add_card_tab.py

import streamlit as st
from data.deck_store import get_deck_names, add_card


def render_add_card_tab():
    """Render the add card tab"""
    st.subheader("Add a New Flashcard")
    
    # Option to select existing deck or create new one
    deck_option = st.radio(
        "Choose deck:",
        options=["Add to existing deck", "Create new deck"]
    )
    
    if deck_option == "Add to existing deck":
        existing_decks = get_deck_names()
        if existing_decks:
            add_to_deck = st.selectbox(
                "Select deck:",
                options=existing_decks,
                key="add_card_deck"
            )
        else:
            st.warning("No decks exist yet. Please create a new deck below.")
            deck_option = "Create new deck"
    
    if deck_option == "Create new deck":
        add_to_deck = st.text_input("New deck name:", key="new_deck_name")
    
    with st.form("add_card_form"):
        new_question = st.text_area("Question", height=100)
        new_answer = st.text_area("Answer", height=100)

        submitted = st.form_submit_button("Add card")

        if submitted:
            if deck_option == "Create new deck" and not add_to_deck.strip():
                st.error("Please enter a deck name.")
            elif not new_question.strip() or not new_answer.strip():
                st.error("Both question and answer are required.")
            else:
                add_card(
                    add_to_deck.strip(),
                    new_question.strip(),
                    new_answer.strip()
                )

                st.success(f"Flashcard added to '{add_to_deck.strip()}'!")
                
                # Preserve user login
                if "user" in st.query_params:
                    user_param = st.query_params["user"]
                    st.query_params.clear()
                    st.query_params["user"] = user_param
                
                st.rerun()