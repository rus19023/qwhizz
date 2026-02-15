import streamlit as st
import streamlit.components.v1 as components

# Page config
st.set_page_config(
    page_title="SYSTEM.CORE",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom fonts and apply brutalist styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=Space+Grotesk:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    
    <style>
    /* === HIDE STREAMLIT BRANDING === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* === ROOT VARIABLES === */
    :root {
        --black: #0A0A0A;
        --white: #FAFAFA;
        --gray-dark: #1A1A1A;
        --gray-mid: #333333;
        --gray-light: #CCCCCC;
        --accent-red: #FF0000;
        --accent-yellow: #FFFF00;
        --grid-size: 8px;
    }
    
    /* === BRUTALIST FOUNDATION === */
    .stApp {
        background: var(--white);
        font-family: 'Space Grotesk', sans-serif;
        color: var(--black);
        line-height: 1.2;
    }
    
    /* === BRUTAL GRID BACKGROUND === */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(var(--gray-light) 1px, transparent 1px),
            linear-gradient(90deg, var(--gray-light) 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.3;
        z-index: 0;
        pointer-events: none;
    }
    
    /* === CONTAINER === */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
        position: relative;
        z-index: 1;
    }
    
    /* === HARSH BORDERS EVERYWHERE === */
    div[data-testid="stVerticalBlock"] > div {
        border: 4px solid var(--black) !important;
        background: var(--white);
        margin-bottom: 0 !important;
        padding: 0 !important;
        box-shadow: 12px 12px 0 var(--black);
        transition: none;
    }
    
    /* === TYPOGRAPHY - RAW AND DIRECT === */
    h1 {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 5rem !important;
        color: var(--black) !important;
        text-transform: uppercase !important;
        letter-spacing: -4px !important;
        margin: 0 !important;
        padding: 40px !important;
        background: var(--accent-yellow);
        border-bottom: 8px solid var(--black);
        line-height: 0.9 !important;
    }
    
    h2 {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        color: var(--black) !important;
        text-transform: uppercase !important;
        letter-spacing: -2px !important;
        margin: 0 !important;
        padding: 24px !important;
        background: var(--white);
        border-bottom: 4px solid var(--black);
        line-height: 1 !important;
    }
    
    h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        color: var(--black) !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        margin: 0 !important;
        padding: 16px 24px !important;
        background: var(--black);
        color: var(--white) !important;
        border: none;
    }
    
    p, label, .stMarkdown {
        font-family: 'Courier Prime', monospace;
        color: var(--black);
        font-size: 1rem;
        line-height: 1.5;
        font-weight: 400;
    }
    
    /* === BRUTAL INPUT FIELDS === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: var(--white) !important;
        border: 3px solid var(--black) !important;
        border-radius: 0 !important;
        color: var(--black) !important;
        padding: 16px !important;
        font-family: 'Courier Prime', monospace !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        transition: none !important;
        box-shadow: 4px 4px 0 var(--black) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        outline: none !important;
        border-color: var(--accent-red) !important;
        box-shadow: 6px 6px 0 var(--black) !important;
        transform: translate(-2px, -2px);
    }
    
    /* Input labels - harsh and direct */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: var(--black) !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        margin-bottom: 8px !important;
    }
    
    /* === BRUTAL BUTTONS === */
    .stButton > button {
        background: var(--black) !important;
        color: var(--white) !important;
        border: 4px solid var(--black) !important;
        border-radius: 0 !important;
        padding: 20px 40px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        transition: all 0.1s ease !important;
        box-shadow: 6px 6px 0 var(--accent-red) !important;
        width: 100%;
        cursor: pointer;
    }
    
    .stButton > button:hover {
        background: var(--accent-red) !important;
        transform: translate(2px, 2px) !important;
        box-shadow: 4px 4px 0 var(--black) !important;
    }
    
    .stButton > button:active {
        transform: translate(6px, 6px) !important;
        box-shadow: 0 0 0 var(--black) !important;
    }
    
    /* === METRICS - STARK AND NUMERICAL === */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        color: var(--black) !important;
        line-height: 1 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--black) !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        margin-bottom: 8px !important;
    }
    
    div[data-testid="stMetricDelta"] {
        font-family: 'Courier Prime', monospace !important;
        font-weight: 700 !important;
    }
    
    /* Metric containers */
    [data-testid="metric-container"] {
        background: var(--white) !important;
        border: 3px solid var(--black) !important;
        padding: 24px !important;
        box-shadow: 6px 6px 0 var(--black) !important;
    }
    
    /* === SLIDER - INDUSTRIAL FEEL === */
    .stSlider {
        padding: 24px !important;
    }
    
    .stSlider > div > div > div {
        background: var(--black) !important;
        height: 8px !important;
    }
    
    .stSlider > div > div > div > div {
        background: var(--accent-yellow) !important;
        border: 3px solid var(--black) !important;
        width: 24px !important;
        height: 24px !important;
        box-shadow: 3px 3px 0 var(--black) !important;
    }
    
    /* === TABS - UTILITARIAN NAVIGATION === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        border-bottom: 4px solid var(--black);
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--white);
        border: 3px solid var(--black);
        border-bottom: none;
        border-radius: 0;
        color: var(--black);
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 16px 32px;
        margin-right: 8px;
        transition: none;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--gray-light);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--black) !important;
        color: var(--white) !important;
        border-bottom: 4px solid var(--black) !important;
        margin-bottom: -4px;
    }
    
    /* === CHECKBOX & RADIO - HARSH CHECKMARKS === */
    .stCheckbox {
        padding: 12px 0;
    }
    
    .stCheckbox > label {
        color: var(--black) !important;
        font-weight: 700 !important;
        font-family: 'Courier Prime', monospace !important;
        font-size: 1.1rem !important;
    }
    
    .stCheckbox input[type="checkbox"] {
        width: 24px !important;
        height: 24px !important;
        border: 3px solid var(--black) !important;
        border-radius: 0 !important;
    }
    
    /* === DIVIDER - BRUTAL SEPARATOR === */
    hr {
        border: none;
        height: 4px;
        background: var(--black);
        margin: 0 !important;
    }
    
    /* === CUSTOM BRUTAL CARD === */
    .brutal-card {
        background: var(--white);
        border: 4px solid var(--black);
        padding: 32px;
        margin: 0;
        box-shadow: 8px 8px 0 var(--black);
        position: relative;
    }
    
    .brutal-card::before {
        content: '▪';
        position: absolute;
        top: 16px;
        right: 16px;
        font-size: 2rem;
        color: var(--accent-red);
    }
    
    /* === BRUTAL BADGE === */
    .brutal-badge {
        display: inline-block;
        background: var(--black);
        color: var(--white);
        border: 3px solid var(--black);
        padding: 8px 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-right: 12px;
        margin-bottom: 12px;
        box-shadow: 4px 4px 0 var(--accent-yellow);
    }
    
    /* === SECTION HEADERS === */
    .section-header {
        background: var(--black);
        color: var(--white);
        padding: 16px 24px;
        margin: 0 0 0 0;
        border: 4px solid var(--black);
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 3px;
    }
    
    /* === WARNING BANNER === */
    .warning-banner {
        background: var(--accent-yellow);
        border: 4px solid var(--black);
        padding: 24px;
        margin: 0;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.1rem;
        text-transform: uppercase;
        box-shadow: 8px 8px 0 var(--black);
    }
    
    /* === DATA TABLE STYLING === */
    .dataframe {
        border: 3px solid var(--black) !important;
        font-family: 'Courier Prime', monospace !important;
    }
    
    .dataframe th {
        background: var(--black) !important;
        color: var(--white) !important;
        border: 2px solid var(--black) !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        border: 2px solid var(--black) !important;
        padding: 12px !important;
        font-weight: 700 !important;
    }
    
    /* === NO ANIMATIONS - INSTANT EVERYTHING === */
    * {
        transition: none !important;
        animation: none !important;
    }
    
    /* Override only for intentional interactions */
    .stButton > button,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        transition: all 0.05s linear !important;
    }
    
    /* === SCROLLBAR - INDUSTRIAL === */
    ::-webkit-scrollbar {
        width: 16px;
        height: 16px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--gray-light);
        border: 2px solid var(--black);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--black);
        border: 2px solid var(--black);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-red);
    }
    
    /* === COLUMNS STYLING === */
    [data-testid="column"] {
        padding: 0 !important;
    }
    
    [data-testid="column"] > div {
        border: 4px solid var(--black) !important;
        background: var(--white) !important;
        margin: 0 8px 0 0 !important;
        box-shadow: 6px 6px 0 var(--black) !important;
    }
    
    [data-testid="column"]:last-child > div {
        margin-right: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Brutal header
st.markdown("""
    <div style="margin: 0; padding: 0;">
        <h1>SYSTEM.CORE</h1>
        <div class="warning-banner" style="border-top: none;">
            ⚠ OPERATIONAL STATUS: ACTIVE // CLEARANCE: LEVEL-5 // UPTIME: 99.97%
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Badges
st.markdown("""
    <div style="padding: 0 40px;">
        <span class="brutal-badge">REAL-TIME</span>
        <span class="brutal-badge">ENCRYPTED</span>
        <span class="brutal-badge">NO-BS</span>
        <span class="brutal-badge">V2.0.1</span>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

# Metrics section
st.markdown("<div class='section-header'>// CRITICAL METRICS</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("ACTIVE", "1,247", "+89")

with col2:
    st.metric("THROUGHPUT", "94.2K/s", "+12.3%")

with col3:
    st.metric("LATENCY", "23ms", "-8ms")

with col4:
    st.metric("ERRORS", "0.01%", "-0.15%")

st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

# Tabs
st.markdown("<div class='section-header'>// CONTROL PANEL</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["OPERATIONS", "CONFIG", "DEPLOY"])

with tab1:
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="brutal-card">
                <h3 style="margin-bottom: 16px; padding: 0;">SYSTEM STATUS</h3>
                <p style="margin: 0; font-size: 1.1rem; line-height: 1.8;">
                ALL SYSTEMS OPERATIONAL<br>
                CPU: 34% | MEM: 2.1GB/8GB<br>
                DISK: 147GB FREE<br>
                NETWORK: 1.2GB/s IN | 890MB/s OUT<br>
                LAST DEPLOY: 2H 34M AGO
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        st.slider("LOAD THRESHOLD", 0, 100, 75)
    
    with col2:
        st.markdown("""
            <div class="brutal-card">
                <h3 style="margin-bottom: 16px; padding: 0;">SECURITY LOG</h3>
                <p style="margin: 0; font-size: 1.1rem; line-height: 1.8;">
                [14:32:11] AUTH SUCCESS - USER_047<br>
                [14:31:58] FIREWALL BLOCK - IP_192.168<br>
                [14:30:22] CERT RENEWED - DOMAIN_PROD<br>
                [14:28:45] SCAN COMPLETE - 0 THREATS<br>
                [14:27:03] BACKUP INITIATED - DB_MAIN
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        st.selectbox("SELECT MODULE", ["CORE.SYSTEM", "AUTH.SERVICE", "DATA.ENGINE", "NET.GATEWAY"])

with tab2:
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("API ENDPOINT", placeholder="https://api.system.core/v2")
        st.text_input("ACCESS TOKEN", type="password", placeholder="••••••••••••••••")
        st.text_input("NAMESPACE", placeholder="production-env")
    
    with col2:
        st.selectbox("REGION", ["US-EAST-1", "US-WEST-2", "EU-CENTRAL-1", "AP-SOUTHEAST-1"])
        st.selectbox("PROTOCOL", ["HTTPS", "WSS", "gRPC", "QUIC"])
        st.selectbox("LOG LEVEL", ["ERROR", "WARN", "INFO", "DEBUG", "TRACE"])
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    st.checkbox("ENABLE AUTO-SCALING")
    st.checkbox("ENFORCE TLS 1.3")
    st.checkbox("REAL-TIME MONITORING")
    st.checkbox("DISASTER RECOVERY MODE")
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    st.button("APPLY CONFIGURATION")

with tab3:
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="brutal-card" style="background: var(--accent-yellow);">
            <h3 style="margin-bottom: 16px; padding: 0; background: transparent; color: var(--black);">⚠ DEPLOYMENT CONTROLS</h3>
            <p style="margin: 0; font-size: 1.1rem; line-height: 1.8;">
            CURRENT BUILD: v2.0.1-stable<br>
            ENVIRONMENT: PRODUCTION<br>
            INSTANCES: 47 ACTIVE / 12 STANDBY<br>
            ROLLBACK AVAILABLE: YES<br>
            ESTIMATED DOWNTIME: 0s (ZERO-DOWNTIME)
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("BUILD VERSION", ["v2.0.1-stable", "v2.0.0", "v1.9.8", "v1.9.7-hotfix"])
        st.selectbox("DEPLOYMENT STRATEGY", ["ROLLING", "BLUE-GREEN", "CANARY", "RECREATE"])
    
    with col2:
        st.selectbox("TARGET ENV", ["PRODUCTION", "STAGING", "QA", "DEVELOPMENT"])
        st.slider("ROLLOUT SPEED (%)", 0, 100, 50)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.button("▶ INITIATE DEPLOY")
    
    with col2:
        st.button("◀ ROLLBACK")

# Footer
st.markdown("<div style='height: 48px;'></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
    <div style="padding: 32px 40px; text-align: center;">
        <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 700; letter-spacing: 2px;">
        SYSTEM.CORE // BUILD 20260130-1447 // NO WARRANTY EXPRESS OR IMPLIED
        </p>
    </div>
""", unsafe_allow_html=True)
