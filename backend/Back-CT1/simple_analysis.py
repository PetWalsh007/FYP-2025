"""
Test Analysis script used for development

"""



import pandas as pd
import numpy as np
import json
import os
import datetime
import logging
from typing import Dict, Any



# setup_processing_logging
logger = logging.getLogger(__name__)


def daily_average(dataframe, info):
    logger.info("Starting  function")
    # take time series data nad compute the daily average over the number of days in the datapoints

    # Check if the DataFrame has a 'timestamp' column

    """
        return {
            "status": "ok",
            "shape": df.shape,
            "columns": data_column_info,
            "is_time_data": is_time_data,
            "time_columns_position": time_columns,
            "total_numeric_cols": len([col for col in data_column_info if col['is_numeric']]) or None,
        }, df
    
    
    """
    # Function accepts a dataframe and a dictionary with information about the data
    # Returns a new dataframe with differnt infomation that can be displayed in the front end
   
def daily_average(dataframe, info):
    logger.info("Starting daily_average function")
    try:
        # Get the position of the timestamp column from the info dictionary
        time_position = info.get("time_columns_position", [])
        if not time_position:
            raise ValueError("No time column position provided in info dictionary.")

        # Identify the timestamp column
        timestamp_raw = time_position[0]
        if isinstance(timestamp_raw, str):
            timestamp_col = timestamp_raw
        elif isinstance(timestamp_raw, int):
            timestamp_col = dataframe.columns[timestamp_raw]
        else:
            raise TypeError(f"Invalid type for time column reference: {type(timestamp_raw)}")

        logger.info(f"Timestamp column identified: '{timestamp_col}'")

        # Log the shape of the original DataFrame
        logger.info(f"Original DataFrame shape: {dataframe.shape}")

     
        #dataframe[timestamp_col] = dataframe[timestamp_col].astype(str).str.strip()

      
        #dataframe[timestamp_col] = pd.to_datetime(dataframe[timestamp_col], errors='coerce')

        # find and log the first rows of na values in the timestamp column
        na_rows = dataframe[dataframe[timestamp_col].isna()]
        if not na_rows.empty:
            logger.info(f"First 5 rows with NaT in '{timestamp_col}': {na_rows.head(5)}")
        else:
            logger.info(f"No NaT values found in '{timestamp_col}' column.")
            

        # Log type of the timestamp column
        logger.info(f"Timestamp column type after conversion: {dataframe[timestamp_col].dtype}")
        # Log invalid timestamps
        invalid_timestamps = dataframe[dataframe[timestamp_col].isna()]
        invalid_timestamps = dataframe[dataframe[timestamp_col].isna() | (dataframe[timestamp_col] == pd.NaT)]
        if len(invalid_timestamps) > 0:
            logger.error(f"Found {len(invalid_timestamps)} rows with invalid timestamps.")
            # Log top 5 invalid timestamps
            logger.debug(f"Invalid rows (top 5): {invalid_timestamps.head(5)}")


        # Extract the date from the timestamp column
        dataframe["date"] = dataframe[timestamp_col].dt.date

        # Get numeric column names from the info dictionary
        numeric_cols = [col["name"] for col in info.get("columns", []) if col.get("is_numeric")]
        if timestamp_col in numeric_cols:
            numeric_cols.remove(timestamp_col)  # Remove timestamp column if marked numeric

        logger.info(f"Numeric columns used for averaging: {numeric_cols}")

        # Compute daily average using groupby
        daily_avg_df = dataframe.groupby("date")[numeric_cols].mean().reset_index()

        # Log the total number of rows in the resulting DataFrame
        logger.info(f"Total rows in the daily average DataFrame: {len(daily_avg_df)}")

        return daily_avg_df

    except Exception as e:
        logger.error(f"Error in daily_average: {str(e)}")
        return pd.DataFrame({"error": [str(e)]})


   
