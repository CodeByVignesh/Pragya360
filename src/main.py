import requests
from lib.sharepoint_process import create_bearer_token, _sharepoint_search
from lib.api_auth import authenticate_user, get_current_active_user
from lib.create_query import create_search_query, create_update_query
from lib.create_token import create_access_token
from lib.db_connection import initialize_elastic, mongo_connect
from lib.document_content_extraction import extract_document
from lib.duplicate_nugget import clean_nuggets, find_duplicate_nugget, get_dynamic_tags, get_nugget_id, process_search_result, update_parent_nugget
from lib.feedback import delete_likes_dislikes, store_likes_dislikes
from model.model import duplicate_nugget_model, nugget_model, search_data, sharepoint_search_model, comment_model, Token
import nltk
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('stopwords')

import aiohttp
import uvicorn
import json
import os
import logging
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
from urllib.error import ContentTooShortError, HTTPError
from fastapi import FastAPI, Request, Response, status

load_dotenv()

token_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
index = os.getenv("INDEX_NAME")

db = os.getenv("users_db")
db = json.loads(db)

# local host ip
local_host = os.getenv("LOCAL_HOST_IP")

# local host port
local_host_port = os.getenv("LOCAL_HOST_PORT")

# testing sever ip
testing_server_ip = os.getenv("TESTING_SERVER_IP")

# testing server host
testing_server_host = os.getenv("TESTING_SERVER_PORT")

# Set up the logging configuration
# log_file_name = '-'
# logging.basicConfig(filename=log_file_name, level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Pragya 360", description="Pragya 360 API")

#PRAGYA_TOKEN_URL = f"{local_host}pragya/token"
PRAGYA_TOKEN_URL = f"{testing_server_ip}pragya/token"


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # start_time = time.time()
    response = await call_next(request)
    # process_time = time.time() - start_time
    # response.headers["X-Process-Time"] = process_time
    return response


@app.get("/pragya/token", response_model=Token)
async def token_creation(request: Request):

    try:
        print("Inside token creation api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")

        try:
            user = authenticate_user(db, client_id, client_secret)
            print("Returned User")
            if not user:
                resp = Response(json.dumps(
                    {"message": "Invalid client or secret ID", "type": "Error"}))
                resp.headers['Content-Type'] = 'application/json'
                resp.status_code = 401
                print(
                    {"message": "Invalid client or secret ID", "type": "Error"})
        except Exception as err:
            print(f"Error in authenticate user function --> {err}")
            raise RuntimeError

        access_token_expires = timedelta(minutes=int(token_expire))
        try:
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            return {
                "status": "success",
                "access_token": access_token,
                "token_type": "bearer"
            }
        except Exception as err:
            print(f"Error in create access token function --> {err}")
            raise RuntimeError
    except Exception as err:
        print("Error in pragya token creation api")
        raise HTTPError


@app.post("/create-nugget", status_code=status.HTTP_201_CREATED)
async def create_nugget(request: Request, input_data: nugget_model, return_response: Response):

    try:
        print("Inside create nugget api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        req_body = dict(input_data)
        req_body_mongo = dict(input_data)

        print(f"Request Body ---->\n{req_body}")

        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }

        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError

        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            print("token verified successfully")
            try:
                # initializing elastic
                es = await initialize_elastic()
            except Exception as err:
                raise RuntimeError

            # create dynamic tags based on descriptive content in nugget
            _dynamic_tags = await get_dynamic_tags(req_body)

            # document_links = {
            #     "demo_presentation_document_link": req_body["demo_presentation_link"],
            #     "functional_specification_document_link": req_body["functional_specification_document_link"],
            #     "requirement_document_link": req_body["requirement_document_link"],
            #     "technical_specification_document_link": req_body["technical_specification_document_link"]
            # }

            # document_content = await extract_document_content(document_links)

            # # print(document_content)

            # req_body["demo_presentation_document_content"] = document_content["demo_presentation_document_link"]
            # req_body["functional_specification_document_content"] = document_content["functional_specification_document_link"]
            # req_body["requirement_document_content"] = document_content["requirement_document_link"]
            # req_body["technical_specification_document_content"] = document_content["technical_specification_document_link"]

            # docupedia link status
            docupedia_status = dict()
            docupedia_status["docupedia_links"] = []
            no_link_status = "No Link or Invalid Link"

            req_body["demo_presentation_document_content"] = ""
            req_body["functional_specification_document_content"] = ""
            req_body["requirement_document_content"] = ""
            req_body["technical_specification_document_content"] = ""

            # DEMO PRESENTATION LINK
            if (req_body["demo_presentation_link"] and "docupedia" in req_body["demo_presentation_link"]):
                extract_document_response = await extract_document(req_body["demo_presentation_link"])
                req_body["demo_presentation_document_content"] = extract_document_response[0]
                if(extract_document_response[1] != "true"):
                    _link_status = {
                        "demo_presentation_link": req_body["demo_presentation_link"],
                        "status": extract_document_response[1]
                    }
                    docupedia_status["docupedia_links"].append(_link_status)
            else:
                _link_status = {
                    "demo_presentation_link": req_body["demo_presentation_link"],
                    "status": no_link_status
                }
                docupedia_status["docupedia_links"].append(_link_status)

            # FUNCTIONAL SPECIFICATION DOCUMENT LINK
            if (req_body["functional_specification_document_link"] and "docupedia" in req_body["functional_specification_document_link"]):
                extract_document_response = await extract_document(req_body["functional_specification_document_link"])
                req_body["functional_specification_document_content"] = extract_document_response[0]
                if(extract_document_response[1] != "true"):
                    _link_status = {
                        "functional_specification_document_link": req_body["functional_specification_document_link"],
                        "status": extract_document_response[1]
                    }
                    docupedia_status["docupedia_links"].append(_link_status)
            else:
                _link_status = {
                    "functional_specification_document_link": req_body["functional_specification_document_link"],
                    "status": no_link_status
                }
                docupedia_status["docupedia_links"].append(_link_status)

            # REQUIREMENT DOCUMENT LINK
            if (req_body["requirement_document_link"] and "docupedia" in req_body["requirement_document_link"]):
                extract_document_response = await extract_document(req_body["requirement_document_link"])
                req_body["requirement_document_content"] = extract_document_response[0]
                if(extract_document_response[1] != "true"):
                    _link_status = {
                        "requirement_document_link": req_body["requirement_document_link"],
                        "status": extract_document_response[1]
                    }
                    docupedia_status["docupedia_links"].append(_link_status)
            else:
                _link_status = {
                    "requirement_document_link": req_body["requirement_document_link"],
                    "status": no_link_status
                }
                docupedia_status["docupedia_links"].append(_link_status)

            # TECHNICAL SPECIFICATION DOCUMENT LINK
            if (req_body["technical_specification_document_link"] and "docupedia" in req_body["technical_specification_document_link"]):
                extract_document_response = await extract_document(req_body["technical_specification_document_link"])
                req_body["technical_specification_document_content"] = extract_document_response[0]
                if(extract_document_response[1] != "true"):
                    _link_status = {
                        "technical_specification_document_link": req_body["technical_specification_document_link"],
                        "status": extract_document_response[1]
                    }
                    docupedia_status["docupedia_links"].append(_link_status)
            else:
                _link_status = {
                    "technical_specification_document_link": req_body["technical_specification_document_link"],
                    "status": no_link_status
                }
                docupedia_status["docupedia_links"].append(_link_status)

            req_body["created_date"] = datetime.now().strftime('%Y-%m-%d')
            req_body["views"] = 0
            req_body["likes"] = 0
            req_body["dislikes"] = 0
            req_body["comment"] = []
            req_body["available_for_search"] = "true"
            req_body["dynamic_tags"] = _dynamic_tags
            
            if(req_body['system_demo'] != ''):
                req_body["system_demo_str"] = f"with system demo yes {req_body['system_demo']}"
            else:
                req_body['system_demo'] = 'No'
                req_body["system_demo_str"] = 'with system demo no'
                
            req_body["collection_str"] = f'with collection {req_body["collection"]}'
            req_body["knowledge_source_str"] = f'with knowledge source {req_body["knowledge_source"]}'
            req_body["technology_str"] = f'with technology {" ".join(req_body["technology"])}'
            
            if(req_body["development_scope"] != "No"):
                req_body["development_scope_str"] = f'with development scope {req_body["development_scope"]}'
            else:
                req_body["development_scope_str"] = ''
                
            req_body["lob_str"] = f'with lob {" ".join(req_body["lob"])}'
            req_body["artifact_tag_str"] = f'with artifact tags {" ".join(req_body["artifact_tag"])}'
            
            if(len(req_body["features_enabled"]) ==1 and req_body["features_enabled"][0] == ''):
                req_body["features_enabled_str"] = ''
            else:
                req_body["features_enabled_str"] = f'with features enabled {" ".join(req_body["features_enabled"])}'

            print(f"Updated Request Body ---->\n{req_body}")

            if (req_body["parent_nugget"] and int(req_body["version"]) > 1):
                await update_parent_nugget(index, req_body["parent_nugget"])

            # insert the data into elastic search
            create_nugget = es.index(index=index, body=req_body)
            print("Nugget is created")
            print(create_nugget)
            print(f"Nugget ID ----> {create_nugget['_id']}")

            # insert data in mongodb for finding duplicate nuggets
            try:
                # initializing mongo
                nugget_string_ = await clean_nuggets(req_body_mongo)
                nugget_string_["nugget_id"] = create_nugget['_id']
                db = await mongo_connect()
                collection = db['string_data']
                result = collection.insert_one(nugget_string_)
                print(
                    f"Joined string inserted into Mongo DB -- > {result.inserted_id}")
            except Exception as err:
                raise RuntimeError
            
            # insert data in mongodb for docupedia content
            try:
                # initializing mongo
                docupedia_status["nugget_id"] = create_nugget['_id']
                db = await mongo_connect()
                collection = db['docupedia_status']
                result = collection.insert_one(docupedia_status)
                print(
                    f"Docupedia Status inserted into Mongo DB -- > {result.inserted_id}")
            except Exception as err:
                raise RuntimeError

            return_response.status_code = 201
            return_data = {
                "status": "success",
                "result": create_nugget["result"],
                "nugget_id": create_nugget["_id"]
            }
            print(return_data)
            print([return_response])
            return return_data
    except Exception as err:
        print(f"Exception in creating nuggets --> {err}")
        return_response.status_code = 400
        return_data = {
            "status": "failure",
            "result": "Error in Creating Nugget"
        }
        print(f"{return_data}")
        return return_data


@app.post("/search-nugget")
async def search_nuggets(request: Request, input_data: search_data, user: str, return_response: Response):

    try:
        user = user.upper()
        print("Inside search nugget api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        req_body = dict(input_data)
        print(req_body)

        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }

        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError

        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            print("token verified successfully")
            try:
                # initializing elastic
                es = await initialize_elastic()
            except Exception as err:
                raise ContentTooShortError

            # search the data in elastic search
            search_query_data = await create_search_query(req_body)

            search_string = search_query_data[0]
            query = search_query_data[1]

            resp = es.search(index=index, body=query)
            print("Nugget search is done")
            # print(resp)

            # reconstruct the response
            resp = resp["hits"]["hits"]
            all_tags = []
            features_enabled_list = []
            _result_list = []
            print(f"Elastic Search Response -->\n{resp}")
            if (resp):
                for item in resp:
                    item["_source"]["nugget_access_to"] = [value.upper() for value in item["_source"]["nugget_access_to"]]
                    if (item["_source"]["is_restricted_nugget"].upper() == "FALSE") or (item["_source"]["is_restricted_nugget"].upper() == "TRUE" and user in item["_source"]["nugget_access_to"]):
                        all_tags += item["_source"]["artifact_tag"]
                        if(item["_source"]["features_enabled"][0] != ""):
                            features_enabled_list += item["_source"]["features_enabled"]
                        _result_list.append(await process_search_result(search_string, item))
                print(f"Result List -->\n{_result_list}")
                if(_result_list):
                    return_response.status_code = 200
                    return_data = {
                        "status": "success",
                        "message": "search completed",
                        "total_tags": len(sorted(list(set(all_tags)))),
                        "tags": sorted(list(set(all_tags))),
                        "features_enabled_count": len(sorted(list(set(features_enabled_list)))),
                        "features_enabled_list": sorted(list(set(features_enabled_list))),
                        "total_result": len(_result_list),
                        "result": _result_list
                    }

                    # insert data in mongodb for finding duplicate nuggets
                    try:
                        # initializing mongo
                        search_log = {
                            "status": "success",
                            "message": "search completed",
                            "search_time": datetime.now(),
                            "search_user": user,
                            "search_query": req_body,
                            "search_result": resp

                        }
                        db = await mongo_connect()
                        _collection_name = f"search_logs_{datetime.now().strftime('%Y-%m-%d')}"
                        collection = db[_collection_name]
                        result = collection.insert_one(search_log)
                        print(
                            f"Search Logs inserted into Mongo DB -- > {result.inserted_id}")
                    except Exception as err:
                        raise RuntimeError
                else:
                    return_response.status_code = 200
                    return_data = {
                        "status": "failed",
                        "message": "Oops!!! your search did not match any document. Try different keywords with less or no filter."
                    }
                    # insert data in mongodb for finding duplicate nuggets
                    try:
                        # initializing mongo
                        search_log = {
                        "status": "failure",
                        "message": "Oops!!! your search did not match any document. Try different keywords with less or no filter.",
                        "search_time":datetime.now(),
                        "search_user":user,
                        "search_query": req_body,
                        "search_result":[]
                        }
                        db = await mongo_connect()
                        _collection_name = f"search_logs_{datetime.now().strftime('%Y-%m-%d')}"
                        collection = db[_collection_name]
                        result = collection.insert_one(search_log)
                        print(
                            f"Search Logs inserted into Mongo DB -- > {result.inserted_id}")
                    except Exception as err:
                        print(
                            f"Error in inserting Search Logs into Mongo DB -- > {err}")
                        raise RuntimeError
                    
            else:
                return_response.status_code = 200
                return_data = {
                    "status": "failed",
                    "message": "Oops!!! your search did not match any document. Try different keywords with less or no filter."
                }
                
                # insert data in mongodb for finding duplicate nuggets
                try:
                    # initializing mongo
                    search_log = {
                        "status": "failure",
                        "message": "Oops!!! your search did not match any document. Try different keywords with less or no filter.",
                        "search_time":datetime.now(),
                        "search_user":user,
                        "search_query": req_body,
                        "search_result":[]
                    }
                    db = await mongo_connect()
                    _collection_name = f"search_logs_{datetime.now().strftime('%Y-%m-%d')}"
                    collection = db[_collection_name]
                    result = collection.insert_one(search_log)
                    print(
                        f"Search Logs inserted into Mongo DB -- > {result.inserted_id}")
                except Exception as err:
                    print(
                        f"Error in inserting Search Logs into Mongo DB -- > {err}")
                    raise RuntimeError
                    
            print(return_data)
            print([return_response])
            return return_data
    except Exception as err:
        print(f"Exception in searching nuggets --> {err}")
        return_response.status_code = 400
        return_data = {
            "status": "failed",
            "message": "Error in search nugget api"
        }
        print(f"{return_data}")
        return return_data


@app.post("/update-nugget")
async def update_nuggets(request: Request, return_response: Response):

    try:
        print("Inside update nugget api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        req_body = await request.json()

        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }

        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError

        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            print("token verified successfully")
            try:
                # initializing elastic
                es = await initialize_elastic()
            except Exception as err:
                raise ContentTooShortError

            # search the data in elastic search
            query = await create_update_query(req_body)

            resp = es.update(index=index, id=req_body["id"], body=query)
            print("---Nugget Updated---")
            print(resp)

            # reconstrut the response
            # resp = resp["hits"]["hits"]

            return_response.status_code = 200
            return_data = {
                "status": "success",
                "result": resp["result"],
                "nugget_id": resp["_id"]
            }
            print(return_data)
            print([return_response])
            return return_data
    except Exception as err:
        print(f"Exception in updating nuggets --> {err}")
        return_response.status_code = 400
        return_data = {
            "status": "failure",
            "result": "Error in Updating Nugget"
        }
        print(f"{return_data}")
        return return_data


# @app.post("/delete-nugget")
# async def delete_nuggets(request: Request, return_response: Response):

#     try:
#         print("Inside delete nugget api")
#         client_id = request.headers.get("client_id")
#         client_secret = request.headers.get("client_secret")
#         # print(f"Client ID --> {client_id}")
#         # print(f"Client Secret --> {client_secret}")
#         req_body = await request.json()

#         headers = {
#             "client_id": client_id,
#             "client_secret": client_secret
#         }

#         try:
#             print("Requesting token creation api")
#             get_token = ''
#             print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
#                     get_token = await response.json()
#         except Exception as err:
#             print(f"Failure in token creation request --> {err}")
#             raise HTTPError

#         # verify Token
#         token_verify = await get_current_active_user(get_token)
#         if (token_verify):
#             print("token verified successfully")
#             try:
#                 # initializing elastic
#                 es = await initialize_elastic()
#             except Exception as err:
#                 raise ContentTooShortError

#             resp = es.delete(index=index, id=req_body["id"])
#             print("---Nugget Deleted---")
#             print(resp)

#             # reconstrut the response
#             # resp = resp["hits"]["hits"]

#             return_response.status_code = 200
#             return_data = {
#                 "status": "success",
#                 "result": resp["result"],
#                 "nugget_id": resp["_id"]
#             }
#             print(return_data)
#             print([return_response])
#             return return_data
#     except Exception as err:
#         print(f"Exception in deleting nuggets --> {err}")
#         return_response.status_code = 400
#         return_data = {
#             "status": "failure",
#             "result": "Error in Deleting Nugget"
#         }
#         print(f"{return_data}")
#         return return_data


@app.get("/get-all-nugget")
async def get_all_nuggets(return_response: Response):

    try:
        # initializing elastic
        es = await initialize_elastic()

        search_query1 = {
            "size": 10000,
            "query": {
                "match_all": {}
            }
        }
        resp = es.search(index=index, body=search_query1)
        if (resp["hits"]["hits"]):
            print("Nugget data available and extracted")
            return resp
        else:
            print("Nugget data Empty")
            return resp

    except Exception as err:
        print(f"Exception in get_all_nuggets --> {err}")
        return_response.status_code = 400
        return_data = {
            "status": "failure",
            "result": "Error in get_all_nuggets"
        }
        print(f"{return_data}")
        return return_data


@app.post("/check-duplicate")
async def check_duplicate_nuggets(request: Request, input_data: duplicate_nugget_model, return_response: Response):
    try:
        print("Inside check duplicate nugget api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        req_body = dict(input_data)
        print(f"Request Body ---->  {req_body}")
        cleaned_nugget_string = await clean_nuggets(req_body)
        print(cleaned_nugget_string)
        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError
        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            print("token verified successfully")
            try:
                # initializing mongo
                db = await mongo_connect()
                collection = db['string_data']
            except Exception as err:
                raise RuntimeError
            documents = collection.find()
            _all_mongo_docs = list(documents)
            # print(f"all mongo db data\n\n{_all_mongo_docs}")
            print(f"Len of mongo data------------>{len(_all_mongo_docs)}")
            all_nugget_string = []
            if _all_mongo_docs:
                for document in _all_mongo_docs:
                    all_nugget_string.append(document['str_value'])
                _duplicate_nuggets = await find_duplicate_nugget(all_nugget_string, cleaned_nugget_string["str_value"])
                if (_duplicate_nuggets[0] == True):
                    all_duplicates = await get_nugget_id(_all_mongo_docs, _duplicate_nuggets)
                    return_data = {
                        "status": "success",
                        "message": "duplicates search completed",
                        "total_duplicates": len(all_duplicates),
                        "result": all_duplicates
                    }
                    print(return_data)
                    print([return_data])
                    return return_data
                else:
                    return_data = {
                        "status": "failure",
                        "message": "No duplicate nugget found !!!",
                    }

                    print(return_data)
                    print([return_data])
                    return return_data
            else:
                return_data = {
                        "status": "failure",
                        "message": "No duplicate nugget found !!!",
                    }
                print(return_data)
                print([return_data])
                return return_data          
    except Exception as err:
        print(f"Error in getting duplicate nuggets --> {err}")
        return_response.status_code = 400
        return_data = {
            "status": "failed",
            "message": "Error in check duplicates api"
        }
        print(f"{return_data}")
        return return_data
        


@app.post("/update/{update_field}")
async def update_nugget_fields(request: Request, return_response: Response, nugget_id: str, user: str, update_field: str, count: int = None, comment_format: comment_model = None):
    try:
        user = user.upper()
        print("Inside update field nugget api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")

        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError
        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            try:
                # initializing elastic
                es = await initialize_elastic()
            except Exception as err:
                raise ContentTooShortError
            query = {
                "query": {
                    "term": {
                        "_id": {
                            "value": nugget_id
                        }
                    }
                }
            }
            resp = es.search(index=index, body=query)
            print("Nugget search is done")
            print(resp)
            if(resp['hits']['hits']):
                es_result = resp['hits']['hits'][0]["_source"]
                print(es_result)
                if (update_field == "view"):
                    past_views = es_result["views"]
                    present_views = past_views + 1
                    update_query = {
                        "doc": {
                            "views": present_views
                        }
                    }
                    resp = es.update(index=index, id=nugget_id, body=update_query)
                    print("---Nugget Updated  --- Views Field  ---")
                    print(resp)
                elif (update_field == "like"):
                    past_likes = es_result["likes"]
                    present_likes = past_likes + count
                    update_query = {
                        "doc": {
                            "likes": present_likes
                        }
                    }
                    resp = es.update(index=index, id=nugget_id, body=update_query)
                    print("---Nugget Updated  ---  Likes Field  ---")
                    print(resp)

                    if (count == 1):
                        field_values = {
                            "like": "true",
                            "dislike": "false"
                        }
                        like_dislike_update = await store_likes_dislikes(nugget_id, user, field_values)
                        print("MongoDB updated successfully")
                    if (count == -1):
                        like_dislike_update = await delete_likes_dislikes(nugget_id, user)
                        print("MongoDB updated successfully")

                elif (update_field == "dislike"):
                    past_dislikes = es_result["dislikes"]
                    present_dislikes = past_dislikes + count
                    update_query = {
                        "doc": {
                            "dislikes": present_dislikes
                        }
                    }
                    resp = es.update(index=index, id=nugget_id, body=update_query)
                    print("---Nugget Updated  ---  Dislikes Field ---")
                    print(resp)

                    if (count == 1):
                        field_values = {
                            "like": "false",
                            "dislike": "true"
                        }
                        like_dislike_update = await store_likes_dislikes(nugget_id, user, field_values)
                        print("MongoDB updated successfully")
                    if (count == -1):
                        like_dislike_update = await delete_likes_dislikes(nugget_id, user)
                        print("MongoDB updated successfully")
                elif (update_field == "comment"):
                    comments = es_result["comment"]
                    req_body = dict(comment_format)
                    req_body["user_id"] = user
                    print(req_body)
                    print(comments)
                    comments.append(req_body)
                    print(f"Present Comments \n\n{comments}")
                    update_query = {
                        "doc": {
                            "comment": comments
                        }
                    }
                    resp = es.update(index=index, id=nugget_id, body=update_query)
                    print("---Nugget Updated  ---  Comment Field ---")
                    print(resp)
                    # reconstrut the response
                    # resp = resp["hits"]["hits"]
                return_response.status_code = 200
                return_data = {
                    "status": "success",
                    "result": resp["result"],
                    "nugget_id": resp["_id"]
                }
                print(return_data)
                print([return_response])
                return return_data
            else:
                print(f"No nugget found with Nugget ID ---> {nugget_id}")
                return_response.status_code = 400
                return_data = {
                    "status": "failure",
                    "result": f"No nugget found with Nugget ID ---> {nugget_id}"
                }
                print(f"{return_data}")
                return return_data      
    except Exception as err:
        print(f"Exception in update field api --> {err}")
        return_response.status_code = 400
        return_data = {
            "status": "failure",
            "result": "Error in update field api"
        }
        print(f"{return_data}")
        return return_data


@app.get("/delete-all-nugget")
async def delete_all_nuggets(request: Request, return_response: Response):
    try:
        print("Inside delete all nugget api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError
        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            try:
                # initializing elastic
                es = await initialize_elastic()
                search_query1 = {
                    "query": {
                        "match_all": {}
                    }
                }
                resp = es.delete_by_query(index=index, body=search_query1)
                print(resp)
                return resp
            except Exception as err:
                print(f"Exception in delete_all_nuggets --> {err}")
                return_response.status_code = 400
                return_data = {
                    "status": "failure",
                    "result": "Error in delete_all_nuggets"
                }
                print(f"{return_data}")
                return return_data
    except Exception as err:
        print(f"Exception in verifying user for authentication --> {err}")
        raise RuntimeError


@app.get("/get-nugget-by-id")
async def get_nugget_by_id(request:Request, id: str, return_response:Response):
    try:
        print("Inside get nugget by id api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError
        # verify Token
        token_verify = await get_current_active_user(get_token)
        if (token_verify):
            _nugget_id = id
            try:
                # initializing elastic
                es = await initialize_elastic()
            except Exception as err:
                raise ContentTooShortError
            query = {
                "query": {
                    "term": {
                        "_id": {
                            "value": _nugget_id
                        }
                    }
                }
            }
            try:
                resp = es.search(index=index, body=query)
                print("Nugget search is done")
                print(resp)
                es_result = resp['hits']['hits']
                print(f"{_nugget_id} --> {es_result}")
                if (es_result):
                    result_data = es_result[0]["_source"]
                    if(result_data['system_demo'] == 'No'):
                        result_data['system_demo'] = ''
                    print(result_data)
                    return result_data
                else:
                    print(f"No nugget found with Nugget ID ---> {_nugget_id}")
                    return None
            except Exception as err:
                print(f"Error in get-nugget-by-id function ---> {err}")
                raise RuntimeError
    except Exception as err:
        print(f"Error in get-nugget-by-id api ---> {err}")
        return_response.status_code = 400
        return_result = {
                    "status": "failure",
                    "message": "Error in getting nugget by id"
                }
        return return_result

@app.get("/get-comment")
async def get_comment_by_id(nugget_id: str, return_response:Response):
    _nugget_id = nugget_id

    try:
        # initializing elastic
        es = await initialize_elastic()
    except Exception as err:
        raise ContentTooShortError
    query = {
        "query": {
            "term": {
                "_id": {
                    "value": _nugget_id
                }
            }
        }
    }

    try:
        resp = es.search(index=index, body=query)
        print("Nugget search is done")
        print(resp)
        es_result = resp['hits']['hits']
        if (es_result):
            result_data = es_result[0]["_source"]["comment"]
            if (result_data):
                print(result_data)
                return_result = {
                    "status": "success",
                    "message": "Comments Found!",
                    "comment": result_data
                }
                return return_result
            else:
                return_result = {
                    "status": "failure",
                    "message": "No Comments Found!",
                    "comment": result_data
                }
                return return_result
        else:
            print(f"No nugget found with Nugget ID ---> {_nugget_id}")
            return None
    except Exception as err:
        print(f"Error in get-comment function ---> {err}")
        return_response.status_code = 400
        return_result = {
                    "status": "failure",
                    "message": "Error in getting comments"
                }
        return return_result

@app.post("/SharepointSearch")
async def sharepoint_search(request: Request, input_data: sharepoint_search_model, return_response: Response):
    try:
        print("Inside sharepoint search api")
        client_id = request.headers.get("client_id")
        client_secret = request.headers.get("client_secret")
        req_body = dict(input_data)
        
        # print(f"Client ID --> {client_id}")
        # print(f"Client Secret --> {client_secret}")
        print(f" Req Body --> {req_body}")
        
        headers = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        try:
            print("Requesting token creation api")
            get_token = ''
            print(f"Pragya Token URL --> {PRAGYA_TOKEN_URL}")
            async with aiohttp.ClientSession() as session:
                async with session.get(PRAGYA_TOKEN_URL, headers=headers) as response:
                    get_token = await response.json()
        except Exception as err:
            print(f"Failure in token creation request --> {err}")
            raise HTTPError
        
        # verify Token
        token_verify = await get_current_active_user(get_token)
        print(token_verify)
        if (token_verify):
            bearer_token = await create_bearer_token()
            _search = await _sharepoint_search(req_body["query"], bearer_token)
            return _search
        else:
            print("Error in Verifying Token")
            raise RuntimeError 
    except Exception as err:
        print(f"Error in sharepoint search api ---> {err}")
        return_response.status_code = 400
        return_result = {
            "status": "failure",
            "message": "Error in Sharepoint Search"
        }
        return return_result

if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=local_host_port)
    uvicorn.run(app, host = "0.0.0.0", port = 8505)
