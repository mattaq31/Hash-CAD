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
    print(new_sequence_energy_dict.keys())

    # Load the dictionaries from the saved pickle files
    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    # Load the statistics dictionary
    with open('stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    # Define your parameters
    f1 = 2.5
    f3 = 0.25
    f2 = 6.0

    # Calculate the required values
    max_on = stat_dict['max_on']
    min_on = stat_dict['mean_on'] - f2 * stat_dict['std_on']

    min_extrem_off = stat_dict['mean_off'] - f1 * stat_dict['std_off']
    print(min_extrem_off)
    min_mean_off = stat_dict['mean_off'] - f3 * stat_dict['std_off']
    print(min_mean_off)

    meanse = np.mean(np.array(list(new_sequence_energy_dict.values())))
    print('means for comparison:')
    print (meanse)
    print(stat_dict['mean_off'] )

    # Save the first plot as a PDF with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")  # Unique timestamp

    # Extract the energies from both dictionaries
    old_energies = list(handle_energy_dict.values())
    new_energies = list(new_sequence_energy_dict.values())

    # Create arbitrary indices for x-axis
    x_old = np.arange(len(old_energies))  # Indices for old sequences
    x_new = np.arange(len(new_energies)) + len(x_old) + 1  # Shift indices for new sequences

    # Create the scatter plot for old and new energies
    # Add horizontal lines
    plt.axhline(y=max_on, color='green', linestyle='--', label='Max On')
    plt.scatter(x_old, old_energies, color='blue', label='Old Handle Energies')
    plt.scatter(x_new, new_energies, color='green', label='New Sequence Energies')

    # Add labels and title
    plt.xlabel('Arbitrary Index')
    plt.ylabel('Energy')
    plt.title('old and new on-target energies')

    # Add legend to differentiate between the two sets
    plt.legend()

    # Save the first plot as a PDF
    plt.savefig('ontarget_energies.pdf')

    # Show the plot
    plt.show()

    # Load sequences from the dictionaries or generate them (if needed)
    newsequences = list(new_sequence_energy_dict.keys())  # New sequences as keys from new_sequence_energy_dict
    oldset = list(handle_energy_dict.keys())  # Old sequences as keys from handle_energy_dict


    print('means for comparison in order new self, new cross, old self:')


    # Perform analysis using the loaded sequences
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
    detla = 40
    x_old = np.arange(len(old_self_off_energies))  # For old_self_off_energies
    x_new = np.arange(len(new_self_off_energies)) + len(old_self_off_energies) + detla  # Shift x-axis for new_self_off_energies
    x_cross = np.arange(len(new_cross_old_off_energies)) + len(x_new) + len(old_self_off_energies)+ detla + detla # Shift x-axis for new_cross_old_off_energies

    # Create the scatter plot for the self and cross validation energies
    plt.figure(figsize=(8, 6))  # Create a new figure


    plt.axhline(y=min_extrem_off, color='blue', linestyle='--', label='Min Extrem Off')
    plt.axhline(y=min_mean_off, color='purple', linestyle='--', label='Min Mean Off')


    plt.scatter(x_new, new_self_off_energies, color='blue', label='New Self Energies')
    plt.scatter(x_old, old_self_off_energies, color='green', label='Old Self Energies')
    plt.scatter(x_cross, new_cross_old_off_energies, color='red', label='New Cross Old Energies')

    # Add labels and title for the second plot
    plt.xlabel('Arbitrary Index')
    plt.ylabel('Energy')
    plt.title('Off_target energies')
    plt.legend()

    # Save the second plot as a PDF
    plt.savefig('Offtarget.pdf')

    # Show the second plot
    plt.show()
