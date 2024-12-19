import os
import matplotlib.pyplot as plt
from collections import Counter
from nupack import *
from tqdm import tqdm

def count_kmer_repeats(sequences, k):
    kmer_counts = Counter()

    for sequence in sequences:
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i:i + k]
            kmer_counts[kmer] += 1

    repeated_kmers = {kmer: count for kmer, count in kmer_counts.items() if count > 1}
    return repeated_kmers

def nupack_compute_mfe(seq1, seq2):
    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    # specify tubes
    t1 = Tube(strands={A: 1e-8, B: 1e-8}, complexes=SetSpec(max_size=2), name='t1')
    # analyze tubes
    model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.015)
    tube_results = tube_analysis(tubes=[t1], model=model1, compute=['pairs', 'mfe', 'sample'], options={'num_sample': 1000})
    try:
        energy = tube_results['(H1+H2)'].mfe[0].energy
    except:
        print(f'The two sequences provided ({seq1}, {seq2}) have no interactions at all.')
        energy = 0
    return energy

# reads in Katzi's sequences
with open(os.path.join('.', 'TT_no_crosscheck96to104_64_sequence_pairs_flipped.txt'), 'r') as f:
    raw_handles = [line.strip() for line in f]
    handles = [i.split('\t')[0] for i in raw_handles]
    antihandles = [i.split('\t')[1] for i in raw_handles]

# checks GC content
gc_content = []
for h in handles:
    gc_content.append((h.count('G') + h.count('C')) / len(h))
plt.hist(gc_content)
plt.show()

# checks number of k-mer repeats
for k in [4, 5, 6]:
    repeats = count_kmer_repeats(handles + antihandles, k)
    print(f"{k}-mer repeats:")
    for kmer, count in repeats.items():
        print(f"  {kmer}: {count}")

# checks binding energies (on-target, off-target, handle-handle, antihandle-antihandle)
h_ah_dg = []
h_h_dg = []
ah_ah_dg = []
h_ah_on_target_dg = []
for i in tqdm(range(len(handles))):
    for j in range(len(handles)):
         energy = nupack_compute_mfe('TT'+handles[i], 'TT'+antihandles[j])
         if i == j:
            h_ah_on_target_dg.append(energy)
         else:
            h_ah_dg.append(energy)
    for j in range(i, len(handles)):
         if i != j:
             h_h_dg.append(nupack_compute_mfe('TT'+handles[i], 'TT'+handles[j]))
             ah_ah_dg.append(nupack_compute_mfe('TT'+antihandles[i], 'TT'+antihandles[j]))

plt.hist(h_h_dg, label='H-H',alpha=0.5)
plt.hist(ah_ah_dg, label='AH-AH',alpha=0.5)
plt.hist(h_ah_dg, label='H-AH',alpha=0.5)
plt.hist(h_ah_on_target_dg, label='H-AH-ON-TARGET',alpha=0.5)
plt.legend()
plt.show()
