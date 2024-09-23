import streamlit as st
st.set_page_config("CustomGPT Trainer", page_icon="🧿")
import home as home
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'user' not in st.session_state:
    st.session_state.user = None
if 'extract_text' not in st.session_state:
    st.session_state.extract_text = None

ADMIN_ACCESS_KEY = st.secrets.ADMIN_ACCESS_KEY
ADMIN_SECRET_KEY = st.secrets.ADMIN_SECRET_KEY


st.header(" 👨‍⚕️ :red[Healthcare]   :green[ChatGPT] Training Module", divider=True)

if st.session_state.user == None:
    with st.form("login",clear_on_submit=True):
        st.subheader("Login")
        username = st.text_input("Username : ")
        password = st.text_input("Password :", type="password")
        submit_button = st.form_submit_button("Login")
        if submit_button:
            if username == ADMIN_ACCESS_KEY and password == ADMIN_SECRET_KEY:
                st.session_state.user = True
                st.rerun()

            else:
                st.error("invalid credentials, try again!")

if st.session_state.user:
    st.subheader("let's train our chatgpt")
    
    amar = st.Page("users/amar.py",title="Amar!", icon="🧞‍♂️")
    arunav = st.Page("users/arunav.py", title="Arunav!", icon="🐼")
    dharmendra = st.Page("users/dharmendra.py", title= "Dharmendra!", icon="🦹‍♂️")
    jit = st.Page("users/jit.py", title="Jit!", icon="🐦")
    shubham = st.Page("users/shubham.py", title="Shubham M!", icon="🐯")
    varsha = st.Page("users/varsha.py", title="Varsha!", icon="🦋")
    priya = st.Page("users/priya.py",title="Priya!", icon="🐱")
    shashikant = st.Page("users/shashikant.py", title= "Shashikant!", icon="🧑‍💻")
    vivek =  st.Page("users/vivek.py", title= "Vivek!", icon="🧑‍🏫")
    test = st.Page("users/test.py", title = "Developer!", icon="🧊")
    pg = st.navigation(
        {
            
            "Users": [arunav, jit, shubham, varsha, priya, amar, dharmendra, shashikant, vivek, test],

        }
    )
    pg.run()
