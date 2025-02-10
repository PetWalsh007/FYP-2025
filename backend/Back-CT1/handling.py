# This file contains functions for handling and passing requests to the appropriate LxCTs 



from fastapi import FastAPI
import subprocess
import requests
import pandas as pd
import numpy as np 
from contextlib import asynccontextmanager



app = FastAPI()

# Testing use of advanced events as requested by FASTapi deprecation warning 

# https://fastapi.tiangolo.com/advanced/events/


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Define Startup tasks
    yield
    # Define Shutdown tasks

app = FastAPI(lifespan=lifespan)




@app.get("/rec_req")
def get_data_request(database: str ="null", table_name: str = "null", fil_condition: str = '1=1', limit: int = 10):
    # function to get data from backend and send processed data to request

    response = requests.get(f'http://192.168.1.81:8000/data?database={database}&table_name={table_name}&limit={limit}')


    pass


