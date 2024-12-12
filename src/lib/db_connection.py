import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json
import os
import ssl
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
load_dotenv()

es_format = os.getenv("es_settings")
es_format = json.loads(es_format)
index = os.getenv("INDEX_NAME")
#ELASTIC_SEARCH_SERVER_IP = os.getenv("ELASTIC_SERVER")
ELASTIC_SEARCH_PROD_IP = os.getenv("ELASTIC_PROD")


async def initialize_elastic():
    try:
        print("Inside initialize elastic search function")
        """INITIALIZING ELASTIC SEARCH"""
        # es = Elasticsearch("http://localhost:9200")
        # es = Elasticsearch([ELASTIC_SEARCH_SERVER_IP], timeout=10000)
        # es = Elasticsearch([ELASTIC_SEARCH_PROD_IP], http_auth=('elastic', 'test123'),
        #                    scheme="https", timeout=10000)
        es = Elasticsearch(hosts=ELASTIC_SEARCH_PROD_IP,
                           port=443, use_ssl=True,
                           http_auth=(os.getenv("elasticUserName"),
                                      os.getenv("elastic_password")),
                           ssl_cert_reqs=ssl.CERT_NONE)
        """
        to check the connection of Elastic Search
        """
        print(es.info())
        print("--Elastic Search Initialized--")

        if not es.indices.exists(index=index):
            print(
                f"----ELASTIC INDEX  --> {index} DOESNOT EXIST----\nCREATING NEW ONE")
            es.indices.create(index=index, body=es_format)
            print("----ELASTIC SEARCH INDEX CREATED----")
        else:
            print("----ELASTIC SEARCH INDEX ALREADY EXISTS----")
        return es
    except Exception as err:
        print(f"Error in initializing Elastic Search: {err}")
        raise ConnectionError


async def mongo_connect():
    # Establish a connection to MongoDB
    try:
        # client = MongoClient('mongodb://localhost:27017/')
        # client = MongoClient(
        #     'mongodb://mongouat:Bosch%40123@10.47.35.157:27017')
        client = MongoClient(
            os.getenv("MONGO_DB_CONNECTION_STRING"), tls=True, tlsAllowInvalidCertificates=True)
        # Access the database and collection
        db = client['PRAGYA_360']
        print("Connected to MongoDB successfully!")
        return db
    except ConnectionFailure:
        print("Failed to connect to MongoDB.")
        raise ConnectionFailure
