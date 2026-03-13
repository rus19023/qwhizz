import streamlit as st

APP_CSS = """
<style>
    /* ── Hide Streamlit chrome ─────────────────────────────────────────── */
    MainMenu          { visibility: hidden; }
    footer            { visibility: hidden; }
    #header           { visibility: hidden; }
    .stDeployButton   { display: none; }

    /* ── Full-width layout ─────────────────────────────────────────────
       Use wide padding on desktop, tighter on mobile.
       DO NOT set max-width: 100% here — it breaks Streamlit's
       responsive column system. Let Streamlit control max-width.
    ──────────────────────────────────────────────────────────────────── */
    .block-container {
        padding-top:   1rem !important;
        padding-left:  1.5rem !important;
        padding-right: 1.5rem !important;
        /* Streamlit default max-width is ~730px. Override to get full width: */
        max-width: min(98vw, 1400px) !important;
    }

    /* ── Sidebar — let Streamlit handle mobile collapse natively ───────
       REMOVED: transform: translateX(0) — that was locking the sidebar
       open and breaking the mobile hamburger menu entirely.
    ──────────────────────────────────────────────────────────────────── */

    /* Make the collapsed-control (hamburger) button always visible */
    button[kind="header"],
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display:    block !important;
        opacity:    1 !important;
        z-index:    999999 !important;
    }

    /* ── Buttons — allow text to wrap ──────────────────────────────── */
    div[data-testid="stButton"] button {
        white-space: normal !important;
        overflow-y:  auto !important;
    }

    /* ── Tabs — scrollable on small screens ────────────────────────── */
    button[data-baseweb="tab"] {
        padding:    6px 12px !important;
        font-size:  14px !important;
        white-space: nowrap !important;
    }
    div[role="tablist"] {
        gap:        6px !important;
        overflow-x: auto !important;
        flex-wrap:  nowrap !important;
    }

    /* ── Multiple choice buttons ────────────────────────────────────── */
    .mc-mode div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
    .mc-mode div[data-testid="stVerticalBlock"] > div {
        height:         100%;
        display:        flex;
        flex-direction: column;
    }
    .mc-mode div[data-testid="stButton"] {
        flex:           1;
        display:        flex;
        flex-direction: column;
    }
    .mc-mode div[data-testid="stButton"] button {
        width:          100% !important;
        flex:           1 !important;
        min-height:     80px !important;
        padding:        14px !important;
        border-radius:  16px !important;
        font-size:      12px !important;
        line-height:    1.0 !important;
        font-weight:    600 !important;
        white-space:    normal !important;
        text-align:     left !important;
        display:        flex !important;
        align-items:    center !important;
        justify-content: flex-start !important;
    }
    .mc-mode div[data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        filter:    brightness(1.05);
    }
    .mc-mode div[data-testid="stButton"] button:active {
        transform: translateY(0px) scale(0.99);
    }
    .mc-mode div[data-testid="stButton"] button:focus {
        outline:        2px solid rgba(255,255,255,0.35) !important;
        outline-offset: 2px !important;
    }

    /* ── Mobile tweaks ──────────────────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container {
            padding-left:  0.5rem !important;
            padding-right: 0.5rem !important;
        }

        /* Stack MC buttons vertically on small screens */
        .mc-mode div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }

        /* Make tabs font smaller on mobile */
        button[data-baseweb="tab"] {
            font-size:  11px !important;
            padding:    4px 8px !important;
        }
    }
</style>
"""

def apply_global_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)