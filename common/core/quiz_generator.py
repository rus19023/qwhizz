# core/quiz_generator.py

import random
import json
import streamlit as st

from core.ai_deck_generator import (
    _call_provider,
    _get_secret,
    PROVIDERS,
    DEFAULT_MODELS,
)


def _get_wrong_answers(card: dict) -> list[str]:
    """
    Extract stored wrong answers from a card, checking all possible field names.

    Args:
        card (dict): A card document from MongoDB.

    Returns:
        list[str]: List of stored wrong answers, or empty list if none found.
    """
    return (
        card.get("wrong_answers")
        or card.get("distractors")
        or card.get("incorrect_answers")
        or []
    )


def _generate_and_save_distractors(
    question: str,
    correct_answer: str,
    deck_name: str | None,
    card_index: int | None,
    count: int = 3,
    provider: str = "claude",
    model: str | None = None,
) -> list[str]:
    """
    Call the selected AI provider to generate plausible distractors, then save
    them back to MongoDB so the API is only called once per card.

    Args:
        question (str): The quiz question text.
        correct_answer (str): The correct answer text.
        deck_name (str | None): The deck's MongoDB _id — needed to save back.
        card_index (int | None): The card's index in the deck array — needed to save back.
        count (int): Number of distractors to generate.
        provider (str): Provider key — 'claude', 'openai', or 'ollama'.
        model (str | None): Model name override. Falls back to DEFAULT_MODELS[provider].

    Returns:
        list[str]: Generated distractor strings, or empty list on failure.
    """
    model = model or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["claude"])

    prompt = (
        f"You are helping create a multiple choice quiz.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {correct_answer}\n\n"
        f"Generate exactly {count} plausible but INCORRECT answer options. "
        f"They must be:\n"
        f"- Similar in style, length, and topic to the correct answer\n"
        f"- Believable enough to require thinking, but clearly wrong\n"
        f"- NOT variations like 'Not X' or 'Incorrect: X'\n\n"
        f"Respond with ONLY a JSON array of {count} strings, no explanation. "
        f'Example: ["wrong 1", "wrong 2", "wrong 3"]'
    )

    try:
        raw = _call_provider(prompt, provider, model)
        if not raw:
            return []

        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()

        distractors = json.loads(raw)
        if not isinstance(distractors, list):
            return []

        distractors = [str(d) for d in distractors[:count]]

        # Save back to MongoDB so this card never needs the API again
        if distractors and deck_name is not None and card_index is not None:
            try:
                from data.db import get_database
                db = get_database()
                db.decks.update_one(
                    {"_id": deck_name},
                    {"$set": {f"cards.{card_index}.wrong_answers": distractors}},
                )
            except Exception:
                pass  # Save failure should never break the quiz

        return distractors

    except Exception:
        return []


def _distractor_unavailable() -> str:
    """
    Absolute last resort placeholder — only appears if the AI call fails.
    If users see this in a quiz, check the provider API key / connection.

    Returns:
        str: A placeholder string signalling a configuration problem.
    """
    return "(distractor unavailable — check API key)"


def generate_fake_answers(
    correct_answer: str,
    card: dict,
    count: int = 3,
    deck_name: str | None = None,
    card_index: int | None = None,
    provider: str = "claude",
    model: str | None = None,
) -> list[str]:
    """
    Generate plausible fake answers for a multiple choice question.

    Priority:
      1. Stored wrong_answers/distractors on the card  → instant, no API call
      2. AI-generated distractors via selected provider → saved back to card
      3. Placeholder string                            → only if AI call fails

    Args:
        correct_answer (str): The correct answer text.
        card (dict): The full card document (used to read stored wrong answers and question).
        count (int): Number of fake answers to return.
        deck_name (str | None): Deck _id — needed to save AI results back to MongoDB.
        card_index (int | None): Card index in deck array — needed to save back.
        provider (str): AI provider key — 'claude', 'openai', or 'ollama'.
        model (str | None): Model name override. Falls back to DEFAULT_MODELS[provider].

    Returns:
        list[str]: List of fake answer strings.
    """
    fake_answers: list[str] = []

    # 1. Use stored wrong answers first (free, instant, no API call)
    stored_wrong = [
        w for w in _get_wrong_answers(card)
        if w and w.lower().strip() != correct_answer.lower().strip()
    ]
    if stored_wrong:
        fake_answers.extend(random.sample(stored_wrong, min(count, len(stored_wrong))))

    # 2. Fill remaining slots with AI-generated distractors
    if len(fake_answers) < count:
        still_needed = count - len(fake_answers)
        ai_distractors = _generate_and_save_distractors(
            question=card.get("question", ""),
            correct_answer=correct_answer,
            deck_name=deck_name,
            card_index=card_index,
            count=still_needed,
            provider=provider,
            model=model,
        )
        for d in ai_distractors:
            if d.lower().strip() != correct_answer.lower().strip() and d not in fake_answers:
                fake_answers.append(d)

    # 3. Absolute last resort — AI failed
    while len(fake_answers) < count:
        placeholder = _distractor_unavailable()
        if placeholder not in fake_answers:
            fake_answers.append(placeholder)

    return fake_answers[:count]


def create_multiple_choice_question(
    card: dict,
    deck_name: str | None = None,
    card_index: int | None = None,
    provider: str = "claude",
    model: str | None = None,
) -> dict:
    """
    Create a multiple choice question dict from a card.

    Pass deck_name and card_index so that AI-generated distractors are saved
    back to MongoDB — meaning the API is only called once per card.

    Args:
        card (dict): The card document from MongoDB.
        deck_name (str | None): The deck's _id — used to persist generated distractors.
        card_index (int | None): The card's index in the deck — used to persist distractors.
        provider (str): AI provider key — 'claude', 'openai', or 'ollama'.
        model (str | None): Model name override. Falls back to DEFAULT_MODELS[provider].

    Returns:
        dict: {question, options, correct_index, correct_answer}
    """
    correct_answer = card["answer"]

    fake_answers = generate_fake_answers(
        correct_answer=correct_answer,
        card=card,
        count=3,
        deck_name=deck_name,
        card_index=card_index,
        provider=provider,
        model=model,
    )

    all_options = fake_answers + [correct_answer]
    random.shuffle(all_options)

    return {
        "question":       card["question"],
        "options":        all_options,
        "correct_index":  all_options.index(correct_answer),
        "correct_answer": correct_answer,
    }


def generate_true_false_statement(question: str, answer: str, is_true: bool = True) -> str:
    """
    Generate a true/false statement from a card's question and answer.

    Args:
        question (str): The card question.
        answer (str): The card answer.
        is_true (bool): Whether to generate a true or false statement.

    Returns:
        str: A statement suitable for a true/false question.
    """
    if is_true:
        return f"{question.rstrip('?')} → {answer}"
    fake = f"Not {answer}" if random.random() > 0.5 else f"{answer} (incorrect version)"
    return f"{question.rstrip('?')} → {fake}"


def create_true_false_question(card: dict) -> dict:
    """
    Create a true/false question dict from a card.

    Args:
        card (dict): The card document from MongoDB.

    Returns:
        dict: {statement, is_true, correct_answer}
    """
    is_true = random.random() > 0.5
    return {
        "statement":      generate_true_false_statement(card["question"], card["answer"], is_true),
        "is_true":        is_true,
        "correct_answer": card["answer"],
    }