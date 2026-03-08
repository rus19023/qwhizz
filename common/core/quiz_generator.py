# core/quiz_generator.py

import random
from difflib import SequenceMatcher

headers={
    "Content-Type": "application/json",
    "x-api-key": st.secrets["ANTHROPIC_API_KEY"],
    "anthropic-version": "2023-06-01",
}


def _get_wrong_answers(card):
    """Extract stored wrong answers from a card, checking all possible field names."""
    return (
        card.get("wrong_answers")
        or card.get("distractors")
        or card.get("incorrect_answers")
        or []
    )


def generate_fake_answers(correct_answer, card, all_cards, count=3):
    """
    Generate plausible fake answers.
    Priority:
      1. Stored wrong_answers/distractors on the card itself
      2. Other cards' correct answers as distractors
      3. Generated variations as a last resort
    """
    fake_answers = []

    # 1. Use stored wrong answers first
    stored_wrong = [
        w for w in _get_wrong_answers(card)
        if w and w.lower().strip() != correct_answer.lower().strip()
    ]
    if stored_wrong:
        sampled = random.sample(stored_wrong, min(count, len(stored_wrong)))
        fake_answers.extend(sampled)

    # 2. Fill remaining slots from other cards' correct answers
    if len(fake_answers) < count:
        other_answers = [
            c["answer"] for c in all_cards
            if c["answer"].lower().strip() != correct_answer.lower().strip()
            and c["answer"] not in fake_answers
        ]
        still_needed = count - len(fake_answers)
        if len(other_answers) >= still_needed:
            fake_answers.extend(random.sample(other_answers, still_needed))
        else:
            fake_answers.extend(other_answers)

    # 3. Last resort: generate variations
    while len(fake_answers) < count:
        variation = _create_variation(correct_answer)
        if variation not in fake_answers:
            fake_answers.append(variation)

    return fake_answers[:count]


def _create_variation(answer):
    """Create a plausible variation of an answer (last resort only)."""
    variations = [
        f"Incorrect: {answer}",
        f"Similar to {answer}",
        f"Related: {answer.split()[0] if len(answer.split()) > 1 else answer}",
        f"Alternative explanation"
    ]
    return random.choice(variations)


def generate_true_false_statement(question, answer, is_true=True):
    """Generate a true/false statement"""
    if is_true:
        return f"{question.rstrip('?')} → {answer}"
    else:
        fake_answer = f"Not {answer}" if random.random() > 0.5 else f"{answer} (incorrect version)"
        return f"{question.rstrip('?')} → {fake_answer}"


def create_multiple_choice_question(card, all_cards):
    """Create a multiple choice question from a card"""
    correct_answer = card["answer"]

    # Generate 3 distractors, using stored wrong answers when available
    fake_answers = generate_fake_answers(correct_answer, card, all_cards, count=3)

    # Combine and shuffle
    all_options = fake_answers + [correct_answer]
    random.shuffle(all_options)

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