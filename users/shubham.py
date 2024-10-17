import streamlit as st
st.session_state.user = "Shubham"
# st.session_state.articles = []
import home

tab1, tab2, tab3, tab4 = st.tabs(["📰 News", "🔊 myGov", "🚀federal", "🎰 OpenAI"])

with tab1:
   
   home.news_data(st.session_state.user)

with tab2:
   
    home.gov_data(st.session_state.user)

with tab3:
   
    home.fed_gov(st.session_state.user)

with tab4:
   
    home.form_data(st.session_state.user)

