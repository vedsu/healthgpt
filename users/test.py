import streamlit as st
st.session_state.user = "Developer"
# st.session_state.articles = []
import home



tab1, tab2, tab3 = st.tabs(["📰 News", "🔊 myGov", "🎰 OpenAI"])

with tab1:
   home.news_data(st.session_state.user)

with tab2:
    home.gov_data(st.session_state.user)

with tab3:
    home.form_data(st.session_state.user)
