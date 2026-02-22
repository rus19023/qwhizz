import streamlit as st

# Page configuration MUST be first
st.set_page_config(
    page_title="🧬 DNA Study Gamified",
    page_icon="🧬🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme setup (package handles its own paths automatically)
from theme_switcher import quick_theme_setup
quick_theme_setup(default_theme='retro')
