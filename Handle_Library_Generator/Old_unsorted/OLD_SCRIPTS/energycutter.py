
from sequence_picking_tools import *




if __name__ == '__main__':
    # open the old handle sequences as dictionary
    with open('handle_energy_dict.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    # Load the dictionary with all the available sequences
    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    depleted_sequence_dict = sequence_energy_dict.copy()

    # Load the statistics
    with open('stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    f1 = 2.5
    f3 = 0.5
    f2 = 6.0

    max_on = -8.5#stat_dict['max_on'] - 1
    min_on = -10.5#stat_dict['mean_on'] - f2 * stat_dict['std_on']

    min_extrem_off = stat_dict['mean_off'] - f1 * stat_dict['std_off']
    print(min_extrem_off)
    min_mean_off = stat_dict['mean_off'] - f3 * stat_dict['std_off']
    print(min_mean_off)

    # Remove sequences outside range
    remove_sequences_outside_range(depleted_sequence_dict, min_on, max_on)





    # Initialize an empty dictionary for the new sequences and their energies
    #new_sequence_energy_dict = {seq: sequence_energy_dict[seq] for seq in newsequences if seq in sequence_energy_dict}

    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open('nrange85to105.pkl', 'wb') as f:
        pickle.dump(depleted_sequence_dict, f)

    print('done')