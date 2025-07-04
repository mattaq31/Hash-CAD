from sequence_picking_tools import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import time






if __name__ == "__main__":
    # open the old handle sequences as dictionary
    with open('handle_energy_dict.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    # Load the dictionary with all the available sequences new_sequence_toto_test_energy_dict.pkl
    #with open('sequence_energy_dict.pkl', 'rb') as f:
    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    depleted_sequence_dict= sequence_energy_dict.copy()
    # Load the statistics
    with open('stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    f1 = 4.5
    f3 = 4.25
    f2 =6.0

    max_on =stat_dict['max_on']
    print(max_on)
    min_on = stat_dict['mean_on']- f2 * stat_dict['std_on']
    print(min_on)

    min_extrem_off = max_on #stat_dict['mean_off']- f1*stat_dict['std_off']
    print(min_extrem_off)
    min_mean_off = stat_dict['mean_off']-f3*stat_dict['std_off']
    print(min_mean_off)


    remove_sequences_outside_range(depleted_sequence_dict, min_on, max_on)

    newsequences= []
    oldset = list(handle_energy_dict.keys())

    while len(depleted_sequence_dict) > 0 and len(newsequences) < 64:
        print(f"Found {len(newsequences)} sequences, {len(depleted_sequence_dict)} sequences to go.")

        new_candidate = pick_and_remove_sequence(depleted_sequence_dict)

        fullset =  newsequences #+ oldset

        if validate_new_seq(new_candidate, fullset, min_extrem_off, min_mean_off) == True:
        #if validate_new_seq(new_candidate, newsequences, min_extrem_off, min_mean_off) == True:
                print(new_candidate)
                newsequences.append(new_candidate)
        #print(len(newsequences))
    print('done')


    # Initialize an empty dictionary for the new sequences and their energies
    new_sequence_energy_dict = {}

    # Loop through the new sequences and find them in sequence_energy_dict
    for seq in newsequences:
        if seq in sequence_energy_dict:
            new_sequence_energy_dict[seq] = sequence_energy_dict[seq]


    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open('new_sequence_energy_dict2.pkl', 'wb') as f:
        pickle.dump(new_sequence_energy_dict, f)





    timestamp = time.strftime("%Y%m%d-%H%M%S")  # Unique timestamp
    dynamic_filename = f"new_sequence_energy_dict_f1_{f1}_f2_{f2}_{timestamp}.pkl"

    # Save the new_sequence_energy_dict to a dynamically named pickle file
    with open(dynamic_filename, 'wb') as f:
        pickle.dump(new_sequence_energy_dict, f)




    selfnew= selfvalidate(newsequences)
    new_self_off_energies = selfnew['all_energies']
    print(np.mean(new_self_off_energies))

    selfold = selfvalidate(oldset)
    old_self_off_energies = selfold['all_energies']
    print(np.mean(old_self_off_energies))

    crossnewold = crossvalidate(newsequences, oldset)

    new_cross_old_off_energies  = crossnewold['all_energies']
    print(np.mean(new_cross_old_off_energies))
    # Create arbitrary indices for the x-axis, ensuring no overlap

    detla = 40
    x_old = np.arange(len(old_self_off_energies))  # For new_self_off_energies
    x_new = np.arange(len(new_self_off_energies)) + len(old_self_off_energies) + detla  # Shift x-axis for old_self_off_energies
    x_cross = np.arange(len(new_cross_old_off_energies)) + len(x_new) + len(x_old) + detla +detla # Shift x-axis for new_cross_old_off_energies

    # Create scatter plot
    plt.scatter(x_new, new_self_off_energies, color='blue', label='New Self Energies')
    plt.scatter(x_old, old_self_off_energies, color='green', label='Old Self Energies')
    plt.scatter(x_cross, new_cross_old_off_energies, color='red', label='New Cross Old Energies')

    # Add labels and title
    plt.xlabel('Arbitrary Index')
    plt.ylabel('Energy')
    plt.title('Scatter Plot of Energies')

    # Add a legend to distinguish the different sets
    plt.legend()

    # Show the plot
    plt.show()