import streamlit as st
import pymongo
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from docx import Document
import io
from PIL import Image
import pytesseract
import boto3
# import openai
from openai import OpenAI, AsyncOpenAI
from newsapi import NewsApiClient
import requests
# from openai.error import OpenAIError

aws_access_key_id = st.secrets.aws_access_key_id
aws_secret_access_key = st.secrets.aws_secret_access_key
db_username = st.secrets.db_username
db_password = st.secrets.db_password


if 'articles' not in st.session_state:
    st.session_state.articles = []
    
if 'page' not in st.session_state:    
    st.session_state.page  = None
if 'role' not in st.session_state:
    st.session_state.role = None


# mongo connection
mongo_uri_template = "mongodb+srv://{username}:{password}@cluster0.thbmwqi.mongodb.net/"
mongo_uri = mongo_uri_template.format(username=db_username, password=db_password)
client = pymongo.MongoClient(mongo_uri)

db = client["customgpt"]
collection = db["data"]
# Init

# s3 storage
s3_client = boto3.client(
    service_name = "s3",
    region_name = 'us-east-1',
    aws_access_key_id = aws_access_key_id,
    aws_secret_access_key = aws_secret_access_key

)

icon_dict = {"Arunav":"🐼",
                    "Jit":"🐦",
                    "Shubham":"🐯",
                    "Priya":"🐱",
                    "Amar":"🧞‍♂️",
                    "Varsha":"🦋",
                    "Dharmendra":"🦹‍♂️",
                    "Vivek":"🧑‍🏫",
                    "Shashikant":"🧑‍💻",
                    "Developer":"🧊"}
                    
#function to view news

def news_data(user):
    # st.write(st.session_state.article)
    st.session_state.role = 'news'
    articles =  []
    icon = icon_dict.get(user)
    st.info(f"Hello, {user}!", icon=icon)
    
    
    on = st.sidebar.toggle("View headlines")
    

              
    
        
    if on:
            with st.sidebar.form(f"{user} search headlines", clear_on_submit=False):
                search_text = st.text_input('search text:', placeholder= 'enter your text to search')
                submit_button = st.form_submit_button(label='Search')
                if submit_button:
                    # st.session_state.article = True
                    # /v2/top-headlines
                    # top_headlines = newsapi.get_top_headlines(q=search_text,
                    #                     #   sources='bbc-news,the-verge',
                    #                       category='health',
                    #                       language='en',
                    #                       country='us')
                    # st.session_state.article = top_headlines
                    # st.text_area(label="articles", placeholder=top_headlines)
            
                    #  https://newsapi.org/v2/top-headlines?q=hipaa&country=us&category=health&apiKey=7f4969be87b541b887aa3c6a22176126   
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {
                        'q' : search_text,
                        'country' : 'us',
                        'category' : 'health',
                        'apiKey' : '7f4969be87b541b887aa3c6a22176126'
                    }
                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                                # Parse the response to JSON
                                data = response.json()
                                
                                # Extract the articles
                                st.session_state.articles = data.get("articles", [])
                                # st.session_state.article = articles
                                # st.text_area(label="articles", placeholder=st.session_state.article)
                    else:
                                st.write(f"Failed to fetch articles. Status code: {response.status_code}")
    else:
        
            with st.sidebar.form(f"{user} search everything",clear_on_submit=False):
                search_text = st.text_input('search text:', placeholder='enter your text to search')
                from_date = st.date_input("date from")
                search_in = st.multiselect("searching are", options=["title", "description", "content"],default='content',placeholder="The fields to restrict your search to option")
                
                sort_by = st.radio(label="sort the articles", options=["relevancy", "popularity", "publishedAt"],
                                captions=[
                                            "articles more closely related to search text come first.",
                                            "articles from popular sources and publishers come first.",
                                            " newest articles come first.",
                                        ],index=None,horizontal=False)
                submit_button = st.form_submit_button(label='Search')

                if submit_button:
                    
                    comma_separated_string = ",".join(search_in)
                    # st.write(comma_separated_string)
                    # /v2/everything
                    # all_articles = newsapi.get_everything(q=search_text,
                    #                                     # searchIn = comma_separated_string,
                    #                                     from_param=from_date,
                    #                                     language='en',
                    #                                     sort_by=sort_by,
                    #                                     )
                    # Define the API URL and parameters
                    url = "https://newsapi.org/v2/everything"
                    params = {
                        "q": search_text,
                        "from": from_date,
                        # "to": "2024-09-11",
                        "searchIn": comma_separated_string,
                        "sortBy": sort_by,
                        "language": "en",
                        "apiKey": "7f4969be87b541b887aa3c6a22176126"
                    }

                    # Streamlit title
                    # st.title("HIPAA News Search")

                    # Send the request
                    response = requests.get(url, params=params)

                    # Check if the response is valid
                    if response.status_code == 200:
                        # Parse the response to JSON
                        data = response.json()
                        
                        # Extract the articles
                        st.session_state.articles = data.get("articles", [])
                        # st.session_state.article = articles
                    else:
                        st.write(f"Failed to fetch articles. Status code: {response.status_code}")
                        
                    # Display articles
            
        # Pagination Logic
    if st.session_state.articles:
             
            
           
            st.success(f"Found - {len(st.session_state.articles)} articles")

            # Number of articles per page
            articles_per_page = 10

            # Calculate total number of pages
            total_pages = (len(st.session_state.articles) - 1) // articles_per_page + 1

            # Create pagination buttons
            st.session_state.page = st.number_input("Page", min_value=1, max_value=total_pages, step=1)
            # st.session_state.page  = page_number

            # Calculate start and end indices for the current page
            start_idx = (st.session_state.page - 1) * articles_per_page
            # end_idx = start_idx + articles_per_page if len(st.session_state.article) > articles_per_page else len(st.session_state.article)
            end_idx = min(start_idx + articles_per_page, len(st.session_state.articles))
            # st.write(start_idx,end_idx,total_pages)
            # Display articles for the current page
            for i, article in enumerate(st.session_state.articles[start_idx:end_idx], start=start_idx+1):
                st.subheader(f"{i}. {article['title']}")
                st.write(article["description"])
                st.write(f"[Read more]({article['url']})")
                st.write("---")

            # Display page navigation
            st.write(f"Page {st.session_state.page} of {total_pages}")
    else:
            # if submit_button:
                st.write("No articles found for the given query.")
    # st.write(st.session_state.article)
                # st.session_state.article = None

# function to take form details
def form_data(user):
        uploaded_file = None
        # text = None
        # on = st.toggle("Activate text feature")
        option_dict = {"Arunav":["Community Source", "Government Source", "Organisations", "Others"], 
            "Jit":["Google Trends", "Instagram", "Facebook", "Twitter", "Others"],
            "Shubham":["You Tube", "Community Source", "Government Source", "Organisations", "Others"],
            "Priya":["Others"], 
            "Amar":["Competitors Source", "Inhouse Source", "Others"], 
            "Varsha":["You Tube","Competitors Source", "Inhouse Source", "Others"], 
            "Dharmendra":["Community Source", "Government Source", "Organisations","Google Trends", "Instagram", "Facebook", "Twitter",
                        "You Tube", "Competitors Source", "Inhouse Source","Linkedin", "Others"],
            "Vivek":["Linkedin", "Others" ],
            "Shashikant":["Others"],
            "Developer":["Community Source", "Government Source", "Organisations","Google Trends", "Instagram", "Facebook", "Twitter",
                        "You Tube", "Competitors Source", "Inhouse Source","Linkedin", "Others"],}

        doc_count = len(list(collection.find({"user":user})))
        with st.form(f"{user}", clear_on_submit=True):
        
            icon = icon_dict.get(user)
            st.info(f"Hello, {user}! - Documents:{doc_count}", icon=icon)
            

            # st.info(f"Hello, {user}!")
            options = sorted(option_dict.get(user))
            document = st.text_input('Ref doc :', placeholder='enter your reference doc name')
            platform = st.selectbox("Ref platform :", options = options)
            link = st.text_area("Ref url :", placeholder="paste your  reference url")
            # if on:
            #     text_area = st.text_area("Content :", placeholder="paste your content here", height = 500)
            #     text = text_area
            #     # st.write(on)
                
            # else:
                # file_type = st.radio(label="file type: ", options=[".pdf", ".txt", ".docx", ".csv", ".xlsx"], index=0,)
            uploaded_file = st.file_uploader("upload .txt file:", type="txt")
                
                


            submit_button = st.form_submit_button(label='Submit')
            if submit_button:
                #create functions for different type of file_type
                if uploaded_file is not None:
                    try:
                        filename = document
                        bucket_name = "vedsubrandwebsite"
                        object_key = filename
                        s3_url = f"https://{bucket_name}.s3.amazonaws.com/customgpt/{platform}/{object_key}.txt"
                        # st.session_state[f'player_{st.session_state.current_player}_photo'] = s3_url
                        
                        s3_client.put_object(
                        Body=uploaded_file, 
                        Bucket=bucket_name, 
                        Key=f'customgpt/{platform}/{object_key}.txt'
                        )

                    except Exception as e:
                        s3_url = f"{str(e)}"
           
                    """ 
                    1. store name, url, comment and date in variable
                    2. store pdf in s3 and fetch its url
                    3. process pdf and get text info
                    4. give prompts to process that text
                    5. store text in s3 and fetch its url
                    6. store variables and urls in mongo db
                    """
                    document = {"user":user, "url": s3_url, "platform":platform, "document":document, "source":link}
                    
                    try:
                        collection.insert_one(document)
                        st.success("upload successfull")
                        st.rerun()
                    except Exception as e:
                        st.error(f"upload failed: {str(e)}")
