import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


main_folder = '/Users/matt/Desktop/optuna_params_library_sweep'

lib_sizes = []
hammings = []

for folder in os.listdir(main_folder):
    if os.path.isdir(os.path.join(main_folder, folder)):
        metrics = pd.read_csv(os.path.join(main_folder, folder, 'metrics.csv'))
        lib_sizes.append(int(folder.split('_')[2]))
        hammings.append(metrics['Best Hamming'].max())

plt.figure(figsize=(10, 5))
plt.scatter(lib_sizes, hammings)
plt.xlabel('Library Size', fontsize=18)
plt.ylabel('Best Hamming Distance', fontsize=18)
plt.show()
