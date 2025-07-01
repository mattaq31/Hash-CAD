from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc

if __name__ == "__main__":
    # Load sequence pairs from a saved file
    sequence_pairs = hf.load_sequence_pairs_from_txt('my_sequences.txt')

    # Enable use of precomputed library (optional)
    hf.choose_precompute_library("my_new_cache.pkl")
    hf.USE_LIBRARY = False

    # Compute energies
    on_e = sc.compute_ontarget_energies(sequence_pairs)
    off_e = sc.compute_offtarget_energies(sequence_pairs)

    # Plot and save histogram
    stats = sc.plot_on_off_target_histograms(on_e, off_e, output_path="energy_hist_loaded_sequences.pdf")
    print(stats)