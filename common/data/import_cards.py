"""
data/import_cards.py

Module for importing flashcards from CSV and JSON files
"""

import csv
import json
import streamlit as st
from data.deck_store import add_card
from data.card_format import validate_card, sanitize_card


def import_from_csv(csv_file, deck_name):
    """
    Import flashcards from CSV file
    
    Args:
        csv_file: Uploaded file object from st.file_uploader
        deck_name: Name of deck to import into
        
    Returns:
        dict with success status and message
    """
    imported_count = 0
    skipped_count = 0
    errors = []
    
    try:
        # Read CSV file
        content = csv_file.read().decode('utf-8')
        lines = content.splitlines()
        reader = csv.DictReader(lines)
        
        for i, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
            question = row.get('question', '').strip()
            answer = row.get('answer', '').strip()
            
            if question and answer:
                # Validate the card
                is_valid, error_msg = validate_card(question, answer, deck_name)
                
                if is_valid:
                    try:
                        # Sanitize before adding
                        clean_q, clean_a = sanitize_card(question, answer)
                        add_card(
                            deck_name=deck_name,
                            question=clean_q,
                            answer=clean_a
                        )
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Line {i}: Database error - {str(e)}")
                        skipped_count += 1
                else:
                    errors.append(f"Line {i}: {error_msg}")
                    skipped_count += 1
            else:
                skipped_count += 1
                errors.append(f"Line {i}: Missing question or answer")
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'message': f"✅ Successfully imported {imported_count} cards. Skipped {skipped_count}."
        }
    
    except Exception as e:
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [str(e)],
            'message': f"❌ Error: {str(e)}"
        }


def import_from_json(json_file, deck_name):
    """
    Import flashcards from JSON file
    
    Args:
        json_file: Uploaded file object from st.file_uploader
        deck_name: Name of deck to import into
        
    Returns:
        dict with success status and message
    """
    imported_count = 0
    skipped_count = 0
    errors = []
    
    try:
        # Read JSON file
        content = json_file.read().decode('utf-8')
        data = json.loads(content)
        
        # Handle both array of cards and single card object
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return {
                'success': False,
                'imported': 0,
                'skipped': 0,
                'errors': ['JSON must be an array of card objects or a single card object'],
                'message': "❌ Invalid JSON format"
            }
        
        for i, card in enumerate(data, start=1):
            question = card.get('question', '').strip()
            card_type = card.get('type', 'flashcard')
            # ponder cards don't need an answer
            answer = card.get('answer', '').strip()
            
            has_required_fields = bool(question) and (bool(answer) or card_type == 'ponder')

            if has_required_fields:
                try:
                    from data.db import get_database
                    db = get_database()
                    deck_doc = db.decks.find_one({"_id": deck_name})
                    if not deck_doc:
                        db.decks.insert_one({"_id": deck_name, "cards": []})

                    # Build full card preserving all fields
                    full_card = {k: v for k, v in card.items()}
                    full_card['question'] = question
                    if answer:
                        full_card['answer'] = answer

                    db.decks.update_one(
                        {"_id": deck_name},
                        {"$push": {"cards": full_card}}
                    )
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Card {i}: Database error - {str(e)}")
                    skipped_count += 1
            else:
                skipped_count += 1
                errors.append(f"Card {i}: Missing question or answer")
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'message': f"✅ Successfully imported {imported_count} cards. Skipped {skipped_count}."
        }
    
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [f"Invalid JSON: {str(e)}"],
            'message': f"❌ Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [str(e)],
            'message': f"❌ Error: {str(e)}"
        }


def render_import_ui(deck_name):
    """
    Render the file upload UI for importing cards
    
    Args:
        deck_name: Name of deck to import into
    """
    st.subheader("📥 Import Cards from File")
    
    # File format selection
    file_format = st.radio(
        "Select file format:",
        ["CSV", "JSON"],
        horizontal=True,
        key="import_format"
    )
    
    # File uploader
    if file_format == "CSV":
        st.info("📋 CSV format: Must have 'question' and 'answer' columns")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            key="csv_uploader"
        )
    else:
        st.info("📋 JSON format: Array of objects with 'question' and 'answer' fields")
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type=['json'],
            key="json_uploader"
        )
    
    # Process upload
    if uploaded_file is not None:
        if st.button("Import Cards", type="primary"):
            with st.spinner(f"Importing cards from {uploaded_file.name}..."):
                # Import based on format
                if file_format == "CSV":
                    result = import_from_csv(uploaded_file, deck_name)
                else:
                    result = import_from_json(uploaded_file, deck_name)
                
                # Display results
                if result['success']:
                    st.success(result['message'])
                    
                    # Show details in expander
                    with st.expander("📊 Import Details"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Imported", result['imported'])
                        with col2:
                            st.metric("Skipped", result['skipped'])
                        
                        if result['errors']:
                            st.warning("⚠️ Errors/Warnings:")
                            for error in result['errors']:
                                st.text(f"• {error}")
                    
                    # Rerun to refresh the card list
                    if result['imported'] > 0:
                        st.balloons()
                       #st.rerun()
                else:
                    st.error(result['message'])
                    if result['errors']:
                        with st.expander("🔍 Error Details"):
                            for error in result['errors']:
                                st.text(f"• {error}")