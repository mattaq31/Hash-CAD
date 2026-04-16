import copy
import pickle
import os
import multiprocessing
from functools import partial

import numpy as np
from tqdm import tqdm

from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver import generate_random_slat_handles


def worker_init(mega_obj, slat_arr):
    """Initialize each worker process with shared read-only data."""
    global _mega, _slat_array
    _mega = mega_obj
    _slat_array = slat_arr


def compute_score(unique_sequences, _seed):
    """Generate random handles and compute parasitic interaction score."""
    mega_working = copy.deepcopy(_mega)
    handle_array = generate_random_slat_handles(_slat_array, unique_sequences=unique_sequences)
    mega_working.assign_assembly_handles(handle_array)
    parasitic_interactions = mega_working.get_parasitic_interactions()
    return parasitic_interactions.get('mean_log_score', None)


if __name__ == '__main__':
    mega = Megastructure(import_design_file=r"/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/exp2_handle_library_sunflowers/design_stuff/empty_sunflower/empty_sunflower.xlsx")
    slat_array = mega.generate_slat_occupancy_grid()
    output_folder = '/Users/matt/Desktop'
    num_workers = multiprocessing.cpu_count() - 2
    total_runs = 2000 * 50

    for library_size in [32, 64]:
        scores = []
        best_score = float('inf')
        worker_fn = partial(compute_score, library_size)

        with multiprocessing.Pool(processes=num_workers, initializer=worker_init, initargs=(mega, slat_array)) as pool:
            pbar = tqdm(pool.imap_unordered(worker_fn, range(total_runs), chunksize=50),
                        total=total_runs, desc=f"Random handles for library size {library_size}")
            for score in pbar:
                scores.append(score)
                if score is not None and score < best_score:
                    best_score = score
                pbar.set_postfix({"Best Loss": best_score})

        score_array = np.array(scores)
        with open(os.path.join(output_folder, f'large_scale_sunflower_random_generation_scores_{library_size}.pkl'), "wb") as f:
            pickle.dump(score_array, f)
