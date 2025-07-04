import numpy as np
import pickle
import os
from nupack import *
import matplotlib.pyplot as plt
from tqdm import tqdm
from crisscross.helper_functions import revcom


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
        print(f'The two sequences provided ({seq1}, {seq2}) have no interactions at all.')
        energy = 0
    return energy

with open(os.path.join('..', 'core_32_sequences.pkl'), 'rb') as f:
    antihandles, handles = pickle.load(f)

with open(os.path.join('..', '256_set.txt'), 'r') as f:
    ext_handles = [line.strip() for line in f]

all_unique_handles = list(set(handles + ext_handles))

energy_vals = []
gc_content = []

for i in tqdm(range((len(all_unique_handles)))):
    energy_vals.append(nupack_compute_mfe(all_unique_handles[i], revcom(all_unique_handles[i])))
    gc_content.append((all_unique_handles[i].count('G') + all_unique_handles[i].count('C')) / len(all_unique_handles[i]))

