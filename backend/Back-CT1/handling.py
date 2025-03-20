# This file contains functions for handling and passing requests to the appropriate LxCTs 



from fastapi import FastAPI, HTTPException
import subprocess
import requests
import pandas as pd
import numpy as np 
from contextlib import asynccontextmanager
import logging
import redis as rd

from typing import Dict, Any

import Custom_Fuzzy as fuzzy
import Custom_DTW as dtw
import step_analysis as step



# Testing use of advanced events - Lifespan Events - as requested by FASTapi deprecation warning 

# https://fastapi.tiangolo.com/advanced/events/


logging.basicConfig(filename="fastapi_lifespan_backend.log", level=logging.INFO, format="%(asctime)s - %(message)s")

logging.info("Starting FastAPI lifespan function...")

redis_host ='192.168.1.86'
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
async def rec_req(operation: str = "op", data: Dict[str, Any]=None, redis_key: str = None):
    """
    Function to dynamically process different types of incoming data from the redis store.
    Operation param is sent along with the data to indicate the type of processing required.
    """
    # try:
    #     if not isinstance(data, dict) or "values" not in data:
    #         raise HTTPException(status_code=400, detail="Invalid request format")

    #     # Convert data to Pandas DataFrame
    #     df = pd.DataFrame(data["values"])
    #     #logging.info(df)
    #     #logging.info(data)
    #     # Get the requested operation
        

    #     # Perform dynamic calculations based on operation
    #     if operation == "stats":  # Summary statistics
    #         # get average of each column where data is int or float
    #         result = df.select_dtypes(include=[np.number]).mean()
    #         logging.info(f'testest --- {result}')
    #         result = result.to_dict()


    #     else:
    #         raise HTTPException(status_code=400, detail="Unsupported operation")

    #     #logging.info(result)
    #     result = format_response(result)  # Apply formatting here
    #     #logging.info(result)
    #     return {"processed": result}

    # except Exception as e:
    #     raise HTTPException(status_code=400, detail=str(e))


    try:
        # get redis data via the key
        redis_data = redis_client.get(redis_key)
        if redis_data is None:
            raise HTTPException(status_code=404, detail="Redis key not found")
        # Convert the redis data to a di

    except Exception as e:
        logging.error(f"Error retrieving data from Redis: {str(e)}")
        return {"error": "Failed to retrieve data from Redis"}


def format_response(result: Dict[str, Any]) -> list:
    # To ensure we always return a list of dictionaries
    try:
        if isinstance(result, dict):
            return [{key: value} for key, value in result.items()]
        elif isinstance(result, list):
            return result  # Already in correct format
        else:
            raise ValueError("Unexpected response format")
    except Exception as e:
        logging.error(f"Error formatting response: {str(e)}")
    

def configure_data()-> None:
    """
    Function to configure the data that has been passed 

    Function is to take the raw data, convert to dframe and 
    then check the data types of the columns and format a response
    based on the data types of the columns for processing

    """



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


