# core/study_modes.py

import streamlit as st

STUDY_MODES = {
    "multiple_choice": {
        "name": "🎯 Multiple Choice",
        "description": "Choose the correct answer from 4 options",
        "requires_typing": False,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0,
        "is_game_mode": True
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
    "flashcard": {
        "name": "📇 Flashcard Mode",
        "description": "Traditional flip cards (honor system)",
        "requires_typing": False,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0.1
    },
    "quiz": {
        "name": "✍️ Quiz Mode",
        "description": "Type your answer for verification",
        "requires_typing": True,
        "requires_commit": False,
        "min_delay": 0,
        "verification_rate": 0
    },
    "commit": {
        "name": "🎯 Commit Mode",
        "description": "Commit before revealing answer",
        "requires_typing": False,
        "requires_commit": True,
        "min_delay": 3,
        "verification_rate": 0.2
    },
    "hardcore": {
        "name": "🔥 Hardcore Mode",
        "description": "All anti-cheat features enabled",
        "requires_typing": True,
        "requires_commit": True,
        "min_delay": 5,
        "verification_rate": 0.3
    }
}


def get_mode_config(mode_key):
    """Get configuration for a study mode"""
    return STUDY_MODES.get(mode_key, STUDY_MODES["flashcard"])

def is_game_mode(mode_key: str) -> bool:
    """Return True if the mode is a game-style mode."""
    return mode_key in {
        "multiple_choice",
        "multi_select",
        "true_false",
        "quiz",
        "hardcore"
    }
