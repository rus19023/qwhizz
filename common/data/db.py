# db.py

from pymongo import MongoClient
import streamlit as st

# Read from Streamlit secrets
MONGO_URI = st.secrets["mongo"]["uri"]
DB_NAME = st.secrets["mongo"]["db_name"]


# Use caching to avoid reconnecting on every Streamlit rerun
@st.cache_resource
def get_database():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


db = get_database()
decks = db.decks
users = db.users
sessions = db.sessions
progress = db.progress
# Track individual study sessions for anti-cheat
study_sessions = db.study_sessions  