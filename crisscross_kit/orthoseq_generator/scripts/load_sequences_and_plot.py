'''
analyze_saved_sequences.py

Purpose:
    This script loads a previously saved set of DNA sequence pairs and analyzes their
    on-target and off-target energy distributions. It is intended for **post hoc analysis**
    of sequences selected by earlier scripts.

    Typical use case:
        - After running `run_sequence_search.py` or any other selection script,
          use this script to recompute and visualize the energy statistics of the saved sequences.

Main Steps:
    1. Load sequence pairs from a previously saved .txt file.
    2. Optionally enable use of a precomputed energy library for faster calculations.
    3. Compute both on-target (self-binding) and off-target (cross-binding) energies.
    4. Plot and save the energy histograms, and print the summary statistics.
'''

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc

if __name__ == "__main__":
    # 1) Load sequence pairs from file (make sure the correct file name is provided). 
    # The file needs to be located in the results folder. This is where run_sequence_search script saves it. 
    sequence_pairs = hf.load_sequence_pairs_from_txt('stell_2.txt')

    # 2) Optional: Enable precomputed energy cache for faster performance
    hf.choose_precompute_library("my_new_cache.pkl")
    hf.USE_LIBRARY = False  # Set to True to use the cache, False to force recomputation

    # 3) Compute on-target energies (self-hybridization)
    on_e = sc.compute_ontarget_energies(sequence_pairs)

    # 4) Compute off-target energies (cross-hybridization)
    off_e = sc.compute_offtarget_energies(sequence_pairs)

    # 5) Plot histograms and save results
    stats = sc.plot_on_off_target_histograms(
        on_e,
        off_e,
        output_path="energy_hist_loaded_sequences.pdf"
    )

    print(stats)