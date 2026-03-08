# data/ponder_store.py
"""
MongoDB operations for ponder responses.
Responses are stored in a separate 'ponder_responses' collection.
"""

from datetime import datetime
from data.db import get_database


def submit_ponder_response(deck_name, card_index, question, response_text, username, anonymous=False):
    """
    Save a ponder response to the database.

    Args:
        deck_name: The deck the card belongs to
        card_index: Index of the card in the deck
        question: The question text (stored for display convenience)
        response_text: The user's response
        username: The logged-in username
        anonymous: Whether to display anonymously
    """
    db = get_database()
    doc = {
        "deck_name": deck_name,
        "card_index": card_index,
        "question": question,
        "response_text": response_text.strip(),
        "username": username,
        "display_name": "Anonymous" if anonymous else username,
        "anonymous": anonymous,
        "timestamp": datetime.utcnow(),
    }
    db.ponder_responses.insert_one(doc)


def get_responses_for_card(deck_name, card_index, exclude_username=None):
    """
    Get all shared responses for a specific card, newest first.
    Optionally exclude a specific user's responses (e.g. to avoid showing own).
    """
    db = get_database()
    query = {"deck_name": deck_name, "card_index": card_index}
    if exclude_username:
        query["username"] = {"$ne": exclude_username}
    return list(
        db.ponder_responses.find(query, {"_id": 0})
        .sort("timestamp", -1)
    )


def get_all_responses_for_deck(deck_name):
    """
    Get all responses for a deck grouped by card_index, newest first.
    Returns a dict: {card_index: [responses]}
    """
    db = get_database()
    responses = list(
        db.ponder_responses.find({"deck_name": deck_name}, {"_id": 0})
        .sort("timestamp", -1)
    )
    grouped = {}
    for r in responses:
        idx = r["card_index"]
        grouped.setdefault(idx, []).append(r)
    return grouped


def get_user_response_for_card(deck_name, card_index, username):
    """Check if a user has already submitted a response for this card."""
    db = get_database()
    return db.ponder_responses.find_one(
        {"deck_name": deck_name, "card_index": card_index, "username": username},
        {"_id": 0}
    )


def delete_ponder_response(deck_name, card_index, username):
    """Allow a user to delete their own response."""
    db = get_database()
    db.ponder_responses.delete_one(
        {"deck_name": deck_name, "card_index": card_index, "username": username}
    )
