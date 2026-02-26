# ui/add_card_tab.py

import streamlit as st
from data.deck_store import add_card, add_card_full, get_deck_names
from data.card_format import validate_card
from data.import_cards import render_import_ui
from data.db import get_database


# Map display names to internal keys
CARD_TYPE_DISPLAY = {
    "📇 Standard Flashcard": "flashcard",
    "🎯 Multiple Choice (single answer)": "multiple_choice",
    "☑️ Multi-Select (multiple answers)": "multi_select",
    "✓✗ True/False": "true_false"
}


def render_add_card_tab():
    """Enhanced add card interface with support for all card types"""
    tab1, tab2 = st.tabs(["✍️ Manual Entry", "📥 Import File"])
    with tab1:
    
        st.subheader("➕ Add New Flashcard")
        
        # Deck selector
        deck_names = get_deck_names()
        if not deck_names:
            st.error("No decks found. Create a deck first in the Manage tab.")
            return
        
        selected_deck = st.selectbox("Select deck", deck_names, index=int(len(deck_names) -1), key="add_card_deck")
        
        # Card type selector - store display name as string to match browser cache
        selected_display = st.selectbox(
            "Card Type",
            options=list(CARD_TYPE_DISPLAY.keys()),
            key="card_type_selector"
        )
        card_type = CARD_TYPE_DISPLAY.get(selected_display, "flashcard")
        
        # Create form based on card type
        with st.form("add_card_form", clear_on_submit=False):
            
            # Common fields
            question = st.text_area("Question", height=100, key="new_question")
            
            # Optional image
            "🖼️ Add Image (Optional)"
            image_url = st.text_input(
                "Image URL",
                help="URL to an image (diagram, chart, table, etc.)",
                key="new_image_url"
            )
            if image_url:
                try:
                    st.image(image_url, caption="Preview")
                except:
                    st.warning("Could not load image preview")
            
            # Card type specific fields
            card_data = {"type": card_type}
            
            if card_type == "flashcard":
                answer = st.text_area("Answer", height=150, key="new_answer")
                card_data["answer"] = answer
            
            elif card_type == "multiple_choice":
                st.subheader("Multiple Choice Options")
                
                num_options = st.slider(
                    "Number of options",
                    min_value=2,
                    max_value=10,
                    value=4,
                    key="mc_num_options"
                )
                
                options = []
                for i in range(num_options):
                    opt = st.text_input(
                        f"Option {chr(65+i)}",
                        key=f"mc_opt_{i}"
                    )
                    options.append(opt)
                
                # Index-based to avoid format_func state bug
                correct_index = st.selectbox(
                    "Correct answer",
                    options=range(num_options),
                    format_func=lambda i: f"{chr(65+i)}. {options[i]}" if options[i] else f"Option {chr(65+i)}",
                    key="mc_correct"
                )
                
                answer = st.text_area(
                    "Full explanation/answer",
                    height=100,
                    help="Detailed explanation shown after answering",
                    key="mc_answer"
                )
                
                card_data["options"] = options
                card_data["correct_index"] = correct_index
                card_data["answer"] = answer
            
            elif card_type == "multi_select":
                st.subheader("Multi-Select Options")
                st.info("Users must select ALL correct answers")
                
                num_options = st.slider(
                    "Number of options",
                    min_value=3,
                    max_value=10,
                    value=6,
                    key="ms_num_options"
                )
                
                options = []
                for i in range(num_options):
                    opt = st.text_input(
                        f"Option {chr(65+i)}",
                        key=f"ms_opt_{i}"
                    )
                    options.append(opt)
                
                st.write("**Select ALL correct answers:**")
                correct_indices = []
                cols = st.columns(2)
                for i in range(num_options):
                    with cols[i % 2]:
                        if st.checkbox(
                            f"{chr(65+i)}. {options[i]}" if options[i] else f"Option {chr(65+i)}",
                            key=f"ms_correct_{i}"
                        ):
                            correct_indices.append(i)
                
                num_correct = len(correct_indices)
                st.caption(f"Selected {num_correct} correct answer(s)")
                
                answer = st.text_area(
                    "Full explanation",
                    height=100,
                    help="Explain why the selected answers are correct",
                    key="ms_answer"
                )
                
                card_data["options"] = options
                card_data["correct_indices"] = correct_indices
                card_data["num_correct"] = num_correct
                card_data["answer"] = answer
            
            elif card_type == "true_false":
                st.subheader("True/False")
                
                # Index-based to avoid format_func state bug
                tf_index = st.selectbox(
                    "Correct answer",
                    options=[0, 1],
                    format_func=lambda i: "✓ TRUE" if i == 0 else "✗ FALSE",
                    key="tf_correct"
                )
                correct_answer = (tf_index == 0)
                
                answer = st.text_area(
                    "Explanation",
                    height=150,
                    help="Explain why the statement is true or false",
                    key="tf_answer"
                )
                
                card_data["correct_answer"] = correct_answer
                card_data["answer"] = answer
            
            # Add image if provided
            if image_url and image_url.strip():
                card_data["image_url"] = image_url.strip()

            # Feedback section
                        # Feedback section
            with st.expander("💬 Add Feedback (Optional — shown after answering)"):
                feedback_text = st.text_area(
                    "Explanation / Feedback",
                    height=100,
                    help="Shown after the student answers. Supports markdown.",
                    key="feedback_text"
                )

                st.write("**Images** (one URL per line):")
                feedback_images_raw = st.text_area(
                    "Image URLs",
                    height=70,
                    help="One image URL per line",
                    key="feedback_images"
                )

                st.write("**Reference Links** (comma-separated URLs):")
                feedback_links_raw = st.text_area(
                    "Links",
                    height=80,
                    placeholder="https://a.com, https://b.com",
                    key="feedback_links_raw"
                )

            submitted = st.form_submit_button("➕ Add Card", type="primary")

            if submitted:
                card_data["question"] = question

                result = validate_card(card_data, card_data.get("answer", ""))

                if isinstance(result, tuple) and len(result) == 2:
                    is_valid, error_msg = result
                else:
                    # backwards compatibility if validate_card returns only bool
                    is_valid = bool(result)
                    error_msg = "" if is_valid else "Invalid card"

                if not is_valid:
                    st.error(f"❌ Invalid card: {error_msg}")
                elif not question.strip():
                    st.error("❌ Question cannot be empty")
                elif not card_data.get("answer", "").strip():
                    st.error("❌ Answer/explanation cannot be empty")
                else:
                    feedback = {}

                    if feedback_text.strip():
                        feedback["text"] = feedback_text.strip()

                    imgs = [u.strip() for u in feedback_images_raw.splitlines() if u.strip()]
                    if imgs:
                        feedback["images"] = imgs

                    # Parse comma-separated links
                    links = []
                    for item in feedback_links_raw.replace("\n", ",").split(","):
                        url = item.strip()
                        if url:
                            links.append({"label": url, "url": url})

                    if links:
                        feedback["links"] = links

                    if feedback:
                        card_data["feedback"] = feedback

                    # Add to deck
                    try:
                        add_card(selected_deck, card_data["question"], card_data["answer"])
                        
                        # If it's a game mode card, update with extra fields
                        if card_type != "flashcard":
                            db = get_database()
                            deck = db.decks.find_one({"_id": selected_deck})
                            
                            if deck:
                                cards = deck["cards"]
                                cards[-1].update(card_data)
                                db.decks.update_one(
                                    {"_id": selected_deck},
                                    {"$set": {"cards": cards}}
                                )
                        
                        st.success(f"✅ Card added to '{selected_deck}'!")
                        
                        with st.expander("Preview added card"):
                            st.json(card_data)
                    
                    except Exception as e:
                        st.error(f"❌ Error adding card: {e}")
                        
    with tab2:
        st.subheader("Import Cards from File")
        
        deck_option_import = st.radio(
            "Choose deck:",
            options=["Add to existing deck", "Create new deck"],
            key="import_deck_option"
        )
        
        if deck_option_import == "Add to existing deck":
            existing_decks = get_deck_names()
            if existing_decks:
                import_deck = st.selectbox(
                    "Select deck:",
                    options=existing_decks,
                    key="import_deck_select"
                )
            else:
                st.warning("No decks exist yet. Please create a new deck below.")
                deck_option_import = "Create new deck"
        
        if deck_option_import == "Create new deck":
            import_deck = st.text_input("New deck name:", key="import_new_deck_name")
        
        if (deck_option_import == "Add to existing deck" and existing_decks) or \
           (deck_option_import == "Create new deck" and import_deck.strip()):
            deck_name = import_deck.strip() if deck_option_import == "Create new deck" else import_deck
            render_import_ui(deck_name)
        elif deck_option_import == "Create new deck":
            st.info("Enter a deck name above to continue")