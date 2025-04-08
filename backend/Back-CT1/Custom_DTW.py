"""
This file contains the implementation of the Dynamic Time Warping (DTW) algorithm. 
This used two methods, a custom implementation and a library implementation.

This file is used as an import for the handling.py file.

"""

import numpy as np
from time import time
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def dtw_custom() -> float:

    pass 


def dtw_library() -> float:


    pass


"""

This file contains the implementation of the Dynamic Time Warping (DTW) algorithm that was 
used as a test during the specification of the project.
Kept here for documentation purposes.

"""


# test DTW implementation

# Script setup to run incremental tests on increasing number of points



#data = pd.read_csv('Real_data_1.csv', delimiter=',', parse_dates=['T1'], index_col='T1')

time_list = []
points_list = []
points_list = []
index = 1

def min_max_normalize(data):
    try:
        return (data - np.min(data)) / (np.max(data) - np.min(data))
    
    except Exception as e:
        return str(e)

def get_info(data):
    logger.info("Getting data info...")
    for col_info in data['columns']:
        if col_info['is_numeric']:
            return col_info['name']

    logger.warning("No numeric columns found.")
    return None, None


#print(data.head())

def dtw_custom(df_1, data_info_1, df_2, data_info_2) -> float:
    logger.info("Starting DTW custom function")  # Log function start
        
    start_time = time()
    # extract the data from both dataframes in line with the data info provided 
    """
        return {
            "status": "ok",
            "shape": df.shape,
            "columns": data_column_info,
            "is_time_data": is_time_data,
            "time_columns_position": time_columns,
            "total_numeric_cols": len([col for col in data_column_info if col['is_numeric']]) or None,
        }, df
    
        data_column_info has data like 
            cols_info['type'] = str(df[col].dtype)
            cols_info['is_numeric'] = pd.api.types.is_numeric_dtype(df[col])
            cols_info['is_integer'] = pd.api.types.is_integer_dtype(df[col])
            cols_info['is_float'] = pd.api.types.is_float_dtype(df[col])
            cols_info['is_categorical'] = isinstance(df[col].dtype, pd.CategoricalDtype)
            cols_info['is_boolean'] = pd.api.types.is_bool_dtype(df[col])
            cols_info['is_text'] = pd.api.types.is_string_dtype(df[col])
    """

    # go through the data info dict for data_column_info dict and find numeric cols - names 
    # and their positions in the dataframe
    # this is a list of dicts with the column name and position in the dataframe

    d1_name = get_info(data_info_1)
    d2_name = get_info(data_info_2)

    logger.info(f"Data 1 column name: {d1_name}")  # Log column name and position
    logger.info(f"Data 2 column name: {d2_name}")  # Log column name and position

    parameter_data = df_1[d1_name].values
    post_change_data = df_2[d2_name].values


    if isinstance(parameter_data, pd.Series):
        parameter_data = parameter_data.values
    if isinstance(post_change_data, pd.Series):
        post_change_data = post_change_data.values
    
    


    try:

        baseline_data_norm = min_max_normalize(parameter_data)

        post_change_data_norm = min_max_normalize(post_change_data)

        if isinstance(baseline_data_norm, str) or isinstance(post_change_data_norm, str):
            logger.error("Normalisation failed: error returned")
            return None


    except Exception as e:
        logger.error(f"Error in normalization: {e}")
        return None

    logger.info("Normalisation complete")  # Log normalisation completion

    # Initialise
    n = len(baseline_data_norm)
    m = len(post_change_data_norm)
    cost_matrix = np.zeros((n, m))

    for i in range(n):
        for j in range(m):
            cost_matrix[i, j] = np.abs(baseline_data_norm[i] - post_change_data_norm[j])
    

    cumulative_cost_matrix = cost_matrix.copy()
    # we want D_0,i and D_0,j to be = 
    cumulative_cost_matrix[1:, 0] = np.inf
    cumulative_cost_matrix[0, 1:] = np.inf


    cumulative_cost_matrix[0, 0] = cost_matrix[0, 0]

    logger.info("Cumulative cost matrix initialised")  # Log cumulative cost matrix initialisation

    for i in range(1, n):
        for j in range(1, m):
            cumulative_cost_matrix[i, j] = cost_matrix[i, j] + min(
                cumulative_cost_matrix[i-1, j],
                cumulative_cost_matrix[i, j-1],
                cumulative_cost_matrix[i-1, j-1]
            )

    # right corner
    i, j = n - 1, m - 1
    path = [(i, j)]

    #  optimal path
    while i > 0 or j > 0:
        if i == 0:
            j -= 1
        elif j == 0:
            i -= 1
        else:
        # find min
            min_index = np.argmin([cumulative_cost_matrix[i-1, j], cumulative_cost_matrix[i, j-1], cumulative_cost_matrix[i-1, j-1]])
            if min_index == 0:
                i -= 1
            elif min_index == 1:
                j -= 1
            else:
                i -= 1
                j -= 1
        path.append((i, j))

    logger.info("Optimal path found")  # Log optimal path finding

    path = path[::-1] # reverse the path

    dtw_distance = cumulative_cost_matrix[-1, -1]
    logger.info(f"DTW distance: {dtw_distance}")  # Log DTW distance


    # return dataframe with the DTW distance and the path
    dtw_df = pd.DataFrame({
        'Baseline Data Index': [i for i, j in path],
        'Post-Change Data Index': [j for i, j in path],
        'Cumulative Cost': [cumulative_cost_matrix[i, j] for i, j in path]
    })
    dtw_df['DTW Distance'] = dtw_distance
    dtw_df['Path'] = path

    end_time = time()
    logger.info(f"Time taken: {end_time - start_time}")  # Log time taken

    return dtw_df 




    """   

    print("Time taken: ", end_time - start_time)
    time_list.append(end_time - start_time)
    #points_list.append(POINTS)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    ax1.plot(time_data[100:350], baseline_data_norm[100:350], label="Baseline (Pre-Change)")
    ax1.plot(time_data[100:350], post_change_data_norm[100:350], label="Post-Change")
    ax1.legend()
    ax1.set_title("Baseline vs Post-Change Data (First 250 Values)")
    ax1.set_xlabel("Data Index")
    ax1.set_ylabel("Process Parameter")
    ax1.xaxis.set_major_locator(plt.MaxNLocator(5))  # Limit the number of x-axis labels to 10

    ax2.imshow(cumulative_cost_matrix, origin='lower', cmap='viridis', aspect='auto')
    ax2.plot(*zip(*path), color='red')  
    ax2.set_title("Cumulative Cost Matrix with Optimal Path")
    ax2.set_xlabel("Post-Change Data Index")
    ax2.set_ylabel("Baseline Data Index")
    fig.colorbar(ax2.imshow(cumulative_cost_matrix, origin='lower', cmap='viridis', aspect='auto'), ax=ax2, label="Cumulative Cost")
    plt.tight_layout()
    plt.show()
    index += 1
    """
