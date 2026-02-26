"""
data/card_format.py

Enhanced card format specification for the flashcard system

Cards can now include:
- Images (URLs or file paths)
- Multiple choice options (up to 10)
- Multi-select questions with multiple correct answers
- True/False questions
"""

import re
from data.deck_store import get_deck

# Example card formats:

# STANDARD FLASHCARD
FLASHCARD_EXAMPLE = {
    "question": "What is DNA?",
    "answer": "Deoxyribonucleic acid - the molecule that carries genetic information",
    "type": "flashcard"
}

# MULTIPLE CHOICE (Single correct answer)
MULTIPLE_CHOICE_EXAMPLE = {
    "question": "What are the four DNA bases?",
    "answer": "A, T, G, C",  # The full answer text
    "type": "multiple_choice",
    "options": [
        "A, T, G, C",      # Index 0 - CORRECT
        "A, U, G, C",      # Index 1
        "A, T, X, Y",      # Index 2
        "B, D, E, F"       # Index 3
    ],
    "correct_index": 0
}

# MULTI-SELECT (Multiple correct answers)
MULTI_SELECT_EXAMPLE = {
    "question": "Which of the following are purines?",
    "answer": "Adenine and Guanine are purines",
    "type": "multi_select",
    "options": [
        "Adenine",    # Index 0 - CORRECT
        "Thymine",    # Index 1
        "Guanine",    # Index 2 - CORRECT
        "Cytosine"    # Index 3
    ],
    "correct_indices": [0, 2],  # List of correct indices
    "num_correct": 2  # Fixed number of correct answers
}

# TRUE/FALSE
TRUE_FALSE_EXAMPLE = {
    "question": "DNA is double-stranded",
    "answer": "True - DNA forms a double helix structure",
    "type": "true_false",
    "correct_answer": True
}

# WITH IMAGE
IMAGE_EXAMPLE = {
    "question": "What process is shown in this diagram?",
    "answer": "DNA Replication",
    "type": "multiple_choice",
    "image_url": "https://example.com/dna_replication.png",  # Can be URL or local path
    "options": [
        "DNA Replication",
        "Transcription",
        "Translation",
        "DNA Repair"
    ],
    "correct_index": 0
}


def validate_card(question, answer, *args, **kwargs):
    """
    Validate card structure

    Accepts either:
      - validate_card(card_dict, answer_str)
      - validate_card(question_str, answer_str)

    Returns:
        (bool, str): (is_valid, error_message)
    """
    # Normalize inputs into a single dict `card`
    if isinstance(question, dict):
        card = dict(question)  # shallow copy
        if not isinstance(answer, str) or not answer:
            answer = card.get("answer", "")
        card.setdefault("answer", answer)
        card.setdefault("question", card.get("question", ""))
    else:
        card = {"question": question, "answer": answer}

    # Basic required fields
    q = (card.get("question") or "")
    a = (card.get("answer") or "")
    if not isinstance(q, str) or not q.strip():
        return False, "Question cannot be empty"
    if not isinstance(a, str) or not a.strip():
        return False, "Answer cannot be empty"

    card_type = card.get("type", "flashcard")

    if card_type == "multiple_choice":
        if "options" not in card or "correct_index" not in card:
            return False, "Multiple choice cards need 'options' and 'correct_index'"
        if not isinstance(card["options"], list) or len(card["options"]) < 2:
            return False, "options must be a list with at least 2 items"
        if len(card["options"]) > 10:
            return False, "Maximum 10 options allowed"
        if not isinstance(card["correct_index"], int):
            return False, "correct_index must be an integer"
        if not (0 <= card["correct_index"] < len(card["options"])):
            return False, "correct_index out of range"

    elif card_type == "multi_select":
        if "options" not in card or "correct_indices" not in card:
            return False, "Multi-select cards need 'options' and 'correct_indices'"
        if not isinstance(card["options"], list) or len(card["options"]) < 3:
            return False, "options must be a list with at least 3 items"
        if len(card["options"]) > 10:
            return False, "Maximum 10 options allowed"
        if not isinstance(card["correct_indices"], list):
            return False, "correct_indices must be a list"
        for idx in card["correct_indices"]:
            if not isinstance(idx, int) or not (0 <= idx < len(card["options"])):
                return False, f"correct_index {idx} out of range"

    elif card_type == "true_false":
        if "correct_answer" not in card:
            return False, "True/false cards need 'correct_answer'"
        if not isinstance(card["correct_answer"], bool):
            return False, "correct_answer must be True or False"

    return True, ""

def get_card_type(card):
    """Determine card type, defaulting to flashcard"""
    return card.get("type", "flashcard")


def is_game_card(card):
    """Check if card has game mode data (multiple choice, true/false, etc.)"""
    card_type = get_card_type(card)
    return card_type in ["multiple_choice", "multi_select", "true_false"]

# Card validation and formatting utilities



# Configuration constants
MAX_QUESTION_LENGTH = 5000
MAX_ANSWER_LENGTH = 10000
MIN_ANSWER_LENGTH = 3
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
    # If validate_card was called with a full card dict as "question"
    if isinstance(question, dict):
        card = question
        question = card.get("question", "")
        answer = card.get("answer", answer if isinstance(answer, str) else "")

    q = (question or "").strip()
    a = (answer or "").strip()
    
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
    return True, 
    
    


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
    
    if isinstance(question, dict):
        card = question
        question = card.get("question", "")
        answer = card.get("answer", answer if isinstance(answer, str) else "")

    q = (question or "").strip()
    a = (answer or "").strip()
    
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
    if isinstance(question, dict):
        card = question
        question = card.get("question", "")
        answer = card.get("answer", answer if isinstance(answer, str) else "")

    q = (question or "").strip()
    a = (answer or "").strip()
    
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