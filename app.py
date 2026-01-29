import streamlit as st

from core.state import init_state
from core.scoring import calculate_points
from ui.layout import render_header
from ui.components import flashcard_box, controls, answer_buttons, user_stats, leaderboard

PAGE_TITLE = "🧬 DNA Study App"


from data.deck_store import (
    get_deck_names, 
    get_deck, 
    add_card,
    find_duplicate_cards,
    delete_card,
    get_all_cards_with_indices
)

from data.user_store import (
    get_user,
    create_user,
    update_user_score,
    get_leaderboard
)

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🧬",  # You can use an emoji or path to an image file
    layout="wide"  # Optional: makes the app use full width
)

render_header()

try:
    st.set_page_config(
        page_title="Debug Test",
        page_icon="🧬",
    )

    
    
    # st.title("Test 1: Streamlit works!")
    # st.write("If you see this, basic Streamlit is working.")
    
    # Test MongoDB secrets
    st.write("Test 2: Checking secrets...")
    if "mongo" in st.secrets:
        st.success("✓ MongoDB secrets found")
        st.write(f"URI starts with: {st.secrets['mongo']['uri'][:20]}...")
    else:
        st.error("✗ MongoDB secrets missing!")
    
    # Test MongoDB connection
    st.write("Test 3: Connecting to MongoDB...")
    from pymongo import MongoClient
    client = MongoClient(st.secrets["mongo"]["uri"])
    db = client[st.secrets["mongo"]["db_name"]]
    count = db.users.count_documents({})
    st.success(f"✓ MongoDB connected! Found {count} users")
    
except Exception as e:
    import traceback
    st.error("CRASH ERROR:")
    st.code(traceback.format_exc())










