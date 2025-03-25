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



# endpoints here to be defined via paramarters passed to condigure_data

def configure_data(raw_data):

    data_dict = _desc_data(raw_data)

    dataframe = data_dict.get("df")

    pass



def _desc_data(raw_data):
    
    try:
        # Convert raw data to DataFrame
        df = pd.read_json(raw_data)

        data_column_info = []
        is_time_data = False  # Will be set True if *any* col is time-like

        for col in df.columns:
            cols_info = {}  # new dict per column!

            cols_info['name'] = col
            cols_info['type'] = str(df[col].dtype)
            cols_info['is_time_data'] = pd.api.types.is_datetime64_any_dtype(df[col])
            cols_info['is_numeric'] = pd.api.types.is_numeric_dtype(df[col])
            cols_info['is_integer'] = pd.api.types.is_integer_dtype(df[col])
            cols_info['is_float'] = pd.api.types.is_float_dtype(df[col])
            cols_info['is_categorical'] = pd.api.types.is_categorical_dtype(df[col])
            cols_info['is_boolean'] = pd.api.types.is_bool_dtype(df[col])
            cols_info['is_text'] = pd.api.types.is_string_dtype(df[col])

            if cols_info['is_time_data']:
                is_time_data = True

            data_column_info.append(cols_info)


     


        return {
            "status": "ok",
            "shape": df.shape,
            "columns": data_column_info,
            "is_time_data": is_time_data,
            "total_numeric_cols": len([col for col in data_column_info if col['is_numeric']]),
            "df": df  # return converted df 
        }

    except Exception as e:
        return {"error": f"Failed to configure data - {str(e)}"}

