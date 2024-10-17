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

if 'fed_articles' not in st.session_state:
    st.session_state.fed_articles = []

if 'gov_articles' not in st.session_state:
    st.session_state.gov_articles = []

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
                    

# function to view federal register
def fed_gov(user):
    st.session_state.role = 'fed'
    # gov_articles =  []
    icon = icon_dict.get(user)
    st.info(f"Hello, {user}!", icon=icon)
    with st.form(key='api_form'):
        st.markdown("#### 🔍 **Search Parameters**")
        

        include_term = st.checkbox("Include Search Term 📝")
        term = st.text_input("Search Term", value=" ")
        # with st.expander():

        include_section = st.checkbox("Include Section 🏛️")
        # if include_section:
        section = st.selectbox("Section", ["--","Health-and-public-welfare","business-and-industry","environment","money","science-and-technology","world"])


        include_cfr_title = st.checkbox("Include CFR Title 📖")
        # if include_cfr_title:
        cfr_title = st.number_input("CFR Title", min = 1, max = 50, steps = 1)

        # include_cfr_part = st.checkbox("Include CFR Part 📃")
        # if include_cfr_part:
        #     cfr_part = st.number_input("CFR Part")

    
        include_dates = st.checkbox("Include Publication Date Range 📅")
        # if include_dates:
        start_date = st.date_input("Start Publication Date")
        end_date = st.date_input("End Publication Date")

        include_effective_dates = st.checkbox("Include On and after effective Date 📅")
        # if include_effective_dates:
        effective_start_date = st.date_input("Start effective Date")

        

        per_page = st.number_input("Results per Page 📄",value=1000)

        submit_button = st.form_submit_button(label="🚀 Submit Search")


    if submit_button:
        
        api_url = "https://www.federalregister.gov/api/v1/documents.json"

        params = {
            "per_page": per_page,
            "order": "newest"
        }

        # Include each parameter only if the corresponding checkbox is selected
        if include_term:
            params["conditions[term]"] = term

        if include_section:
            params["conditions[sections][]"] = section

        if include_cfr_title:
            params["conditions[cfr][title]"] = cfr_title

        if include_cfr_part:
            params["conditions[cfr][part]"] = cfr_part

        if include_dates:
            params["conditions[publication_date][gte]"] = start_date
            params["conditions[publication_date][lte]"] = end_date
        
        if include_effective_dates:
            params["conditions[effective_date][gte]"] = effective_start_date
            

        # Fetch results from the API
        response = requests.get(api_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            st.session_state.fed_articles  = response.json()

            if 'results' in st.session_state.fed_articles:
                st.markdown(f"<h3 style='color: #4CAF50;'>Found {len(st.session_state.fed_articles['results'])} Results</h3>", unsafe_allow_html=True)

                # Display each result in a styled container
                for document in st.session_state.fed_articles['results']:
                    st.markdown("<div style='border: 2px solid #4CAF50; padding: 10px; margin: 10px 0; border-radius: 5px;'>", unsafe_allow_html=True)
                    st.markdown(f"**Title:** {document.get('title', 'N/A')}")
                    st.markdown(f"**Publication Date:** {document.get('publication_date', 'N/A')}")
                    st.markdown(f"**abstract:** {document.get('abstract', 'N/A')}")
                    st.markdown(f"**Details URL:** [Link]({document.get('html_url', 'N/A')})")
                    st.markdown(f"**PDF URL:** [Link]({document.get('pdf_url','N/A')})")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No 'results' key found in the response.")
        else:
            st.error(f"Failed to fetch data. Status Code: {response.status_code}")
            st.write("Error response:", response.text)



# function to view myGov 

def gov_data(user):
    try:
        st.session_state.role = 'gov'
        gov_articles =  []
        icon = icon_dict.get(user)
        st.info(f"Hello, {user}!", icon=icon)
        on = st.toggle("search by query")
        
        api_key = st.secrets.api_key
        # API endpoint
        url = "https://api.govinfo.gov/search"
        
        # Headers for the POST request
        headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key
        }
        if on:
            with st.form("gov", clear_on_submit=False):
                search  =  st.text_input(label="Query:", placeholder="enter you text here")    
                pageSize = st.number_input(label="Page Size:", placeholder="articles count in single page", min_value=10, max_value=100, value="min", step=10)
                if st.form_submit_button(label="Search"):
            
                    # Body data for the request
                    body = {
                    "query": search,
                    "pageSize": pageSize,
                    "offsetMark": "*",
                    "sorts": [
                        {
                            "field": "relevancy",
                            "sortOrder": "ASC"
                        }
                    ],
                    "historical": True,
                    "resultLevel": "default"
                    }
                    # Sending POST request
                    response = requests.post(url, headers=headers, json=body)
        
                    # Print the response
                    if response.status_code == 200:
                        st.session_state.gov_articles = response.json()
                        st.success(f"related documents found:{st.session_state.gov_articles["count"]}")
        
                    else:
                        st.error(f"Error: {response.status_code}")
            if st.session_state.gov_articles:
                # Display each result in the JSON response
                for result in st.session_state.gov_articles['results']:
                    st.subheader(result['title'])
                    # st.write(f"Package ID: {result['packageId']}")
                    # st.write(f"Granule ID: {result['granuleId']}")
                    st.write(f"Last Modified: {result['lastModified']}")
                    st.write(f"Date Issued: {result['dateIssued']}")
                    st.write(f"Collection Code: {result['collectionCode']}")
                    
                    # Display government authors
                    st.write("Government Authors:")
                    for author in result['governmentAuthor']:
                        st.write(f"- {author}")
                   
                    # Display download links
                    url_pdf = f"{result['download']['pdfLink']}?api_key={api_key}"
                    st.page_link(url_pdf, label="PDF", icon="🌎")
                    
        
                    # Divider for clarity between results
                    st.markdown("---")



        else:
                    with st.form("doc_gov", clear_on_submit=False):
                        options=["BILLS", "BILLSTATUS", "BUDGET", "CCAL", "CDIR", "CDOC", "CFR", "CHRG", "CMR", "COMPS",
                                "CPD", "CPRT", "CREC", "CRECB", "CRI", "CRPT", "CZIC", "ECFR", "ECONI", "ERIC","ERP",
                                "FR", "GAOREPORTS", "GOVMAN", "GOVPUB", "GPO", "HJOURNAL", "HMAN", "HOB", "LSA", "PAI",
                                "PLAW", "PPP", "SERIALSET", "SJOURNAL", "SMAN", "STATUTE", "USCODE", "USCOURTS" ] 
                        collection = st.selectbox(label="collection code:", options=options)
                        date = st.date_input("last modified date:")
                        mod_date = f"{date}T00%3A00%3A00Z"
                        # st.write(mod_date)
                        pageSize = st.number_input(label="Page Size:", placeholder="articles count in single page", min_value=10, max_value=100, value="min", step=10)
            
                        if st.form_submit_button(label="Search"):
                            base_url = f"https://api.govinfo.gov/collections/{collection}/{mod_date}?pageSize={pageSize}&offsetMark=%2A&api_key=hjacpL8PngljgbCwwPTrr7xG4KSGfdkbr5RWHgho"
                            
                            response = requests.get(base_url)
                            if response.status_code == 200:
                                st.session_state.gov_articles = response.json()
                                # st.write(st.session_state.gov_articles)
                                st.success(f"published collections found:{st.session_state.gov_articles["count"]}")
                            else:
                                st.error("response failure")
                                # st.success(f"published collections found:{st.session_state.gov_articles["count"]}")
                                # Display the results in the Streamlit app
                    if st.session_state.gov_articles:
                        i = 0
                        for package in st.session_state.gov_articles['packages']:
                            
                            st.subheader(f"{i+1} : {package['title']}")
                            st.write(f"Package ID: {package['packageId']}")
                            st.write(f"Last Modified: {package['lastModified']}")
                            url_summary = package['packageLink']
                            url = url_summary.replace("summary", "pdf")
                            url_pdf = f"{url}?api_key={api_key}"
                            st.page_link(url_pdf, label="PDF", icon="🌎")
                            i+=1
                            st.markdown("---")
            
                    else:
                        st.write("No data available.")
            
    except:
        st.error("error detected, no data found")
        st.session_state.gov_articles = []
        
        

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
