import streamlit as st

try:
    st.set_page_config(
        page_title="Debug Test",
        page_icon="🧬",
    )
    
    st.title("Test 1: Streamlit works!")
    st.write("If you see this, basic Streamlit is working.")
    
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