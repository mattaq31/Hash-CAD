from sequence_computations import *
import pickle
import numpy as np

def pick_and_remove_sequence(seqdict):
    # Select a random key
    random_key = random.choice(list(seqdict.keys()))
    del seqdict[random_key]
    return random_key



def validate_new_seq(newseq, oldset, min_extrem, min_mean):
    oldset = oldset
    newseqs= [newseq, revcom(newseq)]
    revoldset = [revcom(seq) for seq in oldset]

    total_old_set= oldset + revoldset
    Es = np.zeros((len(newseqs), len(total_old_set)))
    E = np.zeros(len(newseqs))

    for k, nseq in enumerate(newseqs):
        E[k]= nupack_compute_energy_TT_self(nseq,nseq,Use_Library=False)
        if E[k] < min_extrem:
            return False

    for j, nseq in enumerate(newseqs):
        for i , oseq in enumerate(total_old_set):
            Es[j, i]  =  nupack_compute_energy_TT_self(nseq, oseq,Use_Library=False)
            #print(Es[j, i])
            if Es[j,i] < min_extrem:
                return False
            #the mean can not be computed if there is no elements in the list. So the firs will caus an error
    if len(oldset) <= 2:
        return True
    else:
        combined_array = np.concatenate((Es.flatten(), E))
        mean = np.mean(combined_array)
        if mean < min_mean:
            return False
        else:
            return True






def remove_sequences_outside_range(seqdict, min_energy, max_energy):
    # Iterate through the dictionary and collect keys that need to be removed
    keys_to_remove = []
    for seq, energy in seqdict.items():
        if energy < min_energy or energy > max_energy:
            keys_to_remove.append(seq)

    # Now remove those keys from the original dictionary
    for key in keys_to_remove:
        del seqdict[key]


if __name__ == "__main__":


    with open('stat_dict.pkl', 'rb') as f:
       stat_dict = pickle.load(f)

    with open(os.path.join('.', 'core_32_sequences.pkl'), 'rb') as f:
        antihandles, handles = pickle.load(f)
    print(handles)
    newtestseq = 'TACCCAC'
    #above seq  should give ture and bellow seq shcould give false
    newtestseq2 = 'AGCCTTT'
    min_extrem = stat_dict['mean_off']- 2.75*stat_dict['std_off']
    min_mean = stat_dict['mean_off']

    T= validate_new_seq(newtestseq, handles, min_extrem, min_mean)
    print(T)
    T2 = validate_new_seq(newtestseq2, handles, min_extrem, min_mean)
    print(T2)
    print('hallo')


    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    print(len(sequence_energy_dict))
    sequence = pick_and_remove_sequence(sequence_energy_dict)
    print(sequence)
    print(len(sequence_energy_dict))