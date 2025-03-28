# This file contains functions for processing the data 

"""
Function to configure the data that has been passed 

Function is to take the raw data, convert to dframe and 
then check the data types of the columns and format a response
based on the data types of the columns for processing

"""



from typing import Dict, Any
import numpy as np
import pandas as pd
import json
import logging

# setup_processing_logging
logger = logging.getLogger(__name__)



# endpoints here to be defined via paramarters passed to condigure_data

def configure_data(raw_data):

    logger.info("Configuring data...")  # Log data configuration event
    data_dict, df= _desc_data(raw_data)


    return data_dict, df



def _desc_data(raw_data):

    logger.info("Describing data...")  # Log data description event

    
    try:
        # Convert raw data to DataFrame
        
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode('utf-8')

        df = pd.read_json(raw_data)



        logger.info(f"DataFrame shape: {df.shape}")  # Log DataFrame shape
        data_column_info = []
        is_time_data = False  # Will be set True if *any* col is time-like

        # 
        # https://pandas.pydata.org/docs/reference/api/pandas.api.types.is_datetime64_any_dtype.html
        # This and similar are used to check the data types of the columns in the dataframe
        # https://pandas.pydata.org/docs/reference/api/pandas.api.types.is_numeric_dtype.html
        # https://pandas.pydata.org/docs/reference/api/pandas.api.types.is_integer_dtype.html
        


        for col in df.columns:
            logger.info(f"Processing column: {col}")  # Log column processing event
            cols_info = {}  # new dict per column
            # remove whitespace from column names
            col = col.strip()
            
            cols_info['name'] = col
            # parse name in the columns to check for dates, datetime, time etc 
            date_list = ['date', 'datetime', 'time', 'timestamp', 'timezone', 'date_time', 'time_stamp' ]
            logger.info(f"Checking for date in column name: {col}")  # Log date check event
            time_flag = any(date in cols_info['name'].lower() for date in date_list)
            cols_info['is_time_data'] = time_flag or pd.api.types.is_datetime64_any_dtype(df[col])
            if time_flag:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass

            cols_info['type'] = str(df[col].dtype)
            cols_info['is_numeric'] = pd.api.types.is_numeric_dtype(df[col])
            cols_info['is_integer'] = pd.api.types.is_integer_dtype(df[col])
            cols_info['is_float'] = pd.api.types.is_float_dtype(df[col])
            cols_info['is_categorical'] = isinstance(df[col].dtype, pd.CategoricalDtype)
            cols_info['is_boolean'] = pd.api.types.is_bool_dtype(df[col])
            cols_info['is_text'] = pd.api.types.is_string_dtype(df[col])

            if cols_info['is_time_data']:
                is_time_data = True

            data_column_info.append(cols_info)

        # get the names of the columns that are time data
        time_columns = None
        time_columns = [cols_info['name'] for cols_info in data_column_info if cols_info['is_time_data']]
     


        return {
            "status": "ok",
            "shape": df.shape,
            "columns": data_column_info,
            "is_time_data": is_time_data,
            "time_columns_position": time_columns,
            "total_numeric_cols": len([col for col in data_column_info if col['is_numeric']]) or None,
        }, df

    except Exception as e:
        return {"error": f"Failed to configure data - {str(e)}"}

