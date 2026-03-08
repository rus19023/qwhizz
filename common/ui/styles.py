import streamlit as st

APP_CSS = """
<style>
    MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    #header {visibility: hidden;}
    .stDeployButton {display: none;}

    .block-container { padding-top: 1rem; 
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            }

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
        # height: 80px !important;
        white-space: normal !important;
        overflow-y: auto !important;
    }

    /* Make main content wider */
    section.main > div {
        max-width: 98% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Shrink tab padding */
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

/* Make multiple choice buttons taller */
button[key^="mc_option_"] {
    min-height: 12rem !important;
    font-size: 1rem !important;
    padding: .75rem !important;
}

/* =========================
   Multiple Choice "Quiz App" Buttons
   ========================= */
   
/* Make the column containers full height and stretch children */
.mc-mode div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
.mc-mode div[data-testid="stVerticalBlock"] > div {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.mc-mode div[data-testid="stButton"] {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.mc-mode div[data-testid="stButton"] button {
    width: 100% !important;
    flex: 1 !important;           /* grow to fill parent instead of fixed height */
    min-height: 80px !important;  /* just a floor, not a ceiling */
    padding: 14px !important;
    border-radius: 16px !important;
    font-size: 12px !important;
    line-height: 1.0 !important;
    font-weight: 600 !important;
    white-space: normal !important;
    text-align: left !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
}

/* Hover effect */
.mc-mode div[data-testid="stButton"] button:hover {
    transform: translateY(-1px);
    filter: brightness(1.05);
}

/* Pressed/click effect */
.mc-mode div[data-testid="stButton"] button:active {
    transform: translateY(0px) scale(0.99);
}

/* Subtle focus ring for accessibility */
.mc-mode div[data-testid="stButton"] button:focus {
    outline: 2px solid rgba(255,255,255,0.35) !important;
    outline-offset: 2px !important;
}

</style>
"""

def apply_global_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)