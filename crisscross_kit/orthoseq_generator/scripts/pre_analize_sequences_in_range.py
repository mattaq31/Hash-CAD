
'''


Purpose:
    Narrow in on a specific on-target energy window for more precise cutoff selection.
    This script should be run **after** `pre_analize_sequences.py`, using the histograms
    from that first pass to set `min_ontarget` and `max_ontarget` appropriately.

Main Steps:
    1. Set a fixed random seed for reproducibility.
    2. Generate all 7-mer sequence pairs (without filtering by 'GGGG' if you want the full range).
    3. Point to the same precomputed energy cache.
    4. Select a random subset of up to 250 pairs whose on-target energies lie within [min_ontarget, max_ontarget].
    5. Compute on- and off-target energies for that restricted pool.
    6. Plot and save the refined histograms to 'energy_hist_10_4to9_6.pdf'.



'''

import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc

if __name__ == "__main__":
    # 1) Set a random seed for reproducibility 
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # 2) Generate the full pool of 7-mer handle/antihandle pairs,
    #    excluding any with 'AAAA', 'CCCC', 'GGGG', or 'TTTT'
    ontarget8mer = sc.create_sequence_pairs_pool(
        length=7,
        fivep_ext="",
        threep_ext="",
        avoid_gggg=False
    )

    sequence_pairs_object = sc.SequencePairRegistry(
        length=20,
        fivep_ext="",
        threep_ext="",
        unwanted_substrings=["AAAA", "CCCC", "GGGG", "TTTT"],
        apply_unwanted_to="core",
        seed=RANDOM_SEED
    )


    # 3) Configure and enable the precomputed energy cache.
    #    The specified pickle file ('8mers.pkl') will be created automatically during execution
    #    inside a folder called 'pre_computed_energies' (created if it doesn’t exist).
    #    If the file already exists, the script will simply load and reuse it instead of recomputing energies.
    hf.choose_precompute_library("8mers.pkl")
    hf.USE_LIBRARY = False

    # 4) Select subset within desired on-target energy range (based on first script’s histograms)
    max_ontarget = -10
    min_ontarget = -30
    subset, indices = sc.select_subset_in_energy_range(
        sequence_pairs_object,
        energy_min=min_ontarget,
        energy_max=max_ontarget,
        self_energy_min=-2,
        max_size=2,
        Use_Library=False
    )

    # 5) Compute on-target energies for the restricted subset
    on_e_subset,self_e_A,self_e_B = sc.compute_ontarget_energies(subset)

    # 6) Compute off-target energies for the same subset
    off_e_subset = sc.compute_offtarget_energies(subset)

    # 7) Plot and save the refined histograms, printing summary stats
    stats = sc.plot_on_off_target_histograms(
        on_e_subset,
        off_e_subset,
        output_path='energy_random10mers_12to13.pdf'
    )

    self_stats =sc.plot_self_energy_histogram([self_e_A,self_e_B],bins=30, output_path='10mer_self_energies.pdf')
