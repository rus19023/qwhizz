# core/answer_checking.py

from difflib import SequenceMatcher


def normalize_answer(text):
    """Normalize answer for comparison"""
    return text.lower().strip().replace(".", "").replace(",", "")


def check_answer(user_answer, correct_answer, threshold=0.8):
    """
    Check if user answer is correct using fuzzy matching
    Returns: (is_correct, similarity_score)
    """
    user_norm = normalize_answer(user_answer)
    correct_norm = normalize_answer(correct_answer)
    
    # Exact match
    if user_norm == correct_norm:
        return True, 1.0
    
    # Fuzzy match using sequence matcher
    similarity = SequenceMatcher(None, user_norm, correct_norm).ratio()
    
    return similarity >= threshold, similarity