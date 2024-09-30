import os
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np


main_folder = '/Users/matt/Desktop/experiment_folders'
cmap = matplotlib.colormaps['autumn']
qual_map = matplotlib.cm.get_cmap('tab20')

exp_folder = os.path.join(main_folder, 'mutation_vs_evo_pop_sweep')
plot_file = os.path.join(exp_folder, f'summary_plot.png')

experiments = [f for f in os.listdir(exp_folder) if os.path.isdir(os.path.join(exp_folder, f))]
v1s = [float(e.split('_')[2]) for e in experiments]
v2s = [int(e.split('_')[5]) for e in experiments]
v1_order = sorted(list(set(v1s)))
v2_order = sorted(list(set(v2s)))
experiments = [os.path.join(exp_folder, e) for e in experiments]
fig, axs = plt.subplots(len(v1_order), len(v2_order), figsize=(20, 20))

for exp, v1, v2 in zip(experiments, v1s, v2s):
    if os.path.exists(os.path.join(exp, 'metrics.csv')):
        metrics = pd.read_csv(os.path.join(exp, 'metrics.csv'))
        # Adding plots for each dataset with different markers and colors
        sns.lineplot(data=metrics, x='Generation',
                     y='Corresponding Physics-Based Score', color=qual_map.colors[int(metrics['Best Hamming'].max())-25],
                     ax=axs[v1_order.index(v1), v2_order.index(v2)],
                     label=f'{v1:.2f} mutation rate, {v2} population size, total generations: {len(metrics)}')
        axs[v1_order.index(v1), v2_order.index(v2)].set_yscale('log')
    break
plt.tight_layout()
for ax in axs.flatten():
    ax.axis('off')

plt.savefig(plot_file, dpi=300)
plt.show()
plt.close(fig)
