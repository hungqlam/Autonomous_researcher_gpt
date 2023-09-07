import os
from dotenv import find_dotenv, load_dotenv
import requests
import json
import pandas as pd
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
    #print("Search result: ", response_data)
    return response_data

def convertjson_csv(response_data):
    df= pd.DataFrame(response_data['organic'])
    df.drop(columns=['imageUrl','position'], inplace=True)
    return df


def find_best_article_urls(response_data,query):
    #turn json into string

    response_str =json.dumps(response_data)

    #create llm to choose best articles
    llm = OpenAI(model_name='gpt-3.5-turbo',temperature=0)
    template ="""
    You are the  top class journalist and researcher, you are extremely good at find most relevant article to certain topic;
    {response_str}
    Above is the list of search results for the query {query}.
    Please choose the 10 best articles from the list, return ONLY an array of the urls, do not include anything else; return ONLY an array of the urls, do not include anything else
        
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




query="Paypal stable coin"

result = search(query)

articles = find_best_article_urls(result, query)

print(articles)


