from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.assembly_handle_optimization import generate_random_slat_handles
from crisscross.assembly_handle_optimization.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure
import numpy as np
import pandas as pd
import re
import os
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from tqdm import tqdm

def read_handle_log(filepath):
    xls = pd.ExcelFile(filepath)
    arrs = []
    i = 1
    while f"handle_interface_{i}" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=f"handle_interface_{i}", header=None)
        a = df.to_numpy(dtype=np.int64)
        arrs.append(a)
        i = i+1
    return np.stack(arrs, axis=-1)



def locate_logged_handle_arrays(folder_path):
    """
    Finds files in a folder that match the pattern 'best_handle_array_generation_<number>.xlsx'.
    Returns a sorted list of [number, filepath] pairs from lowest to highest number.
    """
    pattern = re.compile(r"best_handle_array_generation_(\d+)\.xlsx$")
    matching_files = []

    for fname in os.listdir(folder_path):
        matching_file = pattern.match(fname)
        if matching_file:  # <- fix here
            number = int(matching_file.group(1))
            filepath = os.path.join(folder_path, fname)
            matching_files.append([number, filepath])

    # Sort using a helper function
    def get_number(item):
        return item[0]

    matching_files.sort(key=get_number)
    return matching_files

def intuitive_score(matches,fudge_dG=-10):
    return -np.log(126*np.average(np.exp(-fudge_dG * (matches))))/fudge_dG



def compute_generation_results(file_locations, slat_array, slat_len):
    """
    Compute results for all generations.

    Parameters
    ----------
    file_locations : list of (generation:int, filepath:str)
        Output of locate_logged_handle_arrays(...).
    slat_array : np.ndarray
        Slat occupancy grid from Megastructure.
    slat_len : int
        Length of a single slat (e.g., 32).

    Returns
    -------
    list
        List of dicts with keys:
        - 'generation': int
        - 'match_type': np.ndarray
        - 'counts': np.ndarray
        - 'score': float
    """
    results = []

    for generation, file in tqdm(file_locations, desc="Processing generations", unit="gen"):
        handle_array = read_handle_log(file)

        handle_dict, antihandle_dict = extract_handle_dicts(handle_array, slat_array)
        hamming_results = oneshot_hamming_compute(handle_dict, antihandle_dict, slat_len)

        # matches = number of matching positions
        matches = -(hamming_results - slat_len)
        flat_matches = matches.flatten()
        score = intuitive_score(flat_matches)

        match_type, counts = np.unique(flat_matches, return_counts=True)

        # Store as a plain dict for easy pickling/consumption later
        results.append(
            {
                "generation": generation,
                "match_type": match_type,
                "counts": counts,
                "score": score,
            }
        )

    return results


def save_results_pkl(results, out_path):
    """
    Save results list to a pickle file.

    Parameters
    ----------
    results : list
        Output of compute_generation_results(...).
    out_path : str or Path
        Destination .pkl path.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(results, f, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    """
    Example usage:
    - Reads a megastructure design and all logged handle arrays in a folder.
    - Computes per-generation match histograms + an intuitive score.
    - Saves everything to a pickle file for plotting elsewhere.
    """
    # Example: read a specific design from file
    megastructure = Megastructure(import_design_file=r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH30.xlsx")
    slat_array = megastructure.generate_slat_occupancy_grid()

    # Find logged generations
    folder = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\final_H30_square_evolution"
    file_locations = locate_logged_handle_arrays(folder)

    # Parameters
    slat_len = 32

    # Compute and save
    results = compute_generation_results(file_locations, slat_array, slat_len)

    # Pick where you want the results
    out_pkl = Path(folder) / "evolution_results24000_onwards.pkl"
    save_results_pkl(results, out_pkl)

    # Optional: quick sanity check (no plotting here)
    # loaded = load_results_pkl(out_pkl)
    # print(f"Saved {len(loaded)} generations to {out_pkl}")







