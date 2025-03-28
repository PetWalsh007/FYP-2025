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

    dataframe2 = pd.DataFrame()


    return dataframe2

   
