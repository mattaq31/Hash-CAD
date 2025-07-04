import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc

if __name__ == "__main__":
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # Generate sequence pool
    ontarget7mer = sc.create_sequence_pairs_pool(length=7, fivep_ext="TT", threep_ext="", avoid_gggg=False)

    # Set precomputed energy cache
    hf.choose_precompute_library("TT_7mers.pkl")
    hf.USE_LIBRARY = True

    # Select subset within desired on-target energy range
    max_ontarget = -9.6
    min_ontarget = -10.4
    subset, indices = sc.select_subset_in_energy_range(
        ontarget7mer, energy_min=min_ontarget, energy_max=max_ontarget,
        max_size=250, Use_Library=True
    )

    # Compute energies
    on_e_subset = sc.compute_ontarget_energies(subset)
    off_e_subset = sc.compute_offtarget_energies(subset)
    
    # Plot and save
    stats = sc.plot_on_off_target_histograms(
        on_e_subset,
        off_e_subset,
        output_path='energy_hist_10_4to9_6.pdf'
    )
