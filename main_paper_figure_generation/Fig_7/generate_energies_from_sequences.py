from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
import pickle

if __name__ == "__main__":
    # 1) Load sequence pairs from file (make sure the correct file name is provided).
    # The file needs to be located in the results folder. This is where run_sequence_search script saves it.
    sequence_pairs = hf.load_sequence_pairs_from_txt('/Users/floriankatzmeier/Documents/programming_stuff/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/results/the_new_64_seq.txt', use_default_results_folder=False)

    outpath = "/Users/floriankatzmeier/Documents/programming_stuff/data_hash/"

    # 2) Optional: Enable precomputed energy cache for faster performance
    #hf.choose_precompute_library("my_new_cache.pkl")
    hf.USE_LIBRARY = False  # Set to True to use the cache, False to force recomputation


    on_e = sc.compute_ontarget_energies(sequence_pairs)
    pickle.dump(on_e,open(outpath + "on_e_new64.pkl","wb"))


    off_e = sc.compute_offtarget_energies(sequence_pairs)
    pickle.dump(off_e, open(outpath + "off_e_new64.pkl", "wb"))

    # The file needs to be located in the results folder. This is where run_sequence_search script saves it.
    sequence_pairs2 = hf.load_sequence_pairs_from_txt('/Users/floriankatzmeier/Documents/programming_stuff/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/results/the_old_32_seq.txt', use_default_results_folder=False)

    outpath2 = "/Users/floriankatzmeier/Documents/programming_stuff/data_hash/"

    on_e_2 = sc.compute_ontarget_energies(sequence_pairs2)
    pickle.dump(on_e_2,open(outpath2 + "on_e_old32.pkl","wb"))

    off_e_2 = sc.compute_offtarget_energies(sequence_pairs2)
    pickle.dump(off_e_2, open(outpath2 + "off_e_old32.pkl", "wb"))
