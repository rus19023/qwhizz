# core/quiz_generator.py

import random
import requests
from difflib import SequenceMatcher
import streamlit as st


def _get_headers():
    return {
        "Content-Type": "application/json",
        "x-api-key": st.secrets["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
    }


def _is_too_similar(a, b, threshold=0.85):
    """Return True if two strings are suspiciously similar."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio() > threshold


def _get_wrong_answers(card):
    raw = (
        card.get("wrong_answers")
        or card.get("distractors")
        or card.get("incorrect_answers")
        or []
    )
    return [w for w in raw if w and not w.strip().startswith("[DISTRACTOR")]


def _generate_ai_distractors(question, correct_answer, count=3):
    """Call Claude API to generate plausible wrong answers."""
    prompt = (
        f"Generate exactly {count} plausible but incorrect answers for this flashcard.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {correct_answer}\n\n"
        f"Rules:\n"
        f"- Each wrong answer should be believable but clearly incorrect\n"
        f"- Same format/length as the correct answer\n"
        f"- No duplicates or near-duplicates of each other or the correct answer\n"
        f"- Return ONLY a plain numbered list, one per line, no explanations\n"
        f"Example format:\n1. Wrong answer one\n2. Wrong answer two\n3. Wrong answer three"
    )

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=_get_headers(),
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=10
        )
        response.raise_for_status()
        text = response.json()["content"][0]["text"]

        # Parse numbered list
        distractors = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip leading "1. " or "- " etc.
            if line[0].isdigit() and len(line) > 2 and line[1] in ".):":
                line = line[2:].strip()
            elif line.startswith("- "):
                line = line[2:].strip()
            if line and not _is_too_similar(line, correct_answer):
                distractors.append(line)

        return distractors[:count]

    except Exception as e:
        st.warning(f"Could not generate AI distractors: {e}")
        return []


def generate_fake_answers(correct_answer, card, all_cards, count=3):
    """
    Generate plausible fake answers.
    Priority:
      1. Stored wrong_answers/distractors on the card itself
      2. AI-generated distractors via Claude API
      3. Other cards' correct answers as a last resort
    """
    fake_answers = []

    # 1. Use stored wrong answers first (deduplicated by similarity)
    for w in _get_wrong_answers(card):
        if not w:
            continue
        if _is_too_similar(w, correct_answer):
            continue
        if any(_is_too_similar(w, existing) for existing in fake_answers):
            continue
        fake_answers.append(w)

    fake_answers = fake_answers[:count]

    # 2. Fill remaining with AI-generated distractors
    if len(fake_answers) < count:
        still_needed = count - len(fake_answers)
        ai_distractors = _generate_ai_distractors(
            card.get("question", ""), correct_answer, count=still_needed
        )
        for d in ai_distractors:
            if not _is_too_similar(d, correct_answer) and not any(_is_too_similar(d, f) for f in fake_answers):
                fake_answers.append(d)

    # 3. Last resort: other cards' answers
    if len(fake_answers) < count:
        other_answers = [
            c["answer"] for c in all_cards
            if c["answer"].lower().strip() != correct_answer.lower().strip()
            and c["answer"] not in fake_answers
            and not _is_too_similar(c["answer"], correct_answer)
            and not any(_is_too_similar(c["answer"], f) for f in fake_answers)
        ]
        still_needed = count - len(fake_answers)
        if len(other_answers) >= still_needed:
            fake_answers.extend(random.sample(other_answers, still_needed))
        else:
            fake_answers.extend(other_answers)

    return fake_answers[:count]


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

    fake_answers = generate_fake_answers(correct_answer, card, all_cards, count=3)

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