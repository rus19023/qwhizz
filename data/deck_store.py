# deck_store.py
from data.db import decks

# # run once to sync in-memory decks to database


# from data.decks import DECKS

# for name, cards in DECKS.items():
#     decks.update_one(
#         {"_id": name},
#         {"$set": {"cards": cards}},
#         upsert=True
#     )

# # end run once block


def get_deck_names():
    return sorted(decks.distinct("_id"))


def get_deck(deck_name):
    doc = decks.find_one({"_id": deck_name})
    return doc["cards"] if doc else []


def add_card(deck_name, question, answer):
    decks.update_one(
        {"_id": deck_name},
        {
            "$push": {
                "cards": {
                    "question": question,
                    "answer": answer
                }
            }
        },
        upsert=True
    )
    

def find_duplicate_cards(deck_name):
    """Find duplicate cards in a deck (same question)"""
    doc = decks.find_one({"_id": deck_name})
    if not doc or "cards" not in doc:
        return []
    
    cards = doc["cards"]
    seen = {}
    duplicates = []
    
    for idx, card in enumerate(cards):
        question = card["question"].strip().lower()
        if question in seen:
            duplicates.append({
                "index": idx,
                "question": card["question"],
                "answer": card["answer"],
                "original_index": seen[question]
            })
        else:
            seen[question] = idx
    
    return duplicates


def delete_card(deck_name, card_index):
    """Delete a card from a deck by index"""
    doc = decks.find_one({"_id": deck_name})
    if not doc or "cards" not in doc:
        return False
    
    cards = doc["cards"]
    if 0 <= card_index < len(cards):
        cards.pop(card_index)
        decks.update_one(
            {"_id": deck_name},
            {"$set": {"cards": cards}}
        )
        return True
    return False


def get_all_cards_with_indices(deck_name):
    """Get all cards with their indices for management"""
    doc = decks.find_one({"_id": deck_name})
    if not doc or "cards" not in doc:
        return []
    
    return [
        {
            "index": idx,
            "question": card["question"],
            "answer": card["answer"]
        }
        for idx, card in enumerate(doc["cards"])
    ]