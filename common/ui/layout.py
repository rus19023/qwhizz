# ui/layout.py
import streamlit as st


def render_header():
    st.title(st.secrets['app']['title'])
    st.write(st.secrets['app']['subtitle'])

    
