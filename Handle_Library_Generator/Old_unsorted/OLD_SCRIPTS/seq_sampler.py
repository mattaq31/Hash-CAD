import pickle
import os
from crisscross.helper_functions import revcom
import matplotlib.pyplot as plt

with open(os.path.join('.', 'chris_handle_distribution.pkl'), 'rb') as f:
    all_chris_handles, chris_energies = pickle.load(f)
    all_chris_antihandles = [revcom(handle) for handle in all_chris_handles]
    max_chris_energy = max(chris_energies)
    min_chris_energy = min(chris_energies)

with open(os.path.join('.', 'gc_3_4_full_sweep_energies.pkl'), 'rb') as f:
    possible_new_sequences, new_energies = pickle.load(f)
    possible_new_antihandles = [revcom(handle) for handle in possible_new_sequences]
    validated_new_seqs = []
    validated_new_energies = []
    blocked_antihandles = []
    for i, seq in enumerate(possible_new_sequences):
        if seq not in all_chris_handles and seq not in all_chris_antihandles and seq not in blocked_antihandles:
            if max_chris_energy >= new_energies[i] >= min_chris_energy:
                if 'AAAA' not in seq and 'TTTT' not in seq and 'CCCC' not in seq and 'GGGG' not in seq:
                    blocked_antihandles.append(revcom(seq))
                    validated_new_seqs.append(seq)
                    validated_new_energies.append(new_energies[i])

plt.scatter(range(len(validated_new_energies)), validated_new_energies, c='b')
plt.scatter(range(len(chris_energies)), chris_energies, c='r')
plt.show()

