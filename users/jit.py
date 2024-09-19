import streamlit as st
st.session_state.user = "Jit"
import home


home.form_data(st.session_state.user)