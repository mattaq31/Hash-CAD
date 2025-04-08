import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os

exp_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization/testing_mutation_memory/experiments'
cmap = matplotlib.colormaps['autumn']
qual_map = matplotlib.cm.get_cmap('tab20')

plot_file = os.path.join(exp_folder, f'summary_plot.png')

experiments = [f for f in os.listdir(exp_folder) if os.path.isdir(os.path.join(exp_folder, f))]

names = [e.split('basic_square_')[-1].split('_')[0] + '_' + e.split('memory_')[-1] for e in experiments]

for ind, n in enumerate(names):
    if 'basic_square' in n:
        names[ind] = 'Pre-Split-Handle-Bugfix'

experiments = [os.path.join(exp_folder, e) for e in experiments]


for ind, (exp, name) in enumerate(zip(experiments, names)):
    # find all files starting with best_ in the experiment directory
    handle_array_files = [f for f in os.listdir(exp) if f.startswith('best_') and f.endswith('.xlsx')]
    # sort them by the integer at the end of the filename
    handle_array_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    heatmap_tracker = np.zeros((32, 32))


    for hf_ind, hf in enumerate(handle_array_files):
        # reads in design here
        handle_array = pd.read_excel(os.path.join(exp, hf), sheet_name=None, header=None)['handle_interface_1'].to_numpy()
        if hf_ind > 0:
            # generate a boolean map - true wherever an array element has changed
            mutations = np.abs(handle_array_prev - handle_array)
            mutations[mutations > 0] = 1  # set all non-zero differences to 1
            heatmap_tracker += mutations
        handle_array_prev = handle_array.copy()
        if hf_ind > 1000:
            break

    # plot the heatmap
    plt.figure(figsize=(8, 6))
    plt.imshow(heatmap_tracker, cmap='hot', interpolation='nearest')
    plt.colorbar(label='Number of Changes')
    plt.title(f'Heatmap of Changes for {name}')
    plt.tight_layout()
    plt.savefig(os.path.join(exp_folder, f'mutation_heatmap_{name}.png'), dpi=300)

