# core/ai_deck_enricher.py
"""
AI-powered enrichment of existing flashcard decks.

For each card, detects missing fields and uses the selected AI provider
to fill them in — without touching anything already populated.

Supported enrichment targets:
  - wrong_answers   : plausible distractors for MC mode
  - explanation     : rich explanation shown after answering
  - feedback.text   : shorter hint/feedback shown after answering
"""

from __future__ import annotations
import json
import streamlit as st

from core.ai_deck_generator import (
    _call_provider,
    PROVIDERS,
    DEFAULT_MODELS,
)


# ── Gap detection ─────────────────────────────────────────────────────────────

def card_missing_fields(card: dict) -> list[str]:
    """
    Return a list of field names that are empty / missing on this card.

    Args:
        card (dict): A card document from MongoDB.

    Returns:
        list[str]: Zero or more of: 'wrong_answers', 'explanation', 'feedback'
    """
    missing = []

    wrong = (
        card.get("wrong_answers")
        or card.get("distractors")
        or card.get("incorrect_answers")
        or []
    )
    if not wrong:
        missing.append("wrong_answers")

    if not (card.get("explanation") or "").strip():
        missing.append("explanation")

    feedback = card.get("feedback") or {}
    if not (feedback.get("text") or "").strip():
        missing.append("feedback")

    return missing


# ── Per-field prompts ─────────────────────────────────────────────────────────

def _prompt_wrong_answers(question: str, answer: str, count: int = 3) -> str:
    return (
        f"You are helping create a multiple choice quiz.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {answer}\n\n"
        f"Generate exactly {count} plausible but INCORRECT answer options. "
        f"They must be:\n"
        f"- Similar in style, length, and topic to the correct answer\n"
        f"- Believable enough to require thinking, but clearly wrong\n"
        f"- NOT variations like 'Not X' or 'Incorrect: X'\n\n"
        f"Respond with ONLY a JSON array of {count} strings, no explanation.\n"
        f'Example: ["wrong 1", "wrong 2", "wrong 3"]'
    )


def _prompt_explanation(question: str, answer: str) -> str:
    return (
        f"You are an expert educator.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {answer}\n\n"
        f"Write a clear, educational explanation (2-4 sentences) of WHY this is the correct answer. "
        f"Help a student understand the concept deeply, not just memorize the answer.\n\n"
        f"Respond with ONLY the explanation text, no preamble."
    )


def _prompt_feedback(question: str, answer: str) -> str:
    return (
        f"You are an expert educator.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {answer}\n\n"
        f"Write a short, encouraging feedback message (1-2 sentences) that a student "
        f"would see after answering this question. It should reinforce the key idea.\n\n"
        f"Respond with ONLY the feedback text, no preamble."
    )


# ── AI calls ──────────────────────────────────────────────────────────────────

def _call_for_field(
    field: str,
    question: str,
    answer: str,
    provider: str,
    model: str,
) -> str | list[str] | None:
    """
    Call the AI provider to fill in a single missing field.

    Args:
        field (str): One of 'wrong_answers', 'explanation', 'feedback'.
        question (str): The card's question text.
        answer (str): The card's correct answer text.
        provider (str): Provider key.
        model (str): Model name.

    Returns:
        str | list[str] | None: The generated value, or None on failure.
    """
    try:
        if field == "wrong_answers":
            prompt = _prompt_wrong_answers(question, answer)
            raw = _call_provider(prompt, provider, model)
            if not raw:
                return None
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            result = json.loads(raw)
            return [str(d) for d in result] if isinstance(result, list) else None

        elif field == "explanation":
            prompt = _prompt_explanation(question, answer)
            raw = _call_provider(prompt, provider, model)
            return raw.strip() if raw else None

        elif field == "feedback":
            prompt = _prompt_feedback(question, answer)
            raw = _call_provider(prompt, provider, model)
            return raw.strip() if raw else None

    except Exception:
        return None

    return None


# ── Main enrichment function ──────────────────────────────────────────────────

def enrich_deck(
    deck_name: str,
    cards: list[dict],
    fields_to_fill: list[str],
    provider: str = "claude",
    model: str | None = None,
    progress_callback=None,
) -> list[dict]:
    """
    Iterate over all cards, detect gaps, call AI to fill them, and return
    a list of proposed changes — WITHOUT writing to MongoDB yet.

    Args:
        deck_name (str): The deck's _id (used for context only here).
        cards (list[dict]): Raw card dicts from MongoDB including their index.
        fields_to_fill (list[str]): Which fields to enrich, e.g. ['wrong_answers', 'feedback'].
        provider (str): AI provider key.
        model (str | None): Model override. Falls back to DEFAULT_MODELS[provider].
        progress_callback (callable | None): Called with (current, total, card_question)
            for progress display.

    Returns:
        list[dict]: Proposed changes, each dict has:
            {index, question, answer, changes: {field: new_value}}
    """
    model = model or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["claude"])
    proposals = []
    total = len(cards)

    for i, card in enumerate(cards):
        question = (card.get("question") or "").strip()
        answer   = (card.get("answer") or "").strip()

        if not question or not answer:
            continue

        missing = [f for f in card_missing_fields(card) if f in fields_to_fill]
        if not missing:
            if progress_callback:
                progress_callback(i + 1, total, question)
            continue

        changes = {}
        for field in missing:
            value = _call_for_field(field, question, answer, provider, model)
            if value:
                changes[field] = value

        if changes:
            proposals.append({
                "index":    card.get("index", i),
                "question": question,
                "answer":   answer,
                "changes":  changes,
            })

        if progress_callback:
            progress_callback(i + 1, total, question)

    return proposals


def apply_proposals(deck_name: str, proposals: list[dict]) -> int:
    """
    Write approved proposals back to MongoDB.

    Args:
        deck_name (str): The deck's _id.
        proposals (list[dict]): Proposals as returned by enrich_deck(),
            optionally filtered to only approved ones.

    Returns:
        int: Number of cards updated.
    """
    from data.db import get_database
    db = get_database()

    deck_doc = db.decks.find_one({"_id": deck_name})
    if not deck_doc:
        return 0

    cards_list = deck_doc["cards"]
    updated = 0

    for proposal in proposals:
        idx     = proposal["index"]
        changes = proposal["changes"]

        if idx >= len(cards_list):
            continue

        card = cards_list[idx]

        if "wrong_answers" in changes:
            card["wrong_answers"] = changes["wrong_answers"]

        if "explanation" in changes:
            card["explanation"] = changes["explanation"]

        if "feedback" in changes:
            feedback = card.get("feedback") or {}
            feedback["text"] = changes["feedback"]
            card["feedback"] = feedback

        cards_list[idx] = card
        updated += 1

    db.decks.update_one({"_id": deck_name}, {"$set": {"cards": cards_list}})
    return updated
