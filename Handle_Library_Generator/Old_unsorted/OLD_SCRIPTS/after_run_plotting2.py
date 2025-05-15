import pickle
import matplotlib.pyplot as plt
import numpy as np
from Energy_computation_functions import *
import time

if __name__ == '__main__':
    # Load the old handle sequences and their energies
    with open('handle_energy_dict.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    # Load the new sequence energy dictionary
    with open('non_vertex_cover_energy_dict.pkl', 'rb') as f:
        new_sequence_energy_dict = pickle.load(f)

    # Write the keys to a text file
    with open('new_handles.txt', 'w') as output_file:
        for key in new_sequence_energy_dict.keys():
            output_file.write(f"{key}\n")  # Write each key on a new line

    print(new_sequence_energy_dict.keys())

    # Load the dictionaries from the saved pickle files
    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    # Load the statistics dictionary
    with open('stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    # Define your parameters
    f1 = 2.475
    f3 = 0.5
    f2 = 6.0

    # Calculate the required values
    max_on = stat_dict['max_on']
    min_on = stat_dict['mean_on'] - f2 * stat_dict['std_on']
    min_extrem_off = stat_dict['mean_off'] - f1 * stat_dict['std_off']
    min_mean_off = stat_dict['mean_off'] - f3 * stat_dict['std_off']

    meanse = np.mean(np.array(list(new_sequence_energy_dict.values())))
    print('means for comparison of newseq:')
    print(meanse)

    meansehnad = np.mean(np.array(list(handle_energy_dict.values())))
    print('means for comparison of oldseq:')
    print(meansehnad)
    #print(stat_dict['mean_off'])

    # Extract the energies from both dictionaries
    old_energies = list(handle_energy_dict.values())
    new_energies = list(new_sequence_energy_dict.values())
    detla = 99
    # Create arbitrary indices for x-axis
    x_old = np.arange(len(old_energies))  # Indices for old sequences
    x_new = np.arange(len(new_energies)) + len(x_old) + detla  # Shift indices for new sequences

    # Load sequences from the dictionaries or generate them (if needed)
    newsequences = list(new_sequence_energy_dict.keys())  # New sequences as keys from new_sequence_energy_dict
    oldset = list(handle_energy_dict.keys())  # Old sequences as keys from handle_energy_dict

    # Perform analysis using the loaded sequences
    print('means for comparison in order new self, new cross, old self:')

    selfnew = selfvalidate(newsequences)
    new_self_off_energies = selfnew['all_energies']
    print(np.mean(new_self_off_energies))

    crossnewold = crossvalidate(newsequences, oldset)
    new_cross_old_off_energies = crossnewold['all_energies']
    print(np.mean(new_cross_old_off_energies))

    selfold = selfvalidate(oldset)
    old_self_off_energies = selfold['all_energies']
    print(np.mean(old_self_off_energies))

    # Create arbitrary indices for the x-axis, ensuring no overlap

    x_self_new = np.arange(len(new_self_off_energies)) #+ detla +len(old_energies) + detla+ len(new_energies)
    x_self_old = len(new_self_off_energies)+ detla + np.arange(len(old_self_off_energies))
    x_cross = len(new_self_off_energies)+ detla + len(old_self_off_energies)+ detla + np.arange(len(new_cross_old_off_energies))

    # Create a single plot for all data
    plt.figure(figsize=(10, 8))

    # Plot old and new energies with different colors
    plt.axhline(y=max_on, color='darkgreen', linestyle='--', label='Max On')
    plt.scatter(x_old, old_energies, color='darkblue', label='Old Handle Energies')
    plt.scatter(x_new, new_energies, color='darkorange', label='New Sequence Energies')

    # Plot self and cross-validation off-target energies with different colors
    plt.axhline(y=min_extrem_off, color='darkblue', linestyle='--', label='Min Extrem Off')
    plt.axhline(y=min_mean_off, color='purple', linestyle='--', label='Min Mean Off')
    plt.scatter(x_self_new, new_self_off_energies, color='darkred', label='New Self Energies')
    plt.scatter(x_self_old, old_self_off_energies, color='green', label='Old Self Energies')
    plt.scatter(x_cross, new_cross_old_off_energies, color='orange', label='New Cross Old Energies')


    # Add labels, title, and legend
    plt.xlabel('Arbitrary Index')
    plt.ylabel('Energy')
    plt.title('Old/New On-target and Off-target Energies')
    plt.legend()

    # Save the combined plot as a PDF
    plt.savefig('Combined_Energies_with_deltas_and_prints.pdf')

    # Show the combined plot
    plt.show()


