import pickle
import matplotlib.pyplot as plt
import numpy as np
from Energy_computation_functions import *

if __name__ == '__main__':
    # Load the new sequence energy dictionary
    name = 'TT_no_crosscheck96to104'
    #name = 'handle_energy_dict'
    #with open(name + '.pkl', 'rb') as f:
    #   new_sequence_energy_dict = pickle.load(f)

    with open(name + 'handlesxx.pkl', 'rb') as f:
        new_sequence_energy_dict = pickle.load(f)
    print(len(new_sequence_energy_dict))
    try:
        with open('min_extrem_off.txt', 'r') as f:
            min_extrem_off = float(f.read())
    except:
        min_extrem_off = -8.5

        # Generate a list of sequences from the dictionary values
    sequence_list = list(new_sequence_energy_dict.keys())

        # Generate sequence pairs (sequence and reverse complement)
    sequence_pairs = [(seq, revcom(seq)) for seq in sequence_list]

    # Define the output file name
    output_file = name +'_64_sequence_pairs.txt'

    # Write the sequence pairs to the output file
    with open(output_file, 'w') as f:
        for seq, rev_seq in sequence_pairs:
            f.write(f"{seq}\t{rev_seq}\n")

    min_on = -10.4
    min_off = -9.60
    delta = round(min_off-min_extrem_off, 2)
    # Load the dictionaries from the saved pickle files
    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    # Gather sequence energies
    new_sequences_off = selfvalidate(new_sequence_energy_dict.keys(),Use_Library=False)
    new_sequence_on = np.array(list(new_sequence_energy_dict.values()))

    # Extract energy arrays and remove zeros
    hh = new_sequences_off['handle_handle_energies'][new_sequences_off['handle_handle_energies'] != 0].flatten()
    hah = new_sequences_off['antihandle_handle_energies'][
        new_sequences_off['antihandle_handle_energies'] != 0].flatten()
    ahah = new_sequences_off['antihandle_antihandle_energies'][
        new_sequences_off['antihandle_antihandle_energies'] != 0].flatten()
    new_sequence_on_flat = new_sequence_on[new_sequence_on != 0].flatten()

    # Combine off-target energies and apply range limits
    combined_off = np.concatenate([hh, hah, ahah])
    combined_off = combined_off[(combined_off >= -12) & (combined_off <= -3)]
    new_sequence_on_flat = new_sequence_on_flat[(new_sequence_on_flat >= -12) & (new_sequence_on_flat <= -3)]

    # Define bins within the specified range
    Ibims = 90
    bins_combined = np.linspace(-12, -3,  Ibims)

    # Compute histograms for the data within the specified range
    combined_off_counts, _ = np.histogram(combined_off, bins=bins_combined, density=True)
    new_sequence_on_combined_counts, _ = np.histogram(new_sequence_on_flat, bins=bins_combined, density=True)

    # Calculate mean and standard deviation for combined off-target and on-target binders
    mean_combined_off = np.mean(combined_off)
    std_combined_off = np.std(combined_off)
    mean_on = np.mean(new_sequence_on_flat)
    std_on = np.std(new_sequence_on_flat)

    # Set up for plotting
    bar_width_combined = bins_combined[1] - bins_combined[0]
    x_combined = bins_combined[:-1]

    plt.figure(figsize=(12, 6))
    plt.bar(x_combined, combined_off_counts, width=bar_width_combined, label='Off Target', alpha=0.7,
            edgecolor='black')
    plt.bar(x_combined, new_sequence_on_combined_counts, width=bar_width_combined, label='On Target', alpha=0.7,
            edgecolor='black')

    # Add vertical lines for min_extrem_off, min_on, and min_off with labels in the legend
    plt.axvline(min_extrem_off, color='red', linestyle='--',  linewidth=2.25, label=f' cutoff ({min_extrem_off:.2f})')
    plt.axvline(min_on, color='blue', linestyle='--',   linewidth=2.25 ,label=f' cutoff ({min_on})')
    plt.axvline(min_off, color='green', linestyle='--',  linewidth=2.25, label=f' cutoff ({min_off})')

    # Set default x-axis range from -12 to -3
    plt.xlim(-12, -3)
    plt.ylim(0, 1.6)

    # Add text annotations with larger font size and transparent background to overlay the plot
    plt.text(-11.8, plt.ylim()[1] * 0.95, f'Mean:\n{mean_on:.2f} kcal/mol',
             color='black', fontsize=18, verticalalignment='top', horizontalalignment='left',
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))

    plt.text(-4.9, plt.ylim()[1] * 0.95, f'Mean:\n{mean_combined_off:.2f} kcal/mol',
             color='black', fontsize=18, verticalalignment='top', horizontalalignment='left',
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
    # Add delta text between min_off and min_on
    plt.text((min_off+min_extrem_off) / 2, plt.ylim()[1] * 0.75, f'Δ = {delta} kcal/mol',
             color='black', fontsize=18, verticalalignment='center', horizontalalignment='center',
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # Labeling with larger font sizes
    plt.xlabel('Binding Energy (kcal/mol)', fontsize=18)
    plt.ylabel('Probability Density', fontsize=18)
    plt.title('On Target vs Off Target Binding Energies', fontsize=18)

    # Legend with larger font size
    plt.legend(loc='center right', fontsize=15)

    # Show plot
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.savefig(name + "_set_plot.png", format="png", dpi=300)
    plt.show()







    # Plot individual components
    for component, label in zip([hh, hah, ahah], ['HH', 'HAH', 'AHAH']):
        component = component[(component >= -12) & (component <= -3)]
        counts, _ = np.histogram(component, bins=bins_combined, density=True)
        plt.figure(figsize=(12, 6))
        plt.bar(x_combined, new_sequence_on_combined_counts, width=bar_width_combined, label='On Target', alpha=0.7, edgecolor='black')
        plt.bar(bins_combined[:-1], counts, width=bins_combined[1] - bins_combined[0], label=label, alpha=0.7, edgecolor='black')
        plt.axvline(min_extrem_off, color='red', linestyle='--', linewidth=2.25, label=f'cutoff ({min_extrem_off:.2f})')
        plt.axvline(min_on, color='blue', linestyle='--', linewidth=2.25, label=f'cutoff ({min_on})')
        plt.axvline(min_off, color='green', linestyle='--', linewidth=2.25, label=f'cutoff ({min_off})')
        plt.xlabel('Binding Energy (kcal/mol)', fontsize=18)
        plt.ylabel('Probability Density', fontsize=18)
        plt.title(f'{label} Binding Energies', fontsize=18)
        plt.legend(loc='center right', fontsize=15)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.savefig(name + f"_{label}_plot.png", format="png", dpi=300)
        plt.show()

    # Combine off-target and on-target energies for overall plot
    combined_off_counts, _ = np.histogram(combined_off, bins=bins_combined, density=True)
    new_sequence_on_combined_counts, _ = np.histogram(new_sequence_on_flat, bins=bins_combined, density=True)

    plt.figure(figsize=(12, 6))
    plt.bar(bins_combined[:-1], combined_off_counts, width=bins_combined[1] - bins_combined[0], label='Off Target', alpha=0.7, edgecolor='black')
    plt.bar(bins_combined[:-1], new_sequence_on_combined_counts, width=bins_combined[1] - bins_combined[0], label='On Target', alpha=0.7, edgecolor='black')
    plt.axvline(min_extrem_off, color='red', linestyle='--', linewidth=2.25, label=f'cutoff ({min_extrem_off:.2f})')
    plt.axvline(min_on, color='blue', linestyle='--', linewidth=2.25, label=f'cutoff ({min_on})')
    plt.axvline(min_off, color='green', linestyle='--', linewidth=2.25, label=f'cutoff ({min_off})')
    plt.xlabel('Binding Energy (kcal/mol)', fontsize=18)
    plt.ylabel('Probability Density', fontsize=18)
    plt.title('On Target vs Off Target Binding Energies', fontsize=18)
    plt.legend(loc='center right', fontsize=15)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.savefig(name + "_set_plot.png", format="png", dpi=300)
    plt.show()



















    with open(name + 'cross.pkl', 'rb') as f:
        crossdick = pickle.load(f)

    # Extract the 2D arrays and flatten, removing zeros
    hh = np.array(crossdick['handle_handle_energies']).flatten()
    hah = np.array(crossdick['antihandle_handle_energies']).flatten()
    ahah = np.array(crossdick['antihandle_antihandle_energies']).flatten()

    # Remove zeros from each array
    hh = hh[hh != 0]
    hah = hah[hah != 0]
    ahah = ahah[ahah != 0]
    combined_off = np.concatenate([hh, hah, ahah])

    # Calculate mean and standard deviation for each dataset
    mean_hh, std_hh = np.mean(hh), np.std(hh)
    mean_hah, std_hah = np.mean(hah), np.std(hah)
    mean_ahah, std_ahah = np.mean(ahah), np.std(ahah)



    with open(name + '.pkl', 'rb') as f:
        new_sequence_energy_dict = pickle.load(f)
    print(len(new_sequence_energy_dict))
    new_sequence_on = np.array(list(new_sequence_energy_dict.values()))
    new_sequence_on_flat = new_sequence_on[new_sequence_on != 0].flatten()

    combined_off = combined_off[(combined_off >= -12) & (combined_off <= -3)]
    new_sequence_on_flat = new_sequence_on_flat[(new_sequence_on_flat >= -12) & (new_sequence_on_flat <= -3)]

    # Define bins within the specified range

    bins_combined = np.linspace(-12, -3,  Ibims)

    # Compute histograms for the data within the specified range
    combined_off_counts, _ = np.histogram(combined_off, bins=bins_combined, density=True)
    new_sequence_on_combined_counts, _ = np.histogram(new_sequence_on_flat, bins=bins_combined, density=True)

    # Calculate mean and standard deviation for combined off-target and on-target binders
    mean_combined_off = np.mean(combined_off)
    std_combined_off = np.std(combined_off)
    mean_on = np.mean(new_sequence_on_flat)
    std_on = np.std(new_sequence_on_flat)

    # Set up for plotting
    bar_width_combined = bins_combined[1] - bins_combined[0]
    x_combined = bins_combined[:-1]

    plt.figure(figsize=(12, 6))
    plt.bar(x_combined, combined_off_counts, width=bar_width_combined, label='Off Target', alpha=0.7,
            edgecolor='black')
    plt.bar(x_combined, new_sequence_on_combined_counts, width=bar_width_combined, label='On Target', alpha=0.7,
            edgecolor='black')

    # Add vertical lines for min_extrem_off, min_on, and min_off with labels in the legend
    plt.axvline(min_extrem_off, color='red', linestyle='--',  linewidth=2.25, label=f' cutoff ({min_extrem_off:.2f})')
    plt.axvline(min_on, color='blue', linestyle='--',   linewidth=2.25 ,label=f' cutoff ({min_on})')
    plt.axvline(min_off, color='green', linestyle='--',  linewidth=2.25, label=f' cutoff ({min_off})')

    # Set default x-axis range from -12 to -3
    plt.xlim(-12, -3)
    plt.ylim(0, 1.6)

    # Add text annotations with larger font size and transparent background to overlay the plot
    plt.text(-11.8, plt.ylim()[1] * 0.95, f'Mean:\n{mean_on:.2f} kcal/mol',
             color='black', fontsize=18, verticalalignment='top', horizontalalignment='left',
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))

    plt.text(-4.9, plt.ylim()[1] * 0.95, f'Mean:\n{mean_combined_off:.2f} kcal/mol',
             color='black', fontsize=18, verticalalignment='top', horizontalalignment='left',
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
    # Add delta text between min_off and min_on
    plt.text((min_off+min_extrem_off) / 2, plt.ylim()[1] * 0.75, f'Δ = {delta} kcal/mol',
             color='black', fontsize=18, verticalalignment='center', horizontalalignment='center',
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # Labeling with larger font sizes
    plt.xlabel('Binding Energy (kcal/mol)', fontsize=18)
    plt.ylabel('Probability Density', fontsize=18)
    plt.title('On Target vs Off Target Binding Energies', fontsize=18)

    # Legend with larger font size
    plt.legend(loc='center right', fontsize=15)

    # Show plot
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.savefig(name +'_pool_plot.png', format="png", dpi=300)
    plt.show()




