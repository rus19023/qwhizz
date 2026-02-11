# data/card_format.py
"""
Enhanced card format specification for the flashcard system

Cards can now include:
- Images (URLs or file paths)
- Multiple choice options (up to 10)
- Multi-select questions with multiple correct answers
- True/False questions
"""

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


def validate_card(card):
    """
    Validate card structure
    
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if "question" not in card or "answer" not in card:
        return False, "Card must have 'question' and 'answer' fields"
    
    card_type = card.get("type", "flashcard")
    
    if card_type == "multiple_choice":
        if "options" not in card or "correct_index" not in card:
            return False, "Multiple choice cards need 'options' and 'correct_index'"
        if not (0 <= card["correct_index"] < len(card["options"])):
            return False, "correct_index out of range"
        if len(card["options"]) > 10:
            return False, "Maximum 10 options allowed"
    
    elif card_type == "multi_select":
        if "options" not in card or "correct_indices" not in card:
            return False, "Multi-select cards need 'options' and 'correct_indices'"
        if not isinstance(card["correct_indices"], list):
            return False, "correct_indices must be a list"
        if len(card["options"]) > 10:
            return False, "Maximum 10 options allowed"
        for idx in card["correct_indices"]:
            if not (0 <= idx < len(card["options"])):
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
