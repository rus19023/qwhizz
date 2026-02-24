import streamlit as st

APP_CSS = """
<style>
MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

.block-container { padding-top: 1rem; }

section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: translateX(0) !important;
    margin-left: 0 !important;
}

button[kind="header"],
[data-testid="collapsedControl"] {
    background: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #000000 !important;
    padding: 8px !important;
    visibility: visible !important;
    display: block !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}

div[data-testid="stButton"] button {
    height: 80px !important;
    white-space: normal !important;
    overflow-y: auto !important;
}
</style>
"""

def apply_global_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)