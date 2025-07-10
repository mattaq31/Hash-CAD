#!/usr/bin/env python3
'''
postprocess_subset.py

Purpose:
    Load a previously saved subset of 7-mer sequence pairs and their off-target energies,
    build the interaction graph, run the iterative vertex-cover heuristic to extract an
    independent set (orthogonal sequences), and save the results.

Main Steps:
    1. Fix the random seed for reproducibility.
    2. Load the pickled subset data (sequences, indices, off-target energies).
    3. Build the off-target interaction graph using a specified energy cutoff.
    4. Run the iterative vertex-cover algorithm to find the minimum cover.
    5. Compute the independent set (orthogonal sequences) as the complement of the cover.
    6. Save the independent sequences to a text file.

Usage:
    python postprocess_subset.py
'''

import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import vertex_cover_algorithms as vca
import pickle

if __name__ == "__main__":
    # 1) Reproducibility: fix the RNG for consistent results
    RANDOM_SEED = 41
    random.seed(RANDOM_SEED)

    # 2) Load the saved subset data (sequences, indices, off-target energies)
    with open('subset_data_7mers96to100.pkl', 'rb') as f:
        data = pickle.load(f)

    subset = data['subset']   # list of (seq, rc_seq) pairs
    ids = data['ids']         # corresponding global indices
    id_to_seq = dict(zip(ids, subset))

    off_energies = data['off_energies']  # dict of off-target energy matrices

    # 3) Define the off-target energy cutoff for edges
    offtarget_limit = -7.4

    # 4) Build the graph: vertices = sequence indices, edges where energy < cutoff
    edges = vca.build_edges(off_energies, ids, offtarget_limit)
    vertices = set(ids)

    # 5) Run the iterative vertex-cover heuristic (single multistart here)
    #    - num_vertices_to_remove: how many to drop in each perturbation
    #    - max_iterations: inner-loop iterations
    #    - limit: stop early if cover size reaches len(V)-limit
    #    - multistart: number of random restarts
    #    - population_size: max retained covers per generation
    #    - show_progress: display iteration logs
    vertex_cover = vca.iterative_vertex_cover_multi(
        vertices, edges,
        preserve_V=None,
        num_vertices_to_remove=200,
        max_iterations=200,
        limit=70,
        multistart=1,
        population_size=300,
        show_progress=True
    )

    # 6) Derive the independent set: all vertices not in the cover
    independent = vertices - vertex_cover
    independent_sequences = [id_to_seq[i] for i in independent]

    # 7) Output: print and save the orthogonal (independent) sequences
    print("Selected independent (orthogonal) sequences:")
    for seq, rc in independent_sequences:
        print(seq, rc)

    hf.save_sequence_pairs_to_txt(
        independent_sequences,
        filename='independent_sequences.txt'
    )
