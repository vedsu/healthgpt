import streamlit as st
st.session_state.user = "Developer"
st.session_state.article = None
import home



tab1, tab2 = st.tabs(["📈 News", "🗃 OpenAI"])

with tab1:
   home.news_data(st.session_state.user)

with tab2:
    home.form_data(st.session_state.user)
