# This file contains functions for handling and passing requests to the appropriate LxCTs 



from fastapi import FastAPI, HTTPException
import subprocess
import requests
import pandas as pd
import numpy as np 
from contextlib import asynccontextmanager
import logging
import redis as rd
import json
import random

from typing import Dict, Any

import Custom_Fuzzy as fuzzy
import Custom_DTW as dtw
import step_analysis as step

import processing_script as processing

import simple_analysis as smp




# Testing use of advanced events - Lifespan Events - as requested by FASTapi deprecation warning 

# https://fastapi.tiangolo.com/advanced/events/


logging.basicConfig(filename="fastapi_lifespan_backend.log", level=logging.INFO, format="%(asctime)s - %(message)s")

logging.info("Starting FastAPI lifespan function...")

redis_host ='192.168.1.83'
redis_port = 6379

try:
    redis_client = rd.StrictRedis(host=redis_host, port=redis_port, db=0)
    redis_client.ping()
    logging.info("Connected to Redis server successfully.")
except rd.ConnectionError as e:
    logging.error(f"Redis connection error: {e}")



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Define Startup tasks
    logging.info("------------------------------")  # Log separator
    logging.info("Starting up handling.py...")  # Log startup event
    
    yield
    # Define Shutdown tasks

    logging.info("Shutting down handling.py...")  # Log shutdown event


app = FastAPI(lifespan=lifespan)



@app.post("/rec_req")
async def rec_req(redis_key: str = None):
    """
    Function to dynamically process different types of incoming data from the redis store.
    Operation param is sent along with the data to indicate the type of processing required.
    """
    try:
        data_send = get_redis_data(redis_key)
        if "error" in data_send:
            return {"error": data_send["error"]}

        return data_send

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return {"error": "Failed to process request"}
    



# process the data 
@app.post("/process_data")
def process_data(redis_key: str = None):
    """
    Function to process the data that has been passed in the request
    """

    logging.info(f"Processing data for redis key: {redis_key}")

    op_data = get_redis_data(redis_key)


    # begin processing the data
   
    logging.info(f"Data to process: available")
    data_info_df = processing.configure_data(op_data)
    # strip data_info of the dataframe
    data_info = data_info_df.pop("df", None)
    logging.info(f"Data info: {data_info}")
    # W.I.P - 
    # send data to redis store 
    proc_key = send_processed_data_to_redis(data_info)

    return {"redis_key": proc_key}




def get_redis_data(redis_key):
    """
    Function to get the data from the redis store
    """

    try:
        # get redis data via the key
        if redis_client.exists(redis_key):
            logging.info(f"Redis key {redis_key} exists")
            redis_data = redis_client.get(redis_key)

        

        else:
            logging.info(f"Redis key {redis_key} does not exist")
            return {"error": "Redis key not found"}
        if redis_data is None:
            return {"error": f"No data found for the key {redis_key}"}
        # Convert the redis data to a di
        logging.info(f"Redis data: Available")
        return redis_data

    except Exception as e:
        logging.error(f"Error retrieving data from Redis: {str(e)}")
        return {"error": "Failed to retrieve data from Redis"}


def send_processed_data_to_redis(data):

    """
    Function to send the processed data back to the redis store
    """

    try:
        # Convert the data to JSON
        json_data = json.dumps(data)

        # Generate a unique key for the processed data
        redis_key = f"processed_data:{random.randint(1, 10000)}"

        # Store the processed data in Redis
        redis_client.set(redis_key, json_data)

        return redis_key
    except Exception as e:
        logging.error(f"Error sending data to Redis: {str(e)}")
        return {"error": "Failed to send data to Redis"}



    pass


def step_analysis_func():
    """
    Function to process the PLC step analysis requests
    """


    pass 



def fuzzy_func():
    """
    Function to process the fuzzy logic requests
    """

    pass


def dtw_func():
    """
    Function to process the DTW requests
    """

    pass


