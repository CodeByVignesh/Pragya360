import json
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BAP_BEARER_API = os.getenv("BEARER_TOKEN_LINK")
BAP_BEARER_INPUT = os.getenv("BEARER_TOKEN_INPUT")
BAP_BEARER_INPUT = json.loads(BAP_BEARER_INPUT)

GRAPH_URL = os.getenv("GRAPH_URL")


async def create_bearer_token():
    try:
        print("Inside Create Bearer Token API")
        url = f"{BAP_BEARER_API}/GenerateToken"
        print(url)
        # print(BAP_BEARER_INPUT)
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(url, headers=headers, data=BAP_BEARER_INPUT)

        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful!")
            # print(response.json())  # If the response is JSON
            response = response.json()
            return response['ms_access_token']
        else:
            print(
                f"Request failed with status code: {response.status_code}")
            # print the response content if needed
            # print(response.text)
            raise RuntimeError
    except Exception as err:
        print(f"Error in create bearer token function --> {err}")
        raise RuntimeError


async def _sharepoint_search(query, bearer_token):
    try:
        print("Inside sharepoint search function")
        print(f"query --> {query}")
        # print(f"Bearer Token --> {bearer_token}")
        
        graph_headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
        USER = BAP_BEARER_INPUT["username"]
        QUERY = str(query)
        GRAPH_API = f"{GRAPH_URL}/{USER}/drive/root/search(q='{QUERY}')?select=name,webUrl"

        print(GRAPH_API)

        graph_response = requests.get(GRAPH_API, headers=graph_headers)
        if graph_response.status_code == 200:
            print("Graph Request successful!")
            print(graph_response.json())
            return await process_sharepoint_result(graph_response.json())
        else:
            print(
                f"Request failed with status code: {graph_response.status_code}")
            # print the response content if needed
            print(graph_response.text)
            raise RuntimeError
    except Exception as err:
        print(f"Error in _sharepoint_search function --> {err}")
        raise RuntimeError
            


async def process_sharepoint_result(share_point_result):
    try:
        print("Inside process_sharepoint_result function")
        if (share_point_result["value"]):
            result_data = []
            for data in share_point_result["value"]:
                result_data.append({
                    "title": data["name"],
                    "summary": f"<a href={str(data['webUrl'])} target='_blank'>Click here to access the document</a>"
                })
            return_res = {
                "status": "success",
                "message": "search completed",
                "total_result": len(result_data),
                "result": result_data
            }
            print(return_res)
            return return_res

        else:
            return_res = {
                "status": "failure",
                "message": "No data found!",

            }
            print(return_res)
            return return_res
    except Exception as err:
        print(f"Error in process_sharepoint_result function --> {err}")
        raise RuntimeError
        
