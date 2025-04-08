import os
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np

sns.set_style('whitegrid')

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

fig, axs = plt.subplots(2, 1, figsize=(10, 10))
fig_64, axs_64 = plt.subplots(2, 1, figsize=(10, 10))
fig_32, axs_32 = plt.subplots(2, 1, figsize=(10, 10))

for ind, (exp, name) in enumerate(zip(experiments, names)):
    if os.path.exists(os.path.join(exp, 'metrics.csv')):
        metrics = pd.read_csv(os.path.join(exp, 'metrics.csv'))
        plot_axs = [axs]
        if '32' in name:
            plot_axs.append(axs_32)
        elif '64' in name:
            plot_axs.append(axs_64)

        for ax in plot_axs:
            # Adding plots for each dataset with different markers and colors
            sns.lineplot(data=metrics, x='Generation',
                         y='Best Physics-Based Score', color=qual_map.colors[ind],
                         ax=ax[0],
                         label=name)
            ax[0].set_yscale('log')

            sns.lineplot(data=metrics, x='Generation',
                         y='Corresponding Hamming Distance', color=qual_map.colors[ind],
                         ax=ax[1],
                         label=name)

fig.tight_layout()
fig.savefig('/Users/matt/Desktop/comp_fig.pdf', dpi=300)

fig_32.tight_lfig_64.tight_layout()
fig_64.savefig('/Users/matt/Desktop/comp_fig_64.pdf', dpi=300)
plt.tight_layout()
fig_32.savefig('/Users/matt/Desktop/comp_fig_32.pdf', dpi=300)

# plt.show()


