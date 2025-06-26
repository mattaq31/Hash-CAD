import random
import sequence_generator.helper_functions as hf
import sequence_generator.sequence_computations as sc

if __name__ == "__main__":
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # Generate sequence pool
    ontarget7mer = sc.create_sequence_pairs_pool(length=7, fivep_ext="TT", threep_ext="", avoid_gggg=False)

    # Set precomputed energy cache
    hf.choose_precompute_library("TT_7mers.pkl")
    hf.USE_LIBRARY = True

    # Select a random subset of sequences 
    subset = sc.select_subset(ontarget7mer, max_size=250)

    # Compute on- and off-target energies
    on_e_subset = sc.compute_ontarget_energies(subset)
    off_e_subset = sc.compute_offtarget_energies(subset)

    # Plot and save
    stats = sc.plot_on_off_target_histograms(on_e_subset, off_e_subset, output_path='energy_hist.pdf')
