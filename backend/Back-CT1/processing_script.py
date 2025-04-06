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
        

        # drop the first column (assumed to be ID or index)
        logger.info(f"Initial DataFrame shape: {df.shape}")  # Log initial DataFrame shape
        df.drop(df.columns[0], axis=1, inplace=True)
        logger.info(f"DataFrame shape after dropping first column: {df.shape}")  # Log DataFrame shape after dropping first column

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
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    pass
                else:
                    logger.info(f"Column {col} is flagged as time data based on name")  # Log time flag event
                    # number of rows in the column
                    num_rows = len(df[col])
                    logger.info(f"Number of rows in column {col}: {num_rows}")  # Log number of rows in column
                    try:
                        # regex to check for time format - remove any extra digits after 6 decimal places top keep all times consistent 
                        # Initital find for this potential error was from this https://stackoverflow.com/questions/43190950/serializing-datetime-with-fraction-of-seconds-inconsistency-net 
                        # https://stackoverflow.com/questions/5476065/how-to-truncate-the-time-on-a-datetime-object - datetime objects not truncatable
                        # Cant operate on datetime objects so convert to string first and the fix is to use regex to find the decimal point and then check for 6 digits after it - make all points consistent to allow 
                        # pd.to_datetime to work correctly


                        # r'(?<!\.\d{6})$' - look for a decimal point not followed by 6 digits at the end of the string
                        # convert to string 
                        # string replace 
                        # find pattern with a negative lookbehind to see if decimal point is not followed by 6 digits
                        # if pattern is true - add .000000 
                        df[col] = df[col].astype(str).str.replace(r'(?<!\.\d{6})$', '.000000', regex=True)

                        # simiar here use string replace 
                        # find pattern of decimal point - takes first 6 digits after decimal point 
                        # replace with 6 digits only - removes extra digits
                        # match '.' then find 6 digits and replace with 6 digits only 
                        df[col] = df[col].str.replace(r'(\.\d{6})\d+', r'\1', regex=True)

                        # Convert to datetime
                        df[col] = pd.to_datetime(df[col], errors='coerce')

                        # Check for NaT values after conversion
                        na_rows = df[df[col].isna()]
                        if not na_rows.empty:
                            logger.info(f"First 5 rows with NaT in '{col}': {na_rows.head(5)}")
                        else:
                            logger.info(f"No NaT values found in '{col}' column.")
                        
                    except Exception as e:
                        logger.error(f"Failed to convert column {col} to datetime: {e}")

            logger.info(f"col has this many rows: {len(df[col])}")  # Log number of rows in column
            time_flag = None  # reset flag for next column
            cols_info['type'] = str(df[col].dtype)
            cols_info['is_numeric'] = pd.api.types.is_numeric_dtype(df[col])
            cols_info['is_integer'] = pd.api.types.is_integer_dtype(df[col])
            cols_info['is_float'] = pd.api.types.is_float_dtype(df[col])
            cols_info['is_categorical'] = isinstance(df[col].dtype, pd.CategoricalDtype)
            cols_info['is_boolean'] = pd.api.types.is_bool_dtype(df[col])
            cols_info['is_text'] = pd.api.types.is_string_dtype(df[col])

            if cols_info['is_time_data'] == True:
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

