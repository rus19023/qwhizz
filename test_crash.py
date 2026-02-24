import streamlit as st
st.title("Test App")
choice = st.selectbox("Pick one", ["A", "B", "C"])
st.write(f"You chose {choice}")
