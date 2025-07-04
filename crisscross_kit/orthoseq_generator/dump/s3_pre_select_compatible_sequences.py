from sequence_picking_tools import *
from multiprocessing import cpu_count


def process_sequence(candidate, fullset, min_extrem_off, min_mean_off):
    """Helper function to validate sequence."""
    if validate_new_seq(candidate, fullset, min_extrem_off, min_mean_off):
        return candidate
    return None



def parallel_pick_and_validate_sequences(depleted_sequence_dict, oldset, min_extrem_off, min_mean_off, batch_size=100):
    """Parallelized picking and validating of sequences."""
    newsequences = []
    total_sequences = len(depleted_sequence_dict)  # Total number of sequences to process

    # Progress bar for the main loop
    with tqdm(total=total_sequences, desc="Validating Sequences", ncols=30) as pbar:
        while len(depleted_sequence_dict) > 0:
            # Dynamically adjust the batch size if there are fewer remaining sequences
            actual_batch_size = min(batch_size, len(depleted_sequence_dict))

            # Pick a larger batch of sequences upfront
            candidates = [pick_and_remove_sequence(depleted_sequence_dict) for _ in range(actual_batch_size)]

            # Use only the oldset for validation, without combining with newsequences
            fullset = oldset

            with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                # Submit validation tasks for the batch of candidates
                futures = executor.map(process_sequence, candidates, [fullset] * actual_batch_size,
                                       [min_extrem_off] * actual_batch_size, [min_mean_off] * actual_batch_size)

                # Collect valid sequences
                for result in futures:
                    if result is not None:
                        newsequences.append(result)

                # Update the progress bar based on batch size
                pbar.update(actual_batch_size)

    return newsequences

if __name__ == '__main__':

    name= 'TT_no_crosscheck92to104'
    #the values bellow are plus minus 0.6 times the standart deviation of the whole 7 mer pool



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


    #only relevant in case you want to add sequences ot an exisitng set
    f1 = 9.5 # set high her because we dont want to chekc for self complementarty at this point
    f3 = 2.0
    f2 = 6.0

    max_on = -9.2#stat_dict['max_on'] - 0.00
    min_on = -10.4

    #value controlls off target binding for self complemtarity
    min_extrem_off = -17.0#stat_dict['mean_off'] - f1 * stat_dict['std_off']
    print(min_extrem_off)
    min_mean_off = stat_dict['mean_off'] - f3 * stat_dict['std_off']
    print(min_mean_off)

    # Remove sequences outside range
    remove_sequences_outside_range(depleted_sequence_dict, min_on, max_on)

    # Variables to hold new sequences
    newsequences = []
    # put it here if there is an old set to which the new sequences need to be compatable
    oldset = []#list(handle_energy_dict.keys())
    print(len(depleted_sequence_dict))

    # Run the parallel sequence picking and validation
    newsequences = parallel_pick_and_validate_sequences(depleted_sequence_dict, oldset, min_extrem_off, min_mean_off)

    # Initialize an empty dictionary for the new sequences and their energies
    new_sequence_energy_dict = {seq: sequence_energy_dict[seq] for seq in newsequences if seq in sequence_energy_dict}
    print(len(new_sequence_energy_dict))
    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open(name +'.pkl', 'wb') as f:
        pickle.dump(new_sequence_energy_dict, f)

    print('done')
