import streamlit as st
import streamlit.components.v1 as components

# Page config
st.set_page_config(
    page_title="Aurelia",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom fonts and apply luxury minimal styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=Montserrat:wght@200;300;400;500&family=Cinzel:wght@400;500;600&display=swap" rel="stylesheet">
    
    <style>
    /* === HIDE STREAMLIT BRANDING === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* === LUXURY PALETTE === */
    :root {
        --cream: #FDFCFB;
        --warm-white: #F9F7F4;
        --stone: #E8E4DE;
        --taupe: #D4CEC5;
        --charcoal: #2C2C2C;
        --deep-charcoal: #1A1A1A;
        --gold: #C9A875;
        --rose-gold: #B88B7A;
        --silver: #B8B8B8;
        --accent-subtle: #8B7E6E;
    }
    
    /* === REFINED FOUNDATION === */
    .stApp {
        background: linear-gradient(180deg, var(--cream) 0%, var(--warm-white) 100%);
        font-family: 'Montserrat', sans-serif;
        color: var(--charcoal);
        letter-spacing: 0.3px;
    }
    
    /* === SUBTLE TEXTURE OVERLAY === */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><filter id="noise"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/></filter><rect width="100" height="100" filter="url(%23noise)" opacity="0.03"/></svg>');
        opacity: 0.5;
        pointer-events: none;
        z-index: 0;
    }
    
    /* === ELEGANT CONTAINER === */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 5rem !important;
        max-width: 1100px !important;
        position: relative;
        z-index: 1;
    }
    
    /* === REFINED SPACING === */
    div[data-testid="stVerticalBlock"] > div {
        padding: 0 !important;
        margin-bottom: 3rem !important;
    }
    
    /* === SOPHISTICATED TYPOGRAPHY === */
    h1 {
        font-family: 'Cinzel', serif !important;
        font-weight: 400 !important;
        font-size: 4rem !important;
        color: var(--deep-charcoal) !important;
        letter-spacing: 8px !important;
        margin: 0 0 0.5rem 0 !important;
        line-height: 1.1 !important;
        text-transform: uppercase;
    }
    
    h2 {
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 300 !important;
        font-size: 2.5rem !important;
        color: var(--charcoal) !important;
        letter-spacing: 2px !important;
        margin: 0 0 1.5rem 0 !important;
        line-height: 1.3 !important;
    }
    
    h3 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        font-size: 1.1rem !important;
        color: var(--accent-subtle) !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        margin: 0 0 1rem 0 !important;
    }
    
    p, label, .stMarkdown {
        font-family: 'Montserrat', sans-serif;
        color: var(--charcoal);
        font-size: 0.95rem;
        line-height: 1.8;
        font-weight: 300;
        letter-spacing: 0.3px;
    }
    
    /* === REFINED INPUT FIELDS === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--taupe) !important;
        border-radius: 0 !important;
        color: var(--deep-charcoal) !important;
        padding: 12px 0 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 300 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        outline: none !important;
        border-bottom-color: var(--gold) !important;
        border-bottom-width: 1px !important;
        background: transparent !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--silver) !important;
        font-style: italic;
        font-weight: 200;
    }
    
    /* Refined input labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: var(--accent-subtle) !important;
        font-weight: 400 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* === ELEGANT BUTTONS === */
    .stButton > button {
        background: transparent !important;
        color: var(--deep-charcoal) !important;
        border: 1px solid var(--charcoal) !important;
        border-radius: 0 !important;
        padding: 16px 48px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
        font-size: 0.85rem !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: var(--deep-charcoal);
        transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: -1;
    }
    
    .stButton > button:hover {
        color: var(--cream) !important;
        border-color: var(--deep-charcoal) !important;
    }
    
    .stButton > button:hover::before {
        left: 0;
    }
    
    /* === REFINED METRICS === */
    div[data-testid="stMetricValue"] {
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 3rem !important;
        font-weight: 300 !important;
        color: var(--deep-charcoal) !important;
        letter-spacing: 1px !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--accent-subtle) !important;
        font-size: 0.7rem !important;
        font-weight: 400 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        margin-bottom: 0.5rem !important;
    }
    
    div[data-testid="stMetricDelta"] {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 300 !important;
    }
    
    [data-testid="metric-container"] {
        background: transparent !important;
        padding: 2rem 0 !important;
        border-bottom: 1px solid var(--stone);
    }
    
    /* === MINIMAL SLIDER === */
    .stSlider > div > div > div {
        background: var(--stone) !important;
        height: 1px !important;
    }
    
    .stSlider > div > div > div > div {
        background: var(--gold) !important;
        border: none !important;
        width: 16px !important;
        height: 16px !important;
        border-radius: 50% !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    .stSlider > div > div > div > div:hover {
        transform: scale(1.2);
        box-shadow: 0 4px 12px rgba(201, 168, 117, 0.3) !important;
    }
    
    /* === SOPHISTICATED TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3rem;
        background: transparent;
        border-bottom: 1px solid var(--stone);
        padding-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: var(--silver);
        font-family: 'Montserrat', sans-serif;
        font-weight: 300;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 0 0 1rem 0;
        transition: all 0.4s ease;
        position: relative;
    }
    
    .stTabs [data-baseweb="tab"]::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 0;
        height: 1px;
        background: var(--gold);
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--charcoal);
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--deep-charcoal) !important;
        font-weight: 400 !important;
    }
    
    .stTabs [aria-selected="true"]::after {
        width: 100%;
    }
    
    /* === REFINED CHECKBOX === */
    .stCheckbox {
        padding: 0.8rem 0;
    }
    
    .stCheckbox > label {
        color: var(--charcoal) !important;
        font-weight: 300 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px !important;
    }
    
    /* === ELEGANT DIVIDER === */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--stone), transparent);
        margin: 4rem 0 !important;
    }
    
    /* === LUXURY CARD === */
    .luxury-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.6), rgba(255,255,255,0.3));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(232, 228, 222, 0.5);
        padding: 3rem;
        margin: 2rem 0;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .luxury-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, var(--gold), transparent);
        opacity: 0;
        transition: opacity 0.5s ease;
        pointer-events: none;
    }
    
    .luxury-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
        border-color: rgba(201, 168, 117, 0.3);
    }
    
    .luxury-card:hover::before {
        opacity: 0.03;
    }
    
    /* === ACCENT LINE === */
    .accent-line {
        width: 60px;
        height: 1px;
        background: var(--gold);
        margin: 1.5rem 0;
    }
    
    /* === REFINED BADGE === */
    .luxury-badge {
        display: inline-block;
        background: transparent;
        border: 1px solid var(--taupe);
        color: var(--accent-subtle);
        padding: 6px 18px;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.7rem;
        font-weight: 300;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-right: 12px;
        margin-bottom: 12px;
        transition: all 0.4s ease;
    }
    
    .luxury-badge:hover {
        border-color: var(--gold);
        color: var(--gold);
        transform: translateY(-2px);
    }
    
    /* === SECTION DIVIDER === */
    .section-divider {
        text-align: center;
        position: relative;
        margin: 4rem 0;
    }
    
    .section-divider::before,
    .section-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 45%;
        height: 1px;
        background: linear-gradient(to right, transparent, var(--stone));
    }
    
    .section-divider::before {
        left: 0;
    }
    
    .section-divider::after {
        right: 0;
        background: linear-gradient(to left, transparent, var(--stone));
    }
    
    .section-divider span {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.5rem;
        color: var(--gold);
        background: var(--cream);
        padding: 0 2rem;
        position: relative;
    }
    
    /* === SMOOTH ANIMATIONS === */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .block-container > div {
        animation: fadeIn 1s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* === REFINED SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--warm-white);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--taupe);
        border-radius: 4px;
        transition: background 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--gold);
    }
    
    /* === COLUMN REFINEMENT === */
    [data-testid="column"] {
        padding: 0 1.5rem !important;
    }
    
    [data-testid="column"]:first-child {
        padding-left: 0 !important;
    }
    
    [data-testid="column"]:last-child {
        padding-right: 0 !important;
    }
    
    /* === QUOTE STYLING === */
    blockquote {
        border-left: 2px solid var(--gold);
        padding-left: 2rem;
        margin: 2rem 0;
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.3rem;
        font-style: italic;
        font-weight: 300;
        color: var(--charcoal);
        line-height: 1.7;
    }
    </style>
""", unsafe_allow_html=True)

# Elegant header
st.markdown("""
    <div style="text-align: center; margin-bottom: 4rem;">
        <h1>AURELIA</h1>
        <h2 style="font-style: italic; margin-top: 0.5rem;">Refined Analytics</h2>
        <div class="accent-line" style="margin: 2rem auto;"></div>
        <p style="font-size: 0.9rem; letter-spacing: 2px; color: var(--accent-subtle); margin-top: 2rem;">
            WHERE PRECISION MEETS ELEGANCE
        </p>
    </div>
""", unsafe_allow_html=True)

# Luxury badges
st.markdown("""
    <div style="text-align: center; margin-bottom: 4rem;">
        <span class="luxury-badge">Premium</span>
        <span class="luxury-badge">Exclusive</span>
        <span class="luxury-badge">Curated</span>
    </div>
""", unsafe_allow_html=True)

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Portfolio Value", "$2.4M", "+8.2%")

with col2:
    st.metric("Annual Return", "14.7%", "+2.3%")

with col3:
    st.metric("Assets", "247", "+12")

with col4:
    st.metric("Performance", "96.8", "+1.2")

# Divider
st.markdown('<div class="section-divider"><span>◇</span></div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Insights", "Preferences"])

with tab1:
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="luxury-card">
                <h3>Portfolio Composition</h3>
                <div class="accent-line"></div>
                <p style="margin-bottom: 1.5rem;">
                    Your carefully curated portfolio demonstrates exceptional balance across sectors, 
                    maintaining stability while capitalizing on growth opportunities in emerging markets.
                </p>
                <p style="font-size: 0.85rem; color: var(--accent-subtle); margin: 0;">
                    Equities 62% • Bonds 24% • Alternatives 14%
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="luxury-card">
                <h3>Recent Activity</h3>
                <div class="accent-line"></div>
                <p style="margin-bottom: 1.5rem;">
                    Strategic acquisitions in the technology sector have yielded remarkable returns, 
                    reflecting our commitment to identifying value before the broader market.
                </p>
                <p style="font-size: 0.85rem; color: var(--accent-subtle); margin: 0;">
                    Last transaction: 3 hours ago
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    st.slider("Investment Horizon (Years)", 1, 30, 10)

with tab2:
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="luxury-card">
            <h3>Market Analysis</h3>
            <div class="accent-line"></div>
            <blockquote>
                "The disciplined investor finds opportunity where others see uncertainty, 
                guided by fundamentals rather than sentiment."
            </blockquote>
            <p style="margin-top: 2rem;">
                Current market conditions favor a measured approach, balancing growth potential 
                with capital preservation. Our analysis suggests selective positioning in sectors 
                demonstrating structural resilience and pricing power.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Sector Focus", [
            "Technology & Innovation",
            "Healthcare & Biotech",
            "Sustainable Energy",
            "Financial Services"
        ])
    
    with col2:
        st.selectbox("Risk Profile", [
            "Conservative",
            "Balanced",
            "Growth-Oriented",
            "Aggressive"
        ])

with tab3:
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("<h3>Account Settings</h3>", unsafe_allow_html=True)
    st.markdown("<div class='accent-line'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Account Name", placeholder="Enter your name")
        st.text_input("Email Address", placeholder="your@email.com")
        st.text_input("Phone Number", placeholder="+1 (555) 000-0000")
    
    with col2:
        st.selectbox("Preferred Currency", ["USD", "EUR", "GBP", "CHF"])
        st.selectbox("Communication Preference", ["Email", "Phone", "Secure Message"])
        st.selectbox("Statement Frequency", ["Monthly", "Quarterly", "Annually"])
    
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-divider"><span>◇</span></div>', unsafe_allow_html=True)
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    st.checkbox("Enable two-factor authentication")
    st.checkbox("Receive market insights newsletter")
    st.checkbox("Opt-in to exclusive opportunities")
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    st.button("Update Preferences")

# Footer
st.markdown('<div class="section-divider"><span>◇</span></div>', unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <p style="font-size: 0.75rem; letter-spacing: 3px; color: var(--silver); margin: 0;">
            AURELIA ANALYTICS © 2026
        </p>
        <p style="font-size: 0.7rem; letter-spacing: 2px; color: var(--taupe); margin-top: 0.5rem;">
            Crafted with precision and care
        </p>
    </div>
""", unsafe_allow_html=True)
