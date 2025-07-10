
'''


Purpose:
    Generate an initial pool of DNA sequence pairs, compute their on-target and off-target
    Gibbs free energies, and plot the distributions. This helps you choose sensible energy
    cutoff thresholds for downstream selection algorithms.

    NOTE: After running this once to get the overall energy distributions, use
    `analyze_on_target_range.py` (the second script) for a focused look at a specific
    on-target energy window based on your initial histograms.

Main Steps:
    1. Set a fixed random seed for reproducibility.
    2. Generate all 8-mer sequence pairs (and their reverse complements), filtering out any
       with four identical bases in a row.
    3. Point to (and enable) a precomputed energy cache to speed up repeated runs.
    4. Randomly sample up to 250 sequence pairs from the pool.
    5. Compute on-target energies (pair-hybridization) and off-target energies (cross-hybridization).
    6. Plot and save the histograms of both distributions to 'energy_hist.pdf', printing summary stats.



'''

import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc

if __name__ == "__main__":
    # 1) Reproducibility: fix the RNG
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # 2) Generate the full pool of 8-mer handle/antihandle pairs,
    #    excluding any with 'AAAA', 'CCCC', 'GGGG', or 'TTTT'
    ontarget8mer = sc.create_sequence_pairs_pool(
        length=8,
        fivep_ext="TT",
        threep_ext="",
        avoid_gggg=True
    )

    # 3) Configure and enable the precomputed energy cache.
    #    The specified pickle file ('8mers.pkl') will be created automatically during execution
    #    inside a folder called 'pre_computed_energies' (created if it doesn’t exist).
    #    If the file already exists, the script will simply load and reuse it instead of recomputing energies.
    hf.choose_precompute_library("8mers.pkl")
    hf.USE_LIBRARY = True

    # 4) Randomly sample 250 sequence pairs for a quick pilot analysis
    subset = sc.select_subset(ontarget8mer, max_size=250)

    # 5) Compute on-target (pair-hybridization) energies
    on_e_subset = sc.compute_ontarget_energies(subset)

    # 6) Compute off-target (cross-hybridization) energies
    off_e_subset = sc.compute_offtarget_energies(subset)

    # 7) Plot histograms of both energy distributions, save figure, and print stats
    stats = sc.plot_on_off_target_histograms(
        on_e_subset,
        off_e_subset,
        output_path='energy_hist.pdf'
    )
