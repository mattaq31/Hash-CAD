import numpy as np
import pickle
import os
from nupack import *
import matplotlib.pyplot as plt
from tqdm import tqdm
from crisscross.helper_functions import revcom


with open(os.path.join('..', 'core_32_sequences.pkl'), 'rb') as f:
    antihandles, handles = pickle.load(f)

with open(os.path.join('..', '256_set.txt'), 'r') as f:
    ext_handles = [line.strip() for line in f]

def nupack_compute_mfe(seq1, seq2):
    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    # specify tubes
    t1 = Tube(strands={A: 1e-8, B: 1e-8}, complexes=SetSpec(max_size=2), name='t1')
    # analyze tubes
    model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.025)
    tube_results = tube_analysis(tubes=[t1], model=model1, compute=['pairs', 'mfe', 'sample'],
                                 options={'num_sample': 1000})
    try:
        energy = tube_results['(H1+H2)'].mfe[0].energy
    except:
        energy = 0
    return energy

preread = True

# handles = ['ACGTGTA', 'TGCACGT', 'CGTACGA', 'GATCGTA', 'TACGGCT', 'CTAGGTC', 'AGCTGAC', 'GTACGTT', 'CCGTAGT', 'TAGCTAG']
# antihandles = [revcom(handle) for handle in handles]
if preread:
    with open(os.path.join('..', 'handle_antihandle_binding_energies.pkl'), 'rb') as f:
        crosscorrelated_handle_energies, crosscorrelated_antihandle_energies, crosscorrelated_handle_antihandle_energies = pickle.load(f)
else:
    crosscorrelated_handle_energies= np.zeros((len(handles), len(handles)))
    for i, handle_i in enumerate(tqdm(handles)):
            for j, handle_j in enumerate(handles):
                if j != i: # avoid here the correct binding partners
                    test = nupack_compute_mfe(handle_i, handle_j)
                    crosscorrelated_handle_energies[i, j] = test

    crosscorrelated_antihandle_energies= np.zeros((len(antihandles), len(antihandles)))
    for i, antihandle_i in enumerate(tqdm(antihandles)):
            for j, antihandle_j in enumerate(antihandles):
                if j != i: # avoid here the correct binding partners
                    test = nupack_compute_mfe(antihandle_i, antihandle_j)
                    crosscorrelated_antihandle_energies[i, j] = test

    crosscorrelated_handle_antihandle_energies= np.zeros((len(handles), len(antihandles)))
    for i, handle_i in enumerate(tqdm(handles)):
            for j, antihandle_j in enumerate(antihandles):
                if j != i: # avoid here the correct binding partners
                    test = nupack_compute_mfe(handle_i, antihandle_j)
                    crosscorrelated_handle_antihandle_energies[i, j] = test

matching_handle_antihandle_energies = np.zeros(len(handles))
for i in tqdm(range((len(handles)))):
    matching_handle_antihandle_energies[i] = nupack_compute_mfe(handles[i], antihandles[i])

tiled_handle_matching_handle_antihandle_energies =  np.tile(matching_handle_antihandle_energies, (len(handles), 1))
normalized_crosscorrelated_handle_handle_energies = crosscorrelated_handle_energies/tiled_handle_matching_handle_antihandle_energies
normalized_crosscorrelated_antihandle_antihandle_energies = crosscorrelated_antihandle_energies/tiled_handle_matching_handle_antihandle_energies
normalized_crosscorrelated_handle_antihandle_energies = crosscorrelated_handle_antihandle_energies/tiled_handle_matching_handle_antihandle_energies

print(np.max(normalized_crosscorrelated_handle_handle_energies), np.max(normalized_crosscorrelated_antihandle_antihandle_energies), np.max(normalized_crosscorrelated_handle_antihandle_energies))

plt.hist(normalized_crosscorrelated_handle_handle_energies[normalized_crosscorrelated_handle_handle_energies!=0].flatten(), bins=50)
plt.show()
plt.hist(normalized_crosscorrelated_antihandle_antihandle_energies[normalized_crosscorrelated_antihandle_antihandle_energies!=0].flatten(), bins=50)
plt.show()
plt.hist(normalized_crosscorrelated_handle_antihandle_energies[normalized_crosscorrelated_handle_antihandle_energies!=0].flatten(), bins=50)
plt.show()
