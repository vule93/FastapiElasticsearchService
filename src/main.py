# from fastapi.middleware.cors import CORSMiddleware
from dataclasses import fields
from http import client
from operator import index
from symbol import parameters
from urllib import request
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional
from faker import Faker
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
import pandas as pd
import os
from typing import Union
from dotenv import load_dotenv
import boto3
import csv
from elasticsearch_dsl import Q, Search
from elasticsearch_dsl.query import MultiMatch
from io import StringIO
import logging
logging.basicConfig(level=logging.INFO)
load_dotenv()

# from routes.api import router as api_router

app = FastAPI(debug=True)

def generate_actions():
    """Reads the file through csv.DictReader() and for each row
    yields a single document. This function is passed into the bulk()
    helper to create many documents in sequence.
    """
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )

    obj = s3.get_object(Bucket=os.getenv('BUCKET_NAME'), Key=os.getenv('FILE_PATH'))
    data = obj['Body'].read().decode('utf-8').splitlines()
    records = csv.reader(data)
    headers = next(records)
    csvData = []
    headerCount = len(headers)

    for eachRecord in records:
        tmp = {}
        for count in range(0, headerCount):
            tmp[headers[count]] = eachRecord[count]
        csvData.append(tmp)
    
    for n in csvData:
        doc = {
            "user_id": n["user_id"],
            "first_name": n["first_name"],
            "last_name": n["last_name"],
            "email": n["email"],
            "address": n["address"]
        }

        yield doc

# Create fake data for User and insert on S3 bucket  
def generate_fake_data_into_csv_file_on_S3_bucket():
    users_list = []
    faker_instance = Faker()

    for i in range(1, 1001):
        user = {}
        user['user_id'] = faker_instance.random_number(5)
        user['first_name'] = faker_instance.first_name()
        user['last_name'] = faker_instance.last_name()
        user['email'] = faker_instance.email()
        user['address'] = faker_instance.address()
        users_list.append(user)
    
    users_csv_dataframe = pd.DataFrame(users_list)

    csv_buffer = StringIO()
    users_csv_dataframe.to_csv(csv_buffer, index=False)
    s3csv = boto3.client("s3", 
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name = os.getenv('AWS_DEFAULT_REGION')
    )

    s3csv.put_object(Body=csv_buffer.getvalue(),
                           Bucket=os.getenv('BUCKET_NAME'),
                           Key=os.getenv('FILE_PATH'))


@app.get("/")
async def get_elastic():
    # Generate 1000 users into CSV file on AWS S3 bucket
    generate_fake_data_into_csv_file_on_S3_bucket()

    client = Elasticsearch([{'host': os.getenv("HOSTNAME_ELASTICSEARCH"), 'port': os.getenv("ELASTICSEARCH_PORT"),
                             'scheme': os.getenv("ELASTICSEARCH_SCHEME")}])

    # Create index on Elasticsearch
    index = 'users'
    settings = {"number_of_shards": 1}
    mappings = {
                "properties": {
                    "user_id": {"type": "text"},
                    "first_name": {"type": "text"},
                    "last_name": {"type": "text"},
                    "email": {"type": "text"},
                    "address": {"type": "text"},
                }
            }
    
    # Check if index already exists if not create otherwise
    index_exists = client.indices.exists(index='users')

    if not index_exists:
        client.indices.create(index=index, settings=settings, mappings=mappings, ignore=400)
    
    # Insert into elastc database
    success = 0
    for ok, action in streaming_bulk(
        client=client, index="users", actions=generate_actions()):
        success += 1

    return {"Data": success}

# Endpoint that returns all users
@app.get("/get-all-users")
async def getData():
    client = Elasticsearch([{'host': os.getenv("HOSTNAME_ELASTICSEARCH"), 'port': os.getenv("ELASTICSEARCH_PORT"),
                             'scheme': os.getenv("ELASTICSEARCH_SCHEME")}])
    client.indices.refresh(index="users")
    res = client.search(index="users", query={"match_all": {}}, size=1000)
    hits = res.get("hits", {}).get("hits", [])

    return {
        "results": [hit.get("_source") for hit in hits]
    }

# Search users by their first_name, last_name, address, email and user_id
@app.get("/search")
async def getDataByFirstName(value_to_search: Union[str, None] = None):
    client = Elasticsearch([{'host': os.getenv("HOSTNAME_ELASTICSEARCH"), 'port': os.getenv("ELASTICSEARCH_PORT"),
                             'scheme': os.getenv("ELASTICSEARCH_SCHEME")}])
    client.indices.refresh(index="users")
    query = MultiMatch(query=value_to_search, fields=['first_name', 'last_name', 'email', 'address', 'user_id'])
    result = {"results":[]}
    if not value_to_search:
        return result
    s = Search(using=client, index="users").query(query)
    response = s.execute()
    for hit in response:
        result["results"].append(hit)
    
    return result


# app.include_router(api_router)
