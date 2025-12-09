import copy
import random
import pickle
import numpy as np
from tqdm import tqdm
from datetime import datetime

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, extract_handle_dicts
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from eqcorr2d.eqcorr2d_interface import wrap_eqcorr2d, get_similarity_hist, get_sum_score, get_worst_match, get_seperate_worst_lists
from eqcorr2d.eqcorr2d_interface import *

# ---------------------
# Setup
# ---------------------
random.seed(42)

mega = Megastructure(import_design_file=r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/design_stuff/empty_sunflower/empty_sunflower.xlsx")
slat_array = mega.generate_slat_occupancy_grid()

scores = []

# ---------------------
# Main loop with tqdm
# ---------------------
for x in tqdm(range(100), desc="Generating random handles"):
    mega_working = copy.deepcopy(mega)
    handle_array = generate_random_slat_handles(slat_array, unique_sequences=32)
    mega_working.assign_assembly_handles(handle_array)
    parasitic_interactions = mega_working.get_parasitic_interactions()
    scores.append(parasitic_interactions.get('mean_log_score', None))

# ---------------------
# Print results
# ---------------------

score_array = np.array(scores)

print(score_array.min())

# ---------------------
# Save results as pickle
# ---------------------

filename = "scores_random_reduced32_100.pkl"

with open(filename, "wb") as f:
    pickle.dump(score_array, f)


