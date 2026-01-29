# core/quiz_generator.py

import random
from difflib import SequenceMatcher


def generate_fake_answers(correct_answer, all_answers, count=3):
    """Generate plausible fake answers"""
    fake_answers = []
    
    # Remove correct answer from pool
    available_answers = [a for a in all_answers if a.lower().strip() != correct_answer.lower().strip()]
    
    if len(available_answers) >= count:
        # Use other real answers as distractors
        fake_answers = random.sample(available_answers, count)
    else:
        # If not enough real answers, use what we have
        fake_answers = available_answers.copy()
        
        # Fill remaining with variations
        while len(fake_answers) < count:
            variation = _create_variation(correct_answer)
            if variation not in fake_answers:
                fake_answers.append(variation)
    
    return fake_answers


def _create_variation(answer):
    """Create a plausible variation of an answer"""
    variations = [
        answer + " (incorrect)",
        "Not " + answer,
        answer.replace("is", "is not") if "is" in answer else answer + " variation",
        answer.split()[0] if len(answer.split()) > 1 else answer + " alternative"
    ]
    return random.choice(variations)


def generate_true_false_statement(question, answer, is_true=True):
    """Generate a true/false statement"""
    if is_true:
        return f"{question.rstrip('?')} → {answer}"
    else:
        # Create false statement
        fake_answer = f"Not {answer}" if random.random() > 0.5 else f"{answer} (incorrect version)"
        return f"{question.rstrip('?')} → {fake_answer}"


def create_multiple_choice_question(card, all_cards):
    """Create a multiple choice question from a card"""
    correct_answer = card["answer"]
    all_answers = [c["answer"] for c in all_cards]
    
    # Generate 3 fake answers
    fake_answers = generate_fake_answers(correct_answer, all_answers, count=3)
    
    # Combine and shuffle
    all_options = fake_answers + [correct_answer]
    random.shuffle(all_options)
    
    # Find correct index
    correct_index = all_options.index(correct_answer)
    
    return {
        "question": card["question"],
        "options": all_options,
        "correct_index": correct_index,
        "correct_answer": correct_answer
    }


def create_true_false_question(card):
    """Create a true/false question from a card"""
    is_true = random.random() > 0.5
    
    return {
        "statement": generate_true_false_statement(card["question"], card["answer"], is_true),
        "is_true": is_true,
        "correct_answer": card["answer"]
    }