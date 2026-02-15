"""
data/card_format.py

Card validation and formatting utilities
"""

import re
from data.deck_store import get_deck


# Configuration constants
MAX_QUESTION_LENGTH = 5000
MAX_ANSWER_LENGTH = 10000
MIN_ANSWER_LENGTH = 2
WARN_SHORT_ANSWER_LENGTH = 10


def validate_card(question, answer, deck_name=None):
    """
    Validate a flashcard before adding it to the database
    
    Args:
        question (str): The question text
        answer (str): The answer text
        deck_name (str, optional): Deck name to check for duplicates
        
    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): True if card is valid
            - error_message (str): Empty if valid, error description if invalid
    """
    
    # Strip whitespace for checking
    q = question.strip()
    a = answer.strip()
    
    # 1. Check if empty
    if not q:
        return False, "Question cannot be empty"
    
    if not a:
        return False, "Answer cannot be empty"
    
    # 2. Check length limits
    if len(q) > MAX_QUESTION_LENGTH:
        return False, f"Question too long ({len(q)} chars, max {MAX_QUESTION_LENGTH})"
    
    if len(a) > MAX_ANSWER_LENGTH:
        return False, f"Answer too long ({len(a)} chars, max {MAX_ANSWER_LENGTH})"
    
    if len(a) < MIN_ANSWER_LENGTH:
        return False, f"Answer too short ({len(a)} chars, min {MIN_ANSWER_LENGTH})"
    
    # 3. Check for suspicious patterns
    # Check if answer is just "yes", "no", "true", "false" (might be too simple)
    simple_answers = {'yes', 'no', 'true', 'false', 'y', 'n', 't', 'f'}
    if a.lower() in simple_answers:
        return False, f"Answer too simple: '{a}'. Please provide a more detailed answer."
    
    # 4. Check for duplicate questions in the same deck
    if deck_name:
        try:
            existing_cards = get_deck(deck_name)
            # Check if question already exists (case-insensitive)
            for card in existing_cards:
                if card.get('question', '').strip().lower() == q.lower():
                    return False, f"Duplicate question found in deck '{deck_name}'"
        except:
            # If deck doesn't exist yet, that's okay
            pass
    
    # 5. Warn about potentially problematic content (these are warnings, not errors)
    # We'll return True but could add warnings in the future
    
    # All checks passed
    return True, ""


def sanitize_card(question, answer):
    """
    Sanitize card content to prevent display issues
    
    Args:
        question (str): The question text
        answer (str): The answer text
        
    Returns:
        tuple: (sanitized_question, sanitized_answer)
    """
    
    # Remove excessive whitespace
    q = re.sub(r'\s+', ' ', question.strip())
    a = re.sub(r'\s+', ' ', answer.strip())
    
    # Remove potential HTML tags (basic sanitization)
    q = re.sub(r'<script.*?</script>', '', q, flags=re.DOTALL | re.IGNORECASE)
    a = re.sub(r'<script.*?</script>', '', a, flags=re.DOTALL | re.IGNORECASE)
    
    # Normalize line breaks
    q = q.replace('\r\n', '\n').replace('\r', '\n')
    a = a.replace('\r\n', '\n').replace('\r', '\n')
    
    return q, a


def get_card_warnings(question, answer):
    """
    Get non-critical warnings about a card
    
    Args:
        question (str): The question text
        answer (str): The answer text
        
    Returns:
        list: List of warning messages (empty if no warnings)
    """
    warnings = []
    
    q = question.strip()
    a = answer.strip()
    
    # Check if question doesn't end with punctuation
    if q and q[-1] not in '.?!':
        warnings.append("Question doesn't end with punctuation")
    
    # Check if answer is very short
    if len(a) < WARN_SHORT_ANSWER_LENGTH:
        warnings.append(f"Answer is short ({len(a)} chars). Consider adding more detail.")
    
    # Check if question is very long
    if len(q) > 500:
        warnings.append(f"Question is long ({len(q)} chars). Consider breaking into multiple cards.")
    
    # Check for all caps (might be shouting)
    if q.isupper() and len(q) > 10:
        warnings.append("Question is in ALL CAPS")
    
    if a.isupper() and len(a) > 10:
        warnings.append("Answer is in ALL CAPS")
    
    return warnings


def format_card_stats(question, answer):
    """
    Get statistics about a card
    
    Args:
        question (str): The question text
        answer (str): The answer text
        
    Returns:
        dict: Statistics about the card
    """
    q = question.strip()
    a = answer.strip()
    
    return {
        'question_length': len(q),
        'answer_length': len(a),
        'question_words': len(q.split()),
        'answer_words': len(a.split()),
        'total_chars': len(q) + len(a),
        'has_question_mark': '?' in q,
        'answer_sentences': len([s for s in a.split('.') if s.strip()])
    }


# Example usage and testing
if __name__ == "__main__":
    # Test valid card
    valid, msg = validate_card(
        "What is DNA?",
        "DNA (deoxyribonucleic acid) is the hereditary material in humans and almost all other organisms."
    )
    print(f"Valid card: {valid}, Message: {msg}")
    
    # Test invalid card - empty
    valid, msg = validate_card("", "Some answer")
    print(f"Empty question: {valid}, Message: {msg}")
    
    # Test invalid card - too simple
    valid, msg = validate_card("Is DNA important?", "yes")
    print(f"Simple answer: {valid}, Message: {msg}")
    
    # Test sanitization
    clean_q, clean_a = sanitize_card(
        "What   is    DNA?  ",
        "DNA is   the   molecule\n\n\nthat carries genetic information."
    )
    print(f"Sanitized Q: '{clean_q}'")
    print(f"Sanitized A: '{clean_a}'")
    
    # Test warnings
    warnings = get_card_warnings(
        "WHAT IS DNA",
        "It's DNA"
    )
    print(f"Warnings: {warnings}")
