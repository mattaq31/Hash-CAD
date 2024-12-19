import numpy as np
import pickle
import os
from nupack import *
import matplotlib.pyplot as plt
from tqdm import tqdm
from crisscross.helper_functions import revcom
import itertools


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


# Define the DNA bases
bases = ['A', 'T', 'G', 'C']
seven_mers = [''.join(mer) for mer in itertools.product(bases, repeat=7)]

energy_vals = []
accepted_seqs = []

for i, seq in tqdm(enumerate(seven_mers)):
    if seq.count('G') + seq.count('C') == 3 or seq.count('G') + seq.count('C') == 4:
        energy_vals.append(nupack_compute_mfe(seq, revcom(seq)))
        accepted_seqs.append(seq)

