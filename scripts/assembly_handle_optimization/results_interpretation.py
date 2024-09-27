import os
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import matplotlib.ticker as ticker
import seaborn as sns

groups = ['evolution_population', 'generational_survivors', 'mutation_rate', 'mutation_types']
main_folder = '/Users/matt/Desktop/experiment_folders'
cmap = matplotlib.colormaps['autumn']

for group in groups:
    if group == 'mutation_types': # TODO: need to handle these separately, as they are a different datatype (probably best to read configs directly instead of folder names)
        continue
    exp_folder = os.path.join(main_folder, group)
    plot_file = os.path.join(exp_folder, f'summary_plot.png')
    experiments = [f for f in os.listdir(exp_folder) if os.path.isdir(os.path.join(exp_folder, f))]
    values = [float(e.split('_')[2]) for e in experiments]
    norm = plt.Normalize(min(values), max(values))

    experiments = [os.path.join(exp_folder, e) for e in experiments]

    fig, axs = plt.subplots(4, 1, figsize=(10, 15))
    for exp, val in zip(experiments, values):
        if os.path.exists(os.path.join(exp, 'metrics.csv')):
            metrics = pd.read_csv(os.path.join(exp, 'metrics.csv'))
            # Adding plots for each dataset with different markers and colors
            for ax, column, title in zip(axs.flatten(), ['Best Hamming',
                                                        'Corresponding Physics-Based Score',
                                                        'Corresponding Duplicate Risk Score',
                                                        'Hamming Compute Time'],
                                         ['Candidate with Best Hamming Distance',
                                          'Corresponding Physics-Based Partition Score',
                                          'Corresponding Duplication Risk Score',
                                          'Hamming Compute Time (s)']):

                sns.lineplot(data=metrics, x='Generation', color=cmap(norm(val)),
                                y=column, ax=ax, label=str(val), legend=False)

    # Create a colorbar to show the mapping of parameter values to colors
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Required for ScalarMappable
    cbar = fig.colorbar(sm, ax=axs[-1], orientation='horizontal', label=group)

    axs[1].set_yscale('log')
    plt.tight_layout()

    plt.savefig(plot_file, dpi=300)
    plt.close(fig)


