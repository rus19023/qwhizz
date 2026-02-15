import streamlit as st
from pathlib import Path

def get_package_dir():
    """Get the package directory path"""
    return Path(__file__).parent

def quick_theme_setup():
    package_dir = get_package_dir()
    theme_base_path = package_dir / "theme_base.css"
    themes_dir = package_dir / "themes"
    
    # Load base CSS
    if theme_base_path.exists():
        with open(theme_base_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Get available themes
    theme_files = list(themes_dir.glob("*.css"))
    theme_names = [f.stem for f in theme_files]
    
    # Theme selector in sidebar
    selected_theme = st.sidebar.selectbox(
        "🎨 Choose Theme",
        options=theme_names,
        key="theme_selector"
    )
    
    # Apply selected theme
    apply_theme(selected_theme)

def apply_theme(theme_name):
    package_dir = get_package_dir()
    theme_path = package_dir / "themes" / f"{theme_name}.css"
    
    if theme_path.exists():
        with open(theme_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)