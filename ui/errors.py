import streamlit as st
import traceback

def show_exception(e: Exception) -> None:
    st.error(str(e))
    st.code(traceback.format_exc())