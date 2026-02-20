# ui/add_card_tab.py

import streamlit as st
from data.deck_store import add_card, get_deck_names
#from data.card_format import validate_card
from data.import_cards import render_import_ui
from data.db import get_database


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
        
        selected_deck = st.selectbox("Select deck", deck_names, key="add_card_deck")
        
        # Card type selector
        card_type = st.selectbox(
            "Card Type",
            options=["flashcard", "multiple_choice", "multi_select", "true_false"],
            format_func=lambda x: {
                "flashcard": "📇 Standard Flashcard",
                "multiple_choice": "🎯 Multiple Choice (single answer)",
                "multi_select": "☑️ Multi-Select (multiple answers)",
                "true_false": "✓✗ True/False"
            }[x],
            key="card_type_selector"
        )
        
        # Create form based on card type
        with st.form("add_card_form", clear_on_submit=True):
            
            # Common fields
            question = st.text_area("Question", height=100, key="new_question")
            
            # Optional image
            with st.expander("🖼️ Add Image (Optional)"):
                image_url = st.text_input(
                    "Image URL",
                    help="URL to an image (diagram, chart, table, etc.)",
                    key="new_image_url"
                )
                if image_url:
                    try:
                        st.image(image_url, caption="Preview", width='stretch')
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
                
                correct_index = st.selectbox(
                    "Correct answer",
                    options=list(range(num_options)),
                    format_func=lambda x: f"{chr(65+x)}. {options[x]}" if options[x] else f"Option {chr(65+x)}",
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
                
                correct_answer = st.radio(
                    "Correct answer",
                    options=[True, False],
                    format_func=lambda x: "✓ TRUE" if x else "✗ FALSE",
                    key="tf_correct"
                )
                
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
                
                st.write("**Reference Links:**")
                num_links = st.number_input("Number of links", min_value=0, max_value=5, value=0, key="feedback_num_links")
                feedback_links = []
                for li in range(int(num_links)):
                    lc1, lc2 = st.columns([2, 3])
                    with lc1:
                        link_label = st.text_input(f"Label {li+1}", key=f"feedback_link_label_{li}")
                    with lc2:
                        link_url = st.text_input(f"URL {li+1}", key=f"feedback_link_url_{li}")
                    if link_url.strip():
                        feedback_links.append({"label": link_label.strip(), "url": link_url.strip()})

            # Submit button
            submitted = st.form_submit_button("➕ Add Card", type="primary", width='stretch')
            
            if submitted:
                # Build complete card
                card_data["question"] = question
                
                # Validate card
                is_valid, error_msg = validate_card(card_data)
                
                if not is_valid:
                    st.error(f"❌ Invalid card: {error_msg}")
                elif not question.strip():
                    st.error("❌ Question cannot be empty")
                elif not card_data.get("answer", "").strip():
                    st.error("❌ Answer/explanation cannot be empty")
                else:
                    # Add feedback if present
                    if feedback:
                        card_data["feedback"] = feedback

                    # Add to deck
                    try:
                        add_card(selected_deck, card_data["question"], card_data["answer"])
                        
                        # If it's a game mode card, update with extra fields
                        if card_type != "flashcard":
                            from data.deck_store import get_deck
                            
                            db = get_database()
                            deck = db.decks.find_one({"_id": selected_deck})
                            
                            if deck:
                                # Find the card we just added (last one)
                                cards = deck["cards"]
                                cards[-1].update(card_data)
                                
                                # Update in database
                                db.decks.update_one(
                                    {"_id": selected_deck},
                                    {"$set": {"cards": cards}}
                                )
                        
                        st.success(f"✅ Card added to '{selected_deck}'!")
                        
                        # Show preview
                        with st.expander("Preview added card"):
                            st.json(card_data)
                    
                    except Exception as e:
                        st.error(f"❌ Error adding card: {e}")
                        
    with tab2:
        # Deck selection for import
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
        
        # Only show import UI if deck is selected/named
        if (deck_option_import == "Add to existing deck" and existing_decks) or \
           (deck_option_import == "Create new deck" and import_deck.strip()):
            deck_name = import_deck.strip() if deck_option_import == "Create new deck" else import_deck
            render_import_ui(deck_name)
        elif deck_option_import == "Create new deck":
            st.info("👆 Enter a deck name above to continue")                   

    
# Quick tips
# with st.expander("💡 Tips for Creating Good Questions"):
#         st.markdown("""
#         **Multiple Choice:**
#         - Make distractors plausible but clearly wrong
#         - Keep options similar in length
#         - Use 4-6 options for best results
        
#         **Multi-Select:**
#         - Clearly indicate that multiple answers are needed
#         - Use 4-8 total options with 2-4 correct
#         - Make incorrect options clearly distinguishable
        
#         **True/False:**
#         - Avoid absolute words like "always" and "never"
#         - Make statements clear and unambiguous
#         - Provide detailed explanations
        
#         **Images:**
#         - Use clear, high-quality diagrams
#         - Ensure images are publicly accessible URLs
#         - Test image URLs before adding
#         """)