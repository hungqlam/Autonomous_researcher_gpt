import os
from dotenv import find_dotenv, load_dotenv
import requests
import json
from langchain import OpenAI, LLMChain, PromptTemplate
import openai
from langchain.document_loaders import UnstructuredURLLoader
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
load_dotenv(find_dotenv())
SERPAPI_API_KEY=os.getenv("SERPAPI_API_KEY")
openai.api_key=os.getenv("OPENAI_API_KEY")
#1. serp request to get list of relevant articles

def search(query):
    url = "https://google.serper.dev/search"

    payload = json.dumps(
        {
            "q" :query

        }
    )
    headers ={
        'X-API-KEY':SERPAPI_API_KEY,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST",url,headers=headers, data=payload)
    response_data = response.json()
    print("Search result: ", response_data)
    return response_data





def find_best_article_urls(response_data,query):
    #turn json into string

    response_str =json.dumps(response_data)

    #create llm to choose best articles
    llm = OpenAI(model_name='gpt-3.5-turbo',temperature=0)
    template ="""
    You are the  top class journalist and researcher, you are extremely good at find most relevant article to certain topic;
    {response_str}
    Above is the list of search results for the query {query}.
    Please choose the 3 best articles from the list, return ONLY an array of the urls, do not include anything else; return ONLY an array of the urls, do not include anything else
    
    """
    promt_template=PromptTemplate(
        input_variables=["response_str","query"], template=template
    )
    article_picker_chain = LLMChain(
        llm=llm, prompt=promt_template,verbose=True
    )
    urls = article_picker_chain.predict(response_str=response_str,query=query)

    #convert string to list
    url_list = json.loads(urls)
    return url_list


def get_content_from_urls(urls):
    data = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the HTTP status code indicates an error
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()  # Extract the plain text content
            data.append(text_content)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
    return data

def summarise(data, query):
    text_splitter=CharacterTextSplitter(separator="\n", chunk_size = 3000, chunk_overlap=200, length_function = len)
    text=text_splitter.split_documents(data)
    llm = OpenAI(model_name='gpt-3.5-turbo',temperature=0)
    template="""
    {text}
    You are a world class journalist and you will try to summarize the text above in order to create a twitter thread about {query}
    Please follow all of the following rules:
    1/ Make sure the content is engaging, informative with good data
    2/ Make sure the content is not too long, it should be no more than 3-5 tweets
    3/ The content should address the {query} topic very well
    4/ The content needs to be viral, and get at least 1000 likes
    5/ The content nees to be written in a way that is easy to read and understand
    6/ The content needs to give audience actionable & insights too
    
    SUMMARY:
    """
    promt_template=PromptTemplate(
    input_variables=["response_str","query"], template=template
    )

    summariser_chain = LLMChain(llm=llm, prompt=promt_template,verbose=True)
    summaries=[]
    for chunk in text:
        summary = summariser_chain.predict(text=chunk, query=query)
        summaries.append(summary)

    print(summary)
    return summaries

def save_to_pdf(data, filename='output.pdf',pagesize=(612, 792)):
    c = canvas.Canvas(filename, pagesize=pagesize)
    width, height = letter

    # Set font and size
    c.setFont("Helvetica", 12)

    # Define the line height and starting position
    line_height = 14
    y_position = height - 50

    # Iterate through the data and write it to the PDF
    for text_content in data:
        lines = text_content.split('\n')
        for line in lines:
            # If the line is too close to the bottom, create a new page
            if y_position < 50:
                c.showPage()
                y_position = height - 50

            c.drawString(50, y_position, line)
            y_position -= line_height

    c.save()




query="BTC etf approve"

result = search(query)
urls = find_best_article_urls(result,query)
#data= get_content_from_urls(urls)
#summaries = summarise(data,query)
print(urls)
