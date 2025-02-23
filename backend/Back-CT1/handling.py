# This file contains functions for handling and passing requests to the appropriate LxCTs 



from fastapi import FastAPI, HTTPException
import subprocess
import requests
import pandas as pd
import numpy as np 
from contextlib import asynccontextmanager
import logging

from typing import Dict, Any



# Testing use of advanced events as requested by FASTapi deprecation warning 

# https://fastapi.tiangolo.com/advanced/events/


logging.basicConfig(filename="fastapi_lifespan_backend.log", level=logging.INFO, format="%(asctime)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Define Startup tasks
    yield
    # Define Shutdown tasks

app = FastAPI(lifespan=lifespan)



@app.post("/rec_req")
async def rec_req(operation: str = "op", data: Dict[str, Any]=None):
    """
    Function to dynamically process different types of incoming Pandas-like data.
    """
    try:
        if not isinstance(data, dict) or "values" not in data:
            raise HTTPException(status_code=400, detail="Invalid request format")

        # Convert data to Pandas DataFrame
        df = pd.DataFrame(data["values"])
        logging.info(df)
        logging.info(data)
        # Get the requested operation
        

        # Perform dynamic calculations based on operation
        if operation == "stats":  # Summary statistics
            result = df.describe().to_dict()

        else:
            raise HTTPException(status_code=400, detail="Unsupported operation")

        logging.info(result)

       
        return {result}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
