import matplotlib.pyplot as plt
import numpy as np
from Energy_computation_functions import *

if __name__ == '__main__':
    # Load the flipped sequences text file/Users/katzi/Documents/katzi_code/nupack_scripting/_flipped.txt
    name = 'TT_no_crosscheck96to104_64_sequence_pairs'
    flipped_file = name + '_flipped.txt'

    with open(flipped_file, 'r') as f:
        sequence_pairs = [line.strip().split('\t') for line in f.readlines()]

    # Extract the handles (first column) for analysis
    handles = [pair[0] for pair in sequence_pairs]

    try:
        with open('min_extrem_off.txt', 'r') as f:
            min_extrem_off = float(f.read())
    except:
        min_extrem_off = -8.5

    # Generate sequence energies
    new_sequences_off = selfvalidate(handles, Use_Library=False)
    new_sequence_on = np.array(list(new_sequences_off['handle_handle_energies'].flatten()))

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
    bins_combined = np.linspace(-12, -3, Ibims)

    # Compute histograms for the data within the specified range
    combined_off_counts, _ = np.histogram(combined_off, bins=bins_combined, density=True)
    new_sequence_on_combined_counts, _ = np.histogram(new_sequence_on_flat, bins=bins_combined, density=True)

    hh_counts, _ = np.histogram(hh, bins=bins_combined, density=True)
    hah_counts, _ = np.histogram(hah, bins=bins_combined, density=True)
    ahah_counts, _ = np.histogram(ahah, bins=bins_combined, density=True)

    # Calculate mean and standard deviation for combined off-target and on-target binders
    mean_combined_off = np.mean(combined_off)
    std_combined_off = np.std(combined_off)
    mean_on = np.mean(new_sequence_on_flat)
    std_on = np.std(new_sequence_on_flat)

    # Plot individual histograms
    plt.figure(figsize=(12, 6))
    plt.bar(bins_combined[:-1], hh_counts, width=bins_combined[1] - bins_combined[0], label='Handle-Handle', alpha=0.7, edgecolor='black')
    plt.xlabel('Binding Energy (kcal/mol)', fontsize=14)
    plt.ylabel('Probability Density', fontsize=14)
    plt.title('Handle-Handle Binding Energies', fontsize=16)
    plt.legend(fontsize=12)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.bar(bins_combined[:-1], hah_counts, width=bins_combined[1] - bins_combined[0], label='Antihandle-Handle', alpha=0.7, edgecolor='black')
    plt.xlabel('Binding Energy (kcal/mol)', fontsize=14)
    plt.ylabel('Probability Density', fontsize=14)
    plt.title('Antihandle-Handle Binding Energies', fontsize=16)
    plt.legend(fontsize=12)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.bar(bins_combined[:-1], ahah_counts, width=bins_combined[1] - bins_combined[0], label='Antihandle-Antihandle', alpha=0.7, edgecolor='black')
    plt.xlabel('Binding Energy (kcal/mol)', fontsize=14)
    plt.ylabel('Probability Density', fontsize=14)
    plt.title('Antihandle-Antihandle Binding Energies', fontsize=16)
    plt.legend(fontsize=12)
    plt.show()


