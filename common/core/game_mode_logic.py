# core/game_mode_logic.py
"""
Logic for game modes: multiple choice, multi-select, true/false
"""

import random
from difflib import SequenceMatcher
from core.quiz_generator import generate_fake_answers


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
    num_distractors = num_options - 1

    # Use generate_fake_answers which handles: stored → AI → other cards
    distractors = generate_fake_answers(correct_answer, card, all_cards, count=num_distractors)

    options = distractors + [correct_answer]
    random.shuffle(options)
    correct_index = options.index(correct_answer)

    return options, correct_index


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

    # This requires pre-configured cards
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
    answer_lower = card["answer"].lower()
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
    similarity = calculate_similarity(card_answer, user_answer)
    is_correct = similarity >= threshold
    return is_correct, similarity