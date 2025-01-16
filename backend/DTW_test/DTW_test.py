# test DTW implementation

# Script setup to run incremental tests on increasing number of points

import numpy as np
import matplotlib.pyplot as plt
from dtw import dtw
from time import time
import pandas as pd


#data = pd.read_csv('Real_data_1.csv', delimiter=',', parse_dates=['T1'], index_col='T1')

time_list = []
points_list = []
points_list = []
index = 1

#print(data.head())

while index < 2:
    start_time = time()  
    POINTS = 1500 *(index *.25)  # Number of data points

    POINTS = int(POINTS)

    time_steps = np.linspace(0, 30, POINTS)  # X points over 30 minutes
    baseline_data = np.sin(time_steps)  # Example sine wave for baseline
    parameter_data = baseline_data
    #baseline_data_control = baseline_data

    # Generate post-change data (simulating a control change)
    post_change_data = np.sin(time_steps + 0.5) + np.random.uniform(-.15, +.15, POINTS) * np.random.uniform(-.51,.11,POINTS)  # with phase shift and noise



    #define time data as an array of 1500 points
    time_data = np.linspace(0, 30, POINTS)

    print(np.isnan(parameter_data).any())  # Check if parameter_data contains NaN
    print(np.isnan(post_change_data).any())  # Check if post_change_data contains NaN
    

    def min_max_normalize(data):
        return (data - np.min(data)) / (np.max(data) - np.min(data))
    
    baseline_data_norm = min_max_normalize(parameter_data)

    post_change_data_norm = min_max_normalize(post_change_data)



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

    path = path[::-1] # reverse the path

    dtw_distance = cumulative_cost_matrix[-1, -1]
    print("DTW Distance:", dtw_distance)

    end_time = time()

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
