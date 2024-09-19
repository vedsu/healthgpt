import streamlit as st
st.session_state.user = "Varsha"
import home


home.form_data(st.session_state.user)