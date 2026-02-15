"""
Theme Switcher for Streamlit
A modular theming system with dropdown selector and hybrid theme discovery.
"""

from .theme_switcher import ThemeSwitcher, apply_theme, quick_theme_setup

__all__ = ['ThemeSwitcher', 'apply_theme', 'quick_theme_setup']
__version__ = '2.0.0'