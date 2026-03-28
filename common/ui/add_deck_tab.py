import streamlit as st
from data.deck_store import create_deck, get_deck_names


def render_add_deck_tab() -> None:
    st.subheader("➕ Create New Deck")

    existing = get_deck_names()

    with st.form("create_deck_form"):
        new_name = st.text_input("Deck name", placeholder="e.g. GeSci 205 — Chapter 7")
        submitted = st.form_submit_button("Create Deck", type="primary")

        if submitted:
            name = new_name.strip()
            if not name:
                st.error("Deck name cannot be empty.")
            elif name in existing:
                st.error(f"A deck named '{name}' already exists.")
            else:
                try:
                    create_deck(name)
                    st.success(f"✅ Created deck: '{name}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create deck: {e}")

    if existing:
        st.caption(f"**Existing decks ({len(existing)}):** " + ", ".join(existing))