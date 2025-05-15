from Energy_computation_functions import *
from sequence_picking_tools import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import time
from collections import Counter


if __name__ == '__main__':
    # open the old handle sequences as dictionary
    with open('wide_range_f1_275_f3_3.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    handles = list(handle_energy_dict.keys())
    print(len(handles))

    crossdick = selfvalidate(handles)

    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open('wide_range_f1_275_f3_3cross.pkl', 'wb') as f:
        pickle.dump(crossdick , f)
    print('hallo')

    # Load the statistics
    with open('stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    f1 = 2.75
    f3 = 3
    f2 = 6.0

    max_on =stat_dict['max_on']
    min_on = stat_dict['mean_on']- f2 * stat_dict['std_on']


    min_extrem_off = stat_dict['mean_off']- f1*stat_dict['std_off']
    print(min_extrem_off)
    min_mean_off = stat_dict['mean_off']-f3*stat_dict['std_off']
    print(min_mean_off)


    hh=crossdick['handle_handle_energies']
    hah= crossdick['antihandle_handle_energies']
    ahah = crossdick['antihandle_antihandle_energies']
    all_energies = crossdick['all_energies']

    # Find indices where values are less than min_extrem_off for each array
    hh_infixes = np.argwhere(hh < min_extrem_off)
    hah_infixes = np.argwhere(hah < min_extrem_off)
    ahah_infixes = np.argwhere(ahah < min_extrem_off)

    # Print the results
    print("Indices in 'hh' where value < min_extrem_off:", hh_infixes)
    print("Indices in 'hah' where value < min_extrem_off:", hah_infixes)
    print("Indices in 'ahah' where value < min_extrem_off:", ahah_infixes)

    # Example 'handles' list containing strings
    # Assuming handles contains enough elements to match the indices in the arrays
    # For example, handles = ['A', 'B', 'C', 'D', ...]

    def replace_indices_with_handles(infixes, handles):
        # Replace indices in the infixes with the corresponding values from handles list
        return [(handles[i], handles[j]) for i, j in infixes]

    # Replace the indices in each infix list
    hh_infixes_with_handles = replace_indices_with_handles(hh_infixes, handles)
    hah_infixes_with_handles = replace_indices_with_handles(hah_infixes, handles)
    ahah_infixes_with_handles = replace_indices_with_handles(ahah_infixes, handles)

    # Print the results
    print("Infixes in 'hh' with handles:", hh_infixes_with_handles)
    print("Infixes in 'hah' with handles:", hah_infixes_with_handles)
    print("Infixes in 'ahah' with handles:", ahah_infixes_with_handles)


    def count_index_occurrences(infixes):
        # Flatten the list of tuples into individual indices
        flattened_indices = [index for pair in infixes for index in pair]

        # Count occurrences of each index
        index_count = Counter(flattened_indices)

        return index_count

    # Calculate the occurrences for each set of infixes
    hh_index_counts = count_index_occurrences(hh_infixes)
    hah_index_counts = count_index_occurrences(hah_infixes)
    ahah_index_counts = count_index_occurrences(ahah_infixes)

    # Print the results
    print("Occurrences of indices in 'hh' infixes:", hh_index_counts)
    print("Occurrences of indices in 'hah' infixes:", hah_index_counts)
    print("Occurrences of indices in 'ahah' infixes:", ahah_index_counts)

    # Combine the numpy arrays vertically into one
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))

    # Convert the combined array to a list of tuples for counting
    combined_infixes_list = [tuple(row) for row in combined_infixes]

    # Count the occurrences across the combined list
    combined_index_counts = count_index_occurrences(combined_infixes_list)

    # Print the results
    print("Occurrences of indices across all infixes:", combined_index_counts)


    def elimination_algorithm(infixes_list):
        elimination_order = []
        remaining_tuples = infixes_list.copy()

        while remaining_tuples:
            # Count occurrences in the remaining tuples
            index_count = count_index_occurrences(remaining_tuples)

            # If there are no more tuples, break
            if not index_count:
                break

            # Find the index with the highest count
            most_common_index = index_count.most_common(1)[0][0]

            # Add the index to the elimination order
            elimination_order.append(most_common_index)

            # Eliminate all tuples that contain the most common index
            remaining_tuples = [pair for pair in remaining_tuples if most_common_index not in pair]

        return elimination_order


    def eliminate_indices_from_handles(handles, elimination_order):
        # Create a new list with handles that are NOT in the elimination order
        modified_handles = [handle for i, handle in enumerate(handles) if i not in elimination_order]

        return modified_handles

    # Apply the elimination algorithm
    elimination_order = elimination_algorithm(combined_infixes_list)

    # Print the results
    print("Elimination order of indices:", elimination_order)


    # Example handles list
    # handles = ['A', 'B', 'C', 'D', ...]

    # Apply the elimination to the handles list
    modified_handles = eliminate_indices_from_handles(handles, elimination_order)
    print(len(modified_handles))
    # Print the results
    print("Modified handles after elimination:", modified_handles)
    print()
    crosdick_eliminated = selfvalidate(modified_handles)

    all_energies_eli = crosdick_eliminated ['all_energies']
    detla = 40
    x_eli= np.arange(len(all_energies_eli))
    x_old= np.arange(len(all_energies)) + detla + len(x_eli)

    plt.scatter(x_eli, all_energies_eli, color='red', label='23 best handles')
    plt.scatter(x_old, all_energies, color='g', label='all 32')


    # Add labels and title for the second plot
    plt.xlabel('Arbitrary Index')
    plt.ylabel('Gibbs free energy')
    plt.title('off target energies: handle elimination')
    plt.legend()

    # Save the second plot as a PDF

    plt.savefig('eliminatedhandles.pdf')
    # Show the second plot
    plt.show()
    blacklist= []
    for indexi in elimination_order:
        blacklist.append( handles[indexi])
    print (blacklist)