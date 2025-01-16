# file to test the custom classes for the backend

import numpy as np

class DataNormalising:
    def __init__(self, data):
        self.data = data

    def min_max_normalize(self):
        return (self.data - np.min(self.data)) / (np.max(self.data) - np.min(self.data))
    
    def z_score_normalize(self):
        return (self.data - np.mean(self.data)) / np.std(self.data)
    
    def mean_normalize(self):
        return (self.data - np.mean(self.data)) / (np.max(self.data) - np.min(self.data))
    
    

