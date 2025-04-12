# This file contains functions for handling and passing requests to the appropriate LxCTs 



from fastapi import FastAPI, HTTPException, APIRouter
from routers import secure, public
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

import datetime



# Testing use of advanced events - Lifespan Events - as requested by FASTapi deprecation warning 

# https://fastapi.tiangolo.com/advanced/events/


logging.basicConfig(filename="fastapi_lifespan_backend.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info("Starting FastAPI lifespan function...")

redis_host ='192.168.1.83'
redis_port = 6379
redis_client = None 


def get_redis_client():
    """
    Function to get the Redis client
    """
    con_redis = None
    try:
        if redis_client is None:
            con_redis = rd.StrictRedis(host=redis_host, port=redis_port, db=0)
        return con_redis
    except rd.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        return None



def app_startup_routine():

    redis_rety_count = 0
    redis_rety_limit = 5
    logger.info("Running startup routine...")
    global redis_client
    while redis_rety_count < redis_rety_limit:
        try:
            redis_client = get_redis_client()
            if redis_client is not None:
                logger.info("Connected to Redis server successfully.")
                break
            else:
                logger.error("Failed to connect to Redis server.")
                redis_rety_count += 1
                logger.info(f"Retrying connection to Redis... Attempt {redis_rety_count}/{redis_rety_limit}")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            redis_rety_count += 1
            logger.info(f"Retrying connection to Redis... Attempt {redis_rety_count}/{redis_rety_limit}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Define Startup tasks
    logger.info("------------------------------")  # Log separator
    logger.info("Starting up handling.py...")  # Log startup event

    app_startup_routine()
    
    yield
    # Define Shutdown tasks

    logger.info("Shutting down handling.py...")  # Log shutdown event


app = FastAPI(lifespan=lifespan)


# adding health check to endpoints to help startups
@app.get("/healthcheck")
async def healthcheck():
    """
    Health check endpoint to verify if the service is running.
    """
    return {"status": "OK"}



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
        logger.error(f"Error processing request: {str(e)}")
        return {"error": "Failed to process request"}
    



# process the data 
@app.post("/process_data")
def process_data(redis_key: str = None, operation: str = None, dual: bool = False):
    """
    Function to process the data that has been passed in the request
    """

    logger.info(f"Processing data for redis key: {redis_key}")

    logger.info(f"Operation requested: {operation}")
    logger.info(f"Dual processing requested: {dual}")
    # check if key is not none 
    if redis_key is None:
        logger.error(f"Redis key is None")
        return {"error": "Redis key is None"}
    
    #check if dual is true
    if operation == "DTW_analysis":
        if dual == True:
            try:
                # split the redis key into two keys
                logger.info(f"Dual processing requested")
                redis_key_1 = redis_key.split(",")[0]
                redis_key_2 = redis_key.split(",")[1]

                logger.info(f"Redis key 1: {redis_key_1}")
                logger.info(f"Redis key 2: {redis_key_2}")
                # get the data from the redis store
                op_data_1 = get_redis_data(redis_key_1)
                op_data_2 = get_redis_data(redis_key_2)

                data_info_1, df1 = processing.configure_data(op_data_1)
                data_info_2, df2 = processing.configure_data(op_data_2)

                updated_data_df = dtw.dtw_custom(df1, data_info_1, df2, data_info_2)
                if updated_data_df is None:
                    logger.error("Error in DTW processing")
                    return {"error": "Error in DTW processing"}
                proc_key = send_processed_data_to_redis(updated_data_df)
                try:
                    val = send_data_to_server_db( proc_key, redis_key, operation, flag=1)
                    try: 
                        if "error" in val:
                            logger.error(f"Error sending data to server: {val['error']}")
                            return {"error": val["error"]}
                        else:
                            logger.info(f"Data sent to server successfully: {val}")
                    except Exception as e:
                        logger.error(f"Error processing server response: {str(e)}")
                        return {"error": "Failed to process server response"}
                except Exception as e:
                    logger.error(f"Error sending data to server: {str(e)}")
                    return {"error": "Failed to send data to server"}

                return {"redis_key": proc_key}


            except Exception as e:
                logger.error(f"Error processing dual keys: {str(e)}")
                return {"error": f"Failed to process dual keys - {str(e)}"}
        else:
            # dual is false - need dual to be true for DTW 
            logger.error(f"Dual processing not requested for DTW analysis")
            return {"error": "Dual Keys not sent for DTW analysis"}
            
        


    op_data = get_redis_data(redis_key)
    # if  return {"error": "Redis key not found"} is returned, then we need to handle this error and return a message to the user
    # log type returned 
    logger.info(f"Data type returned: {type(op_data)}")
    
    if isinstance(op_data, dict) and "error" in op_data:
        logger.error(f"Error retrieving data from Redis: {op_data['error']}")
        return {"error": op_data["error"]}
    else:
        logger.info(f"Data retrieved from Redis: Available")
    

    # begin processing the data
   
    logger.info(f"Data to process: available")
    logger.info(f"Calling processing script...")
    data_info, df = processing.configure_data(op_data)
    # strip data_info of the dataframe
    logger.info(f"Data info: {data_info}")



    # W.I.P - 

    # After getting the data info, we need a pipeline to make decisions on what to do with the data - specifically time series vs non time series data
    # We must define a check to ensure that the data we have is inlien with the requried data processing needed 
    # this in line with the required processing requested by the user 
    # ^ update needed to handling incoming process request parameter

    try:
        if operation == "Smp_Daily_Avg":
            logger.info(f"Processing data for daily average... calling analysis function")
            updated_data_df = smp.daily_average(df, data_info)

        


        # send data to redis store 
        logger.info(f"Sending processed data to Redis...")
        try:
            proc_key = send_processed_data_to_redis(updated_data_df)
            if "error" in proc_key:
                logger.error(f"Error sending data to Redis: {proc_key['error']}")
                return {"error": proc_key["error"]}
            else:
                logger.info(f"Data sent to Redis successfully: {proc_key}")
        except Exception as e:
            logger.error(f"Error sending data to Redis: {str(e)}")
            return {"error": "Failed to send data to Redis"}

        try:
            val = send_data_to_server_db( proc_key, redis_key, operation, flag=1)
            try: 
                if "error" in val:
                    logger.error(f"Error sending data to server: {val['error']}")
                    return {"error": val["error"]}
                else:
                    logger.info(f"Data sent to server successfully: {val}")
            except Exception as e:
                logger.error(f"Error processing server response: {str(e)}")
                return {"error": "Failed to process server response"}
        except Exception as e:
            logger.error(f"Error sending data to server: {str(e)}")
            return {"error": "Failed to send data to server"}

        return {"redis_key": proc_key}
    except:
        logger.error(f"Unsupported operation: {operation}")
        return {"error": "Unsupported operation"}
    

    # send the processed data to internal server


def send_data_to_server_db(proc_key: str, redis_key: str, operation: str, flag: int):
    """
    Function to send processed data to the internal server database.
    """
    try:
        logger.info(f"Sending data to server with proc_key: {proc_key}, redis_key: {redis_key}, operation: {operation}, flag: {flag}")
        # Placeholder for actual implementation
        url = f"http://192.168.1.81:8000/store_processed_data?key_proc={proc_key}&key_raw={redis_key}&analysis_type={operation}&flag={flag}"  # Replace with actual server URL
        try:
            response = requests.post(url)
            response.raise_for_status()  # raises errors ~400 and ~500
            logger.info(f"Server response: {response.text}")  # Log the server's response content
            return {"status": "success", "message": "Data sent to server successfully"}
        except Exception as e:
            logger.error(f"Error parsing server response: {str(e)}")
            return {"error": "Failed to parse server response"}
        
    except Exception as e:
        logger.error(f"Error in send_data_to_server_db: {str(e)}")
        return {"error": "Failed to send data to server"}


def get_redis_data(redis_key):
    """
    Function to get the data from the redis store
    """

    try:
        # get redis data via the key
        if redis_client.exists(redis_key):
            logger.info(f"Redis key {redis_key} exists")
            redis_data = redis_client.get(redis_key)

        

        else:
            logger.info(f"Redis key {redis_key} does not exist")
            return {"error": "Redis key not found"}
        if redis_data is None:
            return {"error": f"No data found for the key {redis_key}"}
        # Convert the redis data to a di
        logger.info(f"Redis data: Available")
        return redis_data

    except Exception as e:
        logger.error(f"Error retrieving data from Redis: {str(e)}")
        return {"error": "Failed to retrieve data from Redis"}



# https://stackoverflow.com/questions/10252010/serializing-class-instance-to-json 
def json_serial(obj):
    #logger.info(f"Serializing object of type {type(obj)}")
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Type {type(obj)} not serializable")

def send_processed_data_to_redis(data):
    
    """
    Function to send the processed data back to the redis store
    """
    logger.info(f"Sending processed data to Redis... func")
    # convert data to a list first before sending to redis
    if isinstance(data, pd.DataFrame):
        logger.info(f"Data is a DataFrame")
        data = data.to_dict(orient='records')
    elif isinstance(data, pd.Series):
        logger.info(f"Data is a Series")
        data = data.to_dict()
    elif isinstance(data, dict):
        pass  # Already in the correct format
    else:
        logger.error(f"Unsupported data type: {type(data)}")
        return {"error": "Unsupported data type"}


    try:
        # Convert the data to JSON
        logger.info(f"Converting data to JSON...")
        
        # Generate a unique key for the processed data
        key_num = random.randint(1, 10000)
        key_str = random.choice(['a', 'b', 'c', 'd', 'e'])
        key = f"processed_data:{key_num}{key_str}"
        redis_key = key
        logger.info(f"Generated Redis key: {redis_key}")
        # Store the processed data in Redis
        redis_client.set(redis_key, json.dumps(data, default=json_serial), ex=7200)  # TTL to 2 hours
        

        return redis_key
    except Exception as e:
        logger.error(f"Error sending data to Redis: {str(e)}")
        return {"error": "Failed to send data to Redis"}



    pass






