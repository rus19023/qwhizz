# core/game_mode_logic.py
"""
Logic for game modes: multiple choice, multi-select, true/false
"""

import random
from difflib import SequenceMatcher


def generate_multiple_choice_options(card, all_cards, num_options=4):
    """
    Generate multiple choice options for a card

    Args:
        card: The current card dict
        all_cards: List of all cards (to generate distractors)
        num_options: Number of options to generate (2-10, default 4)

    Returns:
        (options_list, correct_index)
    """
    # If card already has options, use those
    if "options" in card and "correct_index" in card:
        return card["options"][:num_options], card["correct_index"]

    correct_answer = card["answer"]

    # Get other answers as distractors — only from same card type,
    # excluding true/false and essay cards which make poor distractors.
    # Guards: skip cards missing "answer", skip cards whose answer is
    # falsy or non-string (e.g. boolean True stored from old T/F cards).
    from data.card_format import get_card_type
    current_type = get_card_type(card)
    excluded_types = {"true_false", "essay"}

    other_answers = [
        str(c["answer"]) for c in all_cards
        if c.get("answer") is not None          # must have an answer key
        and str(c["answer"]).strip()            # must not be blank
        and str(c["answer"]) != str(correct_answer)   # must differ from correct
        and get_card_type(c) not in excluded_types
        and get_card_type(c) == current_type
    ]

    options = [str(correct_answer)]

    # Randomly select distractors
    num_distractors = min(num_options - 1, len(other_answers))
    if num_distractors > 0:
        distractors = random.sample(other_answers, num_distractors)
        options.extend(distractors)

    # Fill remaining slots with placeholder distractors if needed
    while len(options) < num_options:
        options.append(f"[Option {len(options) + 1}]")

    # Shuffle and find where the correct answer landed
    random.shuffle(options)
    correct_index = options.index(str(correct_answer))

    return options[:num_options], correct_index


def generate_multi_select_options(card, all_cards, num_options=6):
    """
    Generate multi-select options for a card

    Args:
        card: The current card dict with correct_indices
        all_cards: List of all cards
        num_options: Total number of options (default 6)

    Returns:
        (options_list, correct_indices_list)
    """
    # If card already has options, use those
    if "options" in card and "correct_indices" in card:
        return card["options"][:num_options], card["correct_indices"]

    # Requires pre-configured cards
    return [], []


def check_true_false_answer(card, user_answer):
    """
    Check if true/false answer is correct

    Args:
        card: The card dict with correct_answer field
        user_answer: User's boolean answer

    Returns:
        bool: True if correct
    """
    if "correct_answer" in card:
        return card["correct_answer"] == user_answer

    # Fallback: check if "true" is in the answer text
    answer_lower = str(card.get("answer", "")).lower()
    return ("true" in answer_lower) == user_answer


def check_multiple_choice_answer(correct_index, selected_index):
    """Check if multiple choice answer is correct"""
    return correct_index == selected_index


def check_multi_select_answer(correct_indices, selected_indices):
    """
    Check if multi-select answer is correct

    Args:
        correct_indices: List of correct indices
        selected_indices: List of user-selected indices

    Returns:
        bool: True if exactly matches (all correct, no extras)
    """
    return set(correct_indices) == set(selected_indices)


def calculate_similarity(text1, text2):
    """Calculate similarity between two strings (0-1)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def check_typed_answer(card_answer, user_answer, threshold=0.8):
    """
    Check typed answer with fuzzy matching

    Args:
        card_answer: The correct answer
        user_answer: User's typed answer
        threshold: Similarity threshold (0-1)

    Returns:
        (is_correct, similarity_score)
    """
    similarity = calculate_similarity(str(card_answer), user_answer)
    is_correct = similarity >= threshold
    return is_correct, similarity