# data/deck_store.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from data.db import get_database


def _decks():
    """Return the Mongo collection for decks."""
    db = get_database()
    return db.decks


def create_deck(deck_name: str) -> str:
    """Create a deck if it doesn't exist. Returns normalized deck name."""
    name = (deck_name or "").strip()
    if not name:
        raise ValueError("Deck name cannot be empty.")
    _decks().update_one({"_id": name}, {"$setOnInsert": {"cards": []}}, upsert=True)
    return name


def get_deck_names() -> List[str]:
    return sorted(_decks().distinct("_id"))


def get_deck(deck_name: str) -> List[Dict[str, Any]]:
    doc = _decks().find_one({"_id": deck_name}, {"cards": 1})
    return list(doc.get("cards", [])) if doc else []


def add_card(deck_name: str, question: str, answer: str, feedback: Optional[dict] = None) -> None:
    card = {"question": question, "answer": answer}
    if feedback:
        card["feedback"] = feedback

    _decks().update_one(
        {"_id": deck_name},
        {"$push": {"cards": card}},
        upsert=True
    )


def find_duplicate_cards(deck_name: str) -> List[Dict[str, Any]]:
    """Find duplicate cards in a deck (same question)."""
    cards = get_deck(deck_name)
    seen: Dict[str, int] = {}
    duplicates: List[Dict[str, Any]] = []

    for idx, card in enumerate(cards):
        q = (card.get("question") or "").strip().lower()
        if not q:
            continue
        if q in seen:
            duplicates.append({
                "index": idx,
                "question": card.get("question", ""),
                "answer": card.get("answer", ""),
                "original_index": seen[q]
            })
        else:
            seen[q] = idx

    return duplicates


def delete_card(deck_name: str, card_index: int) -> bool:
    """Delete a card from a deck by index."""
    cards = get_deck(deck_name)
    if 0 <= card_index < len(cards):
        cards.pop(card_index)
        _decks().update_one({"_id": deck_name}, {"$set": {"cards": cards}})
        return True
    return False


def get_all_cards_with_indices(deck_name: str) -> List[Dict[str, Any]]:
    cards = get_deck(deck_name)
    return [
        {
            "index": idx,
            "question": (card.get("question") or ""),
            "answer": (card.get("answer") or ""),
            "feedback": card.get("feedback", {}) or {},
        }
        for idx, card in enumerate(cards)
    ]