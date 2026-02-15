import streamlit as st
import streamlit.components.v1 as components

# Page config
st.set_page_config(
    page_title="Aurora Analytics",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom fonts and apply glassmorphism styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    
    <style>
    /* === HIDE STREAMLIT BRANDING === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* === ROOT VARIABLES === */
    :root {
        --glass-bg: rgba(255, 255, 255, 0.08);
        --glass-border: rgba(255, 255, 255, 0.18);
        --accent-purple: #C084FC;
        --accent-blue: #60A5FA;
        --accent-pink: #F472B6;
        --text-primary: #FFFFFF;
        --text-secondary: rgba(255, 255, 255, 0.7);
        --shadow-color: rgba(0, 0, 0, 0.3);
    }
    
    /* === ANIMATED BACKGROUND === */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        font-family: 'Outfit', sans-serif;
        color: var(--text-primary);
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* === FLOATING ORBS === */
    .stApp::before,
    .stApp::after {
        content: '';
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.4;
        animation: float 20s ease-in-out infinite;
        z-index: 0;
    }
    
    .stApp::before {
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, #C084FC, transparent);
        top: -200px;
        right: -200px;
        animation-delay: -5s;
    }
    
    .stApp::after {
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, #60A5FA, transparent);
        bottom: -150px;
        left: -150px;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(30px, -50px) scale(1.1); }
        66% { transform: translate(-20px, 20px) scale(0.9); }
    }
    
    /* === GLASS CONTAINERS === */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px;
        position: relative;
        z-index: 1;
    }
    
    /* Glass card styling */
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMarkdownContainer"]) {
        background: var(--glass-bg);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 8px 32px var(--shadow-color);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMarkdownContainer"]):hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        border-color: rgba(255, 255, 255, 0.3);
    }
    
    /* === TYPOGRAPHY === */
    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 3.5rem !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #C084FC 50%, #60A5FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        letter-spacing: -1px;
    }
    
    h2 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 2rem !important;
        color: var(--text-primary);
        margin-top: 0 !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 1.4rem !important;
        color: var(--text-primary);
        margin-bottom: 0.8rem !important;
    }
    
    p, label, .stMarkdown {
        color: var(--text-secondary);
        font-size: 1.05rem;
        line-height: 1.7;
    }
    
    /* === CUSTOM INPUTS === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border: 1.5px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        color: white !important;
        padding: 14px 18px !important;
        font-family: 'Outfit', sans-serif;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--accent-purple) !important;
        box-shadow: 0 0 0 3px rgba(192, 132, 252, 0.2) !important;
        background: rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Input labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem;
    }
    
    /* === CUSTOM BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
        color: white;
        border: none !important;
        border-radius: 16px;
        padding: 14px 32px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(192, 132, 252, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(192, 132, 252, 0.6);
        background: linear-gradient(135deg, #D8B4FE, #93C5FD);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* === METRICS === */
    div[data-testid="stMetricValue"] {
        font-family: 'Space Mono', monospace;
        font-size: 2.2rem !important;
        font-weight: 700;
        background: linear-gradient(135deg, #FFFFFF, var(--accent-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.95rem !important;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* === SLIDER === */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, var(--accent-purple), var(--accent-blue)) !important;
    }
    
    .stSlider > div > div > div > div {
        background-color: white !important;
        border: 3px solid var(--accent-purple);
        box-shadow: 0 0 10px rgba(192, 132, 252, 0.5);
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        padding: 8px;
        border-radius: 16px;
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue)) !important;
        color: white !important;
    }
    
    /* === CHECKBOX & RADIO === */
    .stCheckbox > label,
    .stRadio > label {
        color: var(--text-primary) !important;
        font-weight: 500;
    }
    
    /* === DIVIDER === */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        margin: 2rem 0;
    }
    
    /* === CUSTOM GLASS BADGE === */
    .glass-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: white;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    /* === CUSTOM GLASS CARD === */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    }
    
    /* === ANIMATIONS === */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .block-container > div {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--accent-purple), var(--accent-blue));
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #D8B4FE, #93C5FD);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1>✨ Aurora Analytics</h1>
        <p style="font-size: 1.2rem; margin-top: -1rem;">
            Where data meets design in perfect harmony
        </p>
        <div style="margin-top: 1rem;">
            <span class="glass-badge">Premium</span>
            <span class="glass-badge">AI-Powered</span>
            <span class="glass-badge">Real-time</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Create columns for metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Users", "24.5K", "+12.3%")

with col2:
    st.metric("Revenue", "$892K", "+8.1%")

with col3:
    st.metric("Engagement", "94.2%", "+5.4%")

with col4:
    st.metric("Conversion", "3.8%", "-0.2%")

st.markdown("---")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "⚙️ Settings", "🎨 Customize"])

with tab1:
    st.markdown("### Performance Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="glass-card">
                <h3 style="margin-top: 0;">📈 Growth Metrics</h3>
                <p>Your platform is experiencing remarkable growth across all key performance indicators. User engagement has reached an all-time high this quarter.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.slider("Time Range (days)", 7, 365, 30)
    
    with col2:
        st.markdown("""
            <div class="glass-card">
                <h3 style="margin-top: 0;">🎯 Goals Status</h3>
                <p>You're on track to meet 87% of your quarterly goals. Focus areas include user retention and feature adoption rates.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.selectbox("Select Metric", ["Revenue", "Users", "Engagement", "Conversion"])

with tab2:
    st.markdown("### Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("API Key", type="password", placeholder="Enter your API key")
        st.text_input("Organization", placeholder="Your organization name")
    
    with col2:
        st.selectbox("Region", ["US East", "US West", "EU Central", "Asia Pacific"])
        st.selectbox("Environment", ["Production", "Staging", "Development"])
    
    st.markdown("---")
    
    st.checkbox("Enable real-time notifications")
    st.checkbox("Auto-refresh dashboard")
    st.checkbox("Dark mode sync with system")
    
    st.button("💾 Save Settings")

with tab3:
    st.markdown("### Personalization")
    
    st.markdown("""
        <div class="glass-card">
            <h3 style="margin-top: 0;">🎨 Theme Customization</h3>
            <p>Customize your dashboard appearance to match your brand identity. All changes are saved automatically and sync across devices.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Accent Color", ["Purple Haze", "Ocean Blue", "Sunset Pink", "Aurora Green"])
        st.selectbox("Font Style", ["Modern (Outfit)", "Classic (Inter)", "Mono (Space Mono)"])
    
    with col2:
        st.selectbox("Animation Level", ["Full", "Reduced", "Minimal", "None"])
        st.slider("Blur Intensity", 0, 100, 80)
    
    st.button("🎯 Apply Theme")

# Footer section
st.markdown("---")
st.markdown("""
    <div class="glass-card" style="text-align: center; margin-top: 3rem;">
        <p style="margin: 0; font-size: 0.9rem;">
            Built with ✨ glassmorphism design • Powered by advanced analytics
        </p>
    </div>
""", unsafe_allow_html=True)
