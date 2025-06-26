from sequence_generator.sequence_computations import *
from tqdm import tqdm
import itertools
import pickle

# Function to check if a sequence contains four consecutive G's, C's, A's, or T's
def has_four_consecutive_bases(seq):
    return 'GGGG' in seq or 'CCCC' in seq or 'AAAA' in seq or 'TTTT' in seq


def preselect_sequences_and_analize(lenght=7,fivep_ext="TT", threep_ext="",avoid_gggg=True):
    # Define the DNA bases
    bases = ['A', 'T', 'G', 'C']
    n_mers = [''.join(mer) for mer in itertools.product(bases, repeat=lenght)]
    unique_seven_mers = []
    for mer in seven_mers:
        rc_mer = revcom(mer)
        if mer not in unique_seven_mers and rc_mer not in unique_seven_mers:
            unique_seven_mers.append(mer)

    # remove GGGG and CCCC and etc
    if avoid_gggg==True:
        filtered_final_list = []
        for mer in unique_seven_mers:
            if not has_four_consecutive_bases(mer):
                filtered_final_list.append(mer)
    else:
        filtered_final_list = unique_seven_mers


    return filtered_final_list
if __name__ == "__main__":



    # Define the DNA bases
    bases = ['A', 'T', 'G', 'C']
    seven_mers = [''.join(mer) for mer in itertools.product(bases, repeat=7)]






    print(len(seven_mers))
    # Remove reverse complements from the filtered list
    unique_seven_mers = []

    for mer in seven_mers:
        rc_mer = revcom(mer)
        if mer not in unique_seven_mers and rc_mer not in unique_seven_mers:
            unique_seven_mers.append(mer)
    print(len(unique_seven_mers))
    sequence_energy_dict = {}  # Dictionary to store sequences and corresponding energy values

    # remove GGGG and CCCC and etc
    filtered_final_list = []
    for mer in unique_seven_mers:
        if not has_four_consecutive_bases(mer):
            filtered_final_list.append(mer)

    for i, seq in tqdm(enumerate(filtered_final_list)):

        energyn = nupack_compute_energy_TT_self(seq, revcom(seq),samples=100,type='total')
        sequence_energy_dict[seq] = energyn


    print(len(sequence_energy_dict))


    # Save the dictionary to a pickle file
    with open('sequence_energy_dict.pkl', 'wb') as f:
        pickle.dump(sequence_energy_dict, f)