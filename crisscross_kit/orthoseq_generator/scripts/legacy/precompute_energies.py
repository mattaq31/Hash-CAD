
'''
Purpose:
    Generate and save a subset of 7-mer sequence pairs (here with 'TT' 5′ flank)
    whose on-target energies lie within a specified range, and compute their
    off-target interaction energies. The result is pickled for later use.

Main Steps:
    1. Fix the random seed for reproducibility.
    2. Generate all 7-mer handle/antihandle pairs with optional 'TT' 5′ extension,
       filtering out any sequences with four identical bases in a row.
    3. Configure and enable the precomputed energy cache to avoid redundant NUPACK calls.
    4. Define the on-target energy window and select all pairs within that range.
    5. Compute off-target energies for the selected subset.
    6. Package and save the subset, indices, and off-target energies to a pickle file.
'''

import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
import pickle

if __name__ == "__main__":
    # 1) Reproducibility: fix the RNG for consistent results
    RANDOM_SEED = 41
    random.seed(RANDOM_SEED)

    # 2) Generate all 7-mer handle/antihandle pairs with 'TT' 5′ flank,
    #    filtering out any containing four identical bases in a row
    ontarget7mer = sc.create_sequence_pairs_pool(
        length=7,
        fivep_ext="TT",
        threep_ext="",
        avoid_gggg=True
    )

    # 3) Configure and enable the precompute‐energy cache.
    #    The file "TT_7mers.pkl" will be created inside 'pre_computed_energies/' if missing,
    #    or loaded if it already exists, to avoid recomputing the same energies.
    hf.choose_precompute_library("TT_7mers.pkl")
    hf.USE_LIBRARY = True

    # 4) Define the on-target energy window for inclusion
    max_ontarget = -9.6   # sequences must bind at least this strongly
    min_ontarget = -10.1  # sequences should not bind stronger than this

    # 5) Select all sequence pairs whose on-target energies lie within [min_ontarget, max_ontarget].
    #    Returns:
    #      - subset: list of (seq, rc_seq) pairs
    #      - ids:   global indices of those pairs
    subset, ids = sc.select_all_in_energy_range(
        ontarget7mer,
        energy_min=min_ontarget,
        energy_max=max_ontarget
    )

    # 6) Compute off-target energies for the selected subset
    off_energies = sc.compute_offtarget_energies(subset)

    # 7) Package the subset, their indices, and off-target energies into a single object
    data = {
        'subset': subset,
        'ids': ids,
        'off_energies': off_energies
    }

    # 8) Save this data to disk for later analysis or plotting
    with open('subset_data_7mers96to101.pkl', 'wb') as f:
        pickle.dump(data, f)