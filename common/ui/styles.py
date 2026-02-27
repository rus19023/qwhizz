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
<<<<<<< HEAD
=======
/* =========================
   Multiple Choice "Quiz App" Buttons
   ========================= */

.mc-mode div[data-testid="stButton"] button {
    width: 100% !important;
    min-height: 160px !important;     /* uniform height */
    height: 160px !important;
    padding: 14px 14px !important;
    border-radius: 16px !important;   /* rounded */
    font-size: 14px !important;       /* smaller but readable */
    line-height: 1.25 !important;
    font-weight: 600 !important;
    white-space: normal !important;   /* allow wrapping */
    overflow: hidden !important;
    text-align: left !important;      /* quiz-app style */
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
}

/* Better spacing between the two columns */
.mc-mode [data-testid="column"] {
    padding: 6px !important;
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
>>>>>>> 0da8c8439b43acd744d086feac38f23e40a65cda
</style>
"""

def apply_global_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)