# core/study_modes.py

import streamlit as st

STUDY_MODES = {
    "flashcard": {
        "name": "📇 Flashcard Mode",
        "description": "Traditional flip cards (honor system)",
        "requires_typing": False,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0.1,
        "is_game_mode": False
    },
    "multiple_choice": {
        "name": "🎯 Multiple Choice",
        "description": "Choose the correct answer from options",
        "requires_typing": False,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0,
        "is_game_mode": True,
        "max_options": 10
    },
    "multi_select": {
        "name": "☑️ Multi-Select",
        "description": "Select all correct answers (checkboxes)",
        "requires_typing": False,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0,
        "is_game_mode": True,
        "supports_multiple_correct": True
    },
    "true_false": {
        "name": "✓✗ True/False",
        "description": "Determine if the statement is true or false",
        "requires_typing": False,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0,
        "is_game_mode": True
    },
    "quiz": {
        "name": "✍️ Quiz Mode",
        "description": "Type your answer for verification",
        "requires_typing": True,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0,
        "is_game_mode": False
    },
    "commit": {
        "name": "🎯 Commit Mode",
        "description": "Commit before revealing answer",
        "requires_typing": False,
        "requires_commit": True,
        "min_delay": 3,
        "verification_rate": 0.2,
        "is_game_mode": False
    },
    "hardcore": {
        "name": "🔥 Hardcore Mode",
        "description": "All anti-cheat features enabled",
        "requires_typing": True,
        "requires_commit": True,
        "min_delay": 5,
        "verification_rate": 0.3,
        "is_game_mode": False
    }
}


def get_mode_config(mode_key):
    """Get configuration for a study mode"""
    return STUDY_MODES.get(mode_key, STUDY_MODES["flashcard"])


def is_game_mode(mode_key):
    """Check if mode is a game mode (multiple choice, true/false, etc.)"""
    config = get_mode_config(mode_key)
    return config.get("is_game_mode", False)
