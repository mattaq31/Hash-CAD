import numpy as np
import pickle
import os
from nupack import *
import matplotlib.pyplot as plt
from tqdm import tqdm

dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}

def revcom(sequence):
    """
    Reverse complements a DNA sequence.
    :param sequence: DNA string, do not add any other characters (TODO: make more robust)
    :return: processed sequence (string)
    """
    return "".join(dna_complement[n] for n in reversed(sequence))


with open(os.path.join('/root', 'core_32_sequences.pkl'), 'rb') as f:
    antihandles, handles = pickle.load(f)


def nupack_compute_mfe(seq1, seq2):
    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    # specify tubes
    t1 = Tube(strands={A: 1e-8, B: 1e-8}, complexes=SetSpec(max_size=2), name='t1')
    # analyze tubes
    model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.025)
    tube_results = tube_analysis(tubes=[t1], model=model1, compute=['pairs', 'mfe', 'sample'],
                                 options={'num_sample': 1000})
    energy = tube_results['(H1+H2)'].mfe[0].energy
    return energy


pooled_energies = []
for index, h in tqdm(enumerate(handles)):
    energies = []
    # handles with other handles
    for i2, h2 in enumerate(handles):
        if i2 != index:
            energies.append(nupack_compute_mfe(h, h2))

    # handles with other antihandles (except itself)
    for i2, h2 in enumerate(handles):
        if i2 != index:
            energies.append(nupack_compute_mfe(h, revcom(h2)))

    # antihandle with all other antihandles (Except itself)
    for i2, h2 in enumerate(handles):
        if i2 != index:
            energies.append(nupack_compute_mfe(revcom(h), revcom(h2)))
    pooled_energies.append(np.mean(energies))
    if index == 1:
        break


plt.scatter(np.arange(1, len(pooled_energies)+1), pooled_energies)
plt.xticks(ticks=np.arange(1, 33), labels=handles, rotation=90)
plt.ylabel('Energy (kcal/mol)')
plt.title('Handle-Antihandle Energy')
plt.tight_layout()
plt.savefig('/root/energies.pdf')
plt.show()
