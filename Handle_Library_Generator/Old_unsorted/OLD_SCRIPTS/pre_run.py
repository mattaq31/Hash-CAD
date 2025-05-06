from Energy_computation_functions import *
from sequence_picking_tools import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import time







# open the old handle sequences as dictionary
with open('handle_energy_dict.pkl', 'rb') as f:
    handle_energy_dict = pickle.load(f)

# Load the dictionary with all the available sequences
with open('sequence_energy_dict.pkl', 'rb') as f:
    sequence_energy_dict = pickle.load(f)

depleted_sequence_dict= sequence_energy_dict.copy()
# Load the statistics
with open('stat_dict.pkl', 'rb') as f:
    stat_dict = pickle.load(f)

f1 = 2.75
f3 = 0.75
f2 =6.0

max_on =stat_dict['max_on']-2
min_on = stat_dict['mean_on']- f2 * stat_dict['std_on']


min_extrem_off = stat_dict['mean_off']- f1*stat_dict['std_off']
print(min_extrem_off)
min_mean_off = stat_dict['mean_off']-f3*stat_dict['std_off']
print(min_mean_off)


remove_sequences_outside_range(depleted_sequence_dict, min_on, max_on)

newsequences= []
oldset = list(handle_energy_dict.keys())

while len(depleted_sequence_dict) > 0:# and len(newsequences) < 14:
    print(f"Found {len(newsequences)} sequences, {len(depleted_sequence_dict)} sequences to go.")

    new_candidate = pick_and_remove_sequence(depleted_sequence_dict)

    fullset = oldset #+ newsequences

    if validate_new_seq(new_candidate, fullset, min_extrem_off, min_mean_off) == True:
       # if validate_new_seq(new_candidate, newsequences, min_extrem_off, min_mean_off) == True:
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
with open('new_sequence_toto_test_energy_dict_highenergyself.pkl', 'wb') as f:
    pickle.dump(new_sequence_energy_dict, f)