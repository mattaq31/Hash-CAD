import random
import sequence_generator.helper_functions as hf
import sequence_generator.sequence_computations as sc
import pickle
if __name__ == "__main__":
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # Generate sequence pool
    ontarget7mer = sc.create_sequence_pairs_pool(length=7, fivep_ext="TT", threep_ext="", avoid_gggg=False)

    # Set precomputed energy cache
    hf.choose_precompute_library("TT_7mers.pkl")
    hf.USE_LIBRARY = True
    
    # Select all sequences within desired on-target energy range
    
    max_ontarget = -9.6
    min_ontarget = -10.0
    #min_ontarget = -10.4

    subset, ids=  sc.select_all_in_energy_range(ontarget7mer, energy_min=min_ontarget, energy_max=max_ontarget)

    off_energies = sc.compute_offtarget_energies(subset)

    data = {
        'subset': subset,
        'ids': ids,
        'off_energies': off_energies
    }

    with open('subset_data_7mers96to100.pkl', 'wb') as f:
        pickle.dump(data, f)