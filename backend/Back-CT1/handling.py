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

import datetime



# Testing use of advanced events - Lifespan Events - as requested by FASTapi deprecation warning 

# https://fastapi.tiangolo.com/advanced/events/


logging.basicConfig(filename="fastapi_lifespan_backend.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info("Starting FastAPI lifespan function...")


redis_client = None



# Load the existing config
CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        return {}

def save_config(config_data):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config_data, file, indent=4)


def load_config_call():
    global CONFIG
    CONFIG = load_config()


def pull_config_data():
    # function to pull the updated config data from the server db 

    # send a request to the abstraction layer /healthcheck endpoint to see if tis active 
    # if it is active then send a request to the abstraction layer /config endpoint to get the config data



    config_local = load_config()
    config_server = None


    try:
        response = requests.get(f"http://{CONFIG['endpoints']['db-connection-layer']['ip']}:{CONFIG['endpoints']['db-connection-layer']['port']}/healthcheck")
        if response.status_code == 200:
            logging.info("Abstraction layer is active")
          
    except Exception as e:
        logging.error(f"Error connecting to abstraction layer: {e}")
        return None

    try:
        response = requests.get(f"http://{CONFIG['endpoints']['db-connection-layer']['ip']}:{CONFIG['endpoints']['db-connection-layer']['port']}/config")
        if response.status_code == 200:
            config_server = response.json()
            # if error in response then log the error and return None
            if 'error' in config_server:
                logging.error(f"Error pulling config data from server: {config_server['error']}")
                return None
            logging.info("Config data pulled from server")
        else:
            logging.error(f"Error pulling config data from server: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error connecting to abstraction layer: {e}")
        return None

    # comparing local config with server config and updating local config with server config

    try:
        # Extracting the "endpoints" section from both configurations
        local_endpoints = config_local.get("endpoints", {})
        server_endpoints = config_server.get("endpoints", {})

        # Compare and update the local endpoints with server endpoints
        for key, server_endpoint in server_endpoints.items():
            if key not in local_endpoints or local_endpoints[key] != server_endpoint:
                logging.info(f"Updating endpoint '{key}' in local config with server data.")
                local_endpoints[key] = server_endpoint

        # Save the updated endpoints back to the local configuration
        config_local["endpoints"] = local_endpoints

        # Save the updated local configuration to the config file
        save_config(config_local)
        logging.info("Local configuration updated successfully with server data.")

    except Exception as e:
        logging.error(f"Error updating local config with server data: {e}")

    return True

    pass


def get_redis_client():
    con_redis = None
    try:
        con_redis = rd.StrictRedis(host=CONFIG_FILE['endpoints']['redis-memory-store']['ip'], port=CONFIG_FILE['endpoints']['redis-memory-store']['port'], db=0)
        con_redis.ping()
        logger.info("Connected to Redis server successfully.")
        return con_redis
    except rd.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
    return con_redis


def app_startup_routine():
    rsp = None
    retry_count = 0

    
    # ---------------------
    # Get config data from the server db - output to file
    # ---------------------

    
    load_config_call()


        

    load_config_call()

    
    
    
    
    
    global redis_client
    redis_con_attempt = 0
    redis_con_max_attempts = 5
    while redis_client is None and redis_con_attempt < redis_con_max_attempts:
        try:
            redis_client = get_redis_client()
            if redis_client is None:
                logger.error("Failed to connect to Redis server.")
                raise Exception("Redis connection failed")
            if redis_client.ping():
                logger.info("Redis client ping successful.")
                logger.info("Redis client initialized successfully.")
                break

        except Exception as e:
            logger.error(f"Error during app startup: {e}")



    
        


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
    except:
        logger.error(f"Unsupported operation: {operation}")
        return {"error": "Unsupported operation"}
    

    # send the processed data to internal server


def send_data_to_server_db(proc_key: str, redis_key: str, operation: str, flag: int):
    """
    Function to send processed data to the internal server database.
    """
    endpoint_ip = CONFIG['endpoints']['db-connection-layer']['ip']
    endpoint_port = CONFIG['endpoints']['db-connection-layer']['port']
    try:
        logger.info(f"Sending data to server with proc_key: {proc_key}, redis_key: {redis_key}, operation: {operation}, flag: {flag}")
        # Placeholder for actual implementation
        url = f"http://{endpoint_ip}:{endpoint_port}/store_processed_data?key_proc={proc_key}&key_raw={redis_key}&analysis_type={operation}&flag={flag}"  # Replace with actual server URL
        response = requests.post(url)
        
        if response.status_code != 200:
            logger.error(f"Failed to send data to server. Status code: {response.status_code}, Response: {response.text}")
            return {"error": "Failed to send data to server"}
        


        # Add logic to send data to the server database here
        return {"status": "success", "message": "Data sent to server successfully"}
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



