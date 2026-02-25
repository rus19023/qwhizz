import streamlit as st

APP_CSS = """
<style>
    MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    #header {visibility: hidden;}
    .stDeployButton {display: none;}

    .block-container { padding-top: 1rem; }

    # section[data-testid="stSidebar"] {
    #     display: block !important;
    #     visibility: visible !important;
    #     transform: translateX(0) !important;
    #     margin-left: 0 !important;
    # }

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

    /* Make main content wider */
    section.main > div {
        max-width: 98% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }/* Shrink tab padding */
    button[data-baseweb="tab"] {
        padding: 6px 12px !important;
        font-size: 14px !important;
        white-space: nowrap !important;
    }

    /* Reduce tab container spacing */
    div[role="tablist"] {
        gap: 6px !important;
    }
    div[role="tablist"] {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
}
</style>
"""

def apply_global_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)