import json
import logging
import os
from urllib.parse import urlparse, parse_qs
import re
import requests
import nltk
from nltk.corpus import stopwords


# Docupedia link
docupedia_link = os.getenv("DOCUPEDIA_LINK")
docupedia_id = os.getenv("DOCUPEDIA_ID")
docupedia_id_space = os.getenv("DOCUPEDIA_ID_SPACE")


#This function is used to Clean the Docupedia Content
async def clean_docupedia_content(docupedia_text):
    try:
        # Replace the content between < and > with spaces
        clean_content = re.sub(r'<[^>]*>', ' ', docupedia_text)
        clean_content = " ".join(clean_content.split())
        return clean_content
    except Exception as err:
        print(f"Error in clean docupedia content function --> {err}")
        raise RuntimeError

# async def extract_document_content(document_links):
#     print("Inside Docupedia Content Extraction Function")
#     document_links = dict(document_links)
#     return_content = {}

#     for key, value in document_links.items():
#         if (value and "docupedia" in value):
#             parsed_url = urlparse(value)
#             params = parse_qs(parsed_url.query)
#             params = dict(params)
#             print(params)
#             print(params["pageId"][0])
#             page_id = params["pageId"][0]
#             print(page_id)
#             _url = f"https://inside-docupedia.bosch.com/confluence/rest/api/content/{page_id}?expand=body.view"
#             print(_url)
#             # async with aiohttp.ClientSession() as session:
#             #     # async with session.get(f"{local_host}pragya/token", headers=headers) as response:
#             #     async with session.get(_url) as response:
#             #         response_content = await response.json()

#             response_content = requests.request("GET", _url)
#             print(response_content)
#             print(type(response_content.text))
#             print(response_content.text)

#             response_content = json.loads(response_content.text)
#             print(type(response_content))


#             print(response_content)
#             print(response_content["title"])

#             docupedia_content = await clean_docupedia_content(f'{response_content["title"]} {response_content["body"]["view"]["value"]}')

#             return_content[key] = docupedia_content
#         else:
#             return_content[key] = value
#     return return_content


# document_links = {
#     "demo_presentation_link": "https://inside-docupedia.bosch.com/confluence/pages/viewpage.action?pageId=2381510755",
#     "functional_specification_document_link": "https://inside-docupedia.bosch.com/confluence/pages/viewpage.action?pageId=508577529",
#     "requirement_document_link": "https://inside-docupedia.bosch.com/confluence/pages/viewpage.action?pageId=1930106177",
#     "technical_specification_document_link": "https://inside-docupedia.bosch.com/confluence/pages/viewpage.action?pageId=2299848552"
# }

# extract_document_content(document_links)

async def get_docupedia_content(_url):
    docupedia_content = ""
    response_content = requests.request("GET", _url)
    if response_content.status_code == 200:
        print("Docupedia content extraction api is successful")
        response_content = json.loads(response_content.text)
        docupedia_content = await clean_docupedia_content(f'{response_content["title"]} {response_content["body"]["view"]["value"]}')
        return [docupedia_content, "true"]
    else:
        print(f"Docupedia content extraction api failed ---> {response_content.status_code}")
        return [docupedia_content, "false"]
    

#This function is used to Extract the Content from Docupedia
async def extract_document(document_link):
    try:
        print("Inside Extract Document Function")
        parsed_url = urlparse(document_link)
        params = parse_qs(parsed_url.query)
        params = dict(params)
        if "pageId" in params:
            page_id = params["pageId"][0]
            _url = f"{docupedia_link}/{page_id}?expand=body.view"
            print(_url)
            return await get_docupedia_content(_url)
        else:
            print("Docupedia Page dont contain Page ID")
            try:
                _idurl = docupedia_id.format((parsed_url.path).split('/')[3],(parsed_url.path).split('/')[4])
            except:
                _idurl = docupedia_id_space.format((parsed_url.path).split('/')[3])
            _idresponse = requests.request("GET", _idurl)
            if _idresponse.status_code == 200:
                page_id = (eval(_idresponse.content))['results'][0]['id']
                _url = f"{docupedia_link}/{page_id}?expand=body.view"
                print(_url)
                return await get_docupedia_content(_url)
            else:
                print("Invalid Docupedia URL")
                return ["", "Invalid Docupedia URL"]           
    except Exception as err:
        print(f"Error in extract document function --> {err}")
        return ["", "Invalid Docupedia URL"]


async def remove_stopwords(text):
    try:
        # Select the language for stopwords
        stop_words = set(stopwords.words('english'))
        words = nltk.word_tokenize(text)  # Tokenize the text into words
        filtered_words = [word for word in words if word.lower(
        ) not in stop_words]  # Filter out stopwords
        # Join the filtered words back into a string
        return ' '.join(filtered_words)
    except Exception as err:
        print(f"Exception in stopwords function-->{err}")
        raise RuntimeError
