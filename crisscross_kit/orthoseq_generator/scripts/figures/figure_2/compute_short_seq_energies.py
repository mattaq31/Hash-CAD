"""
Purpose:
    Compute NUPACK on-target and off-target energies for short sequences and
    save results to PKL for downstream analysis.

    This script does no plotting and no graph/selection logic.
"""

import os
import pickle
import random
import numpy as np

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


def run_compute_short_seq(
    length,
    range_sigma,
    random_seed=42,
    fivep_ext="",
    threep_ext="",
    avoid_gggg=False,
    use_library=False,
    output_dir=None,
):
    # Deterministic sampling for reproducibility.
    random.seed(random_seed)
    hf.choose_precompute_library(f"short_seq_{length}mers.pkl")
    hf.USE_LIBRARY = use_library
    hf.set_nupack_params(material="dna", celsius=37, sodium=0.05, magnesium=0.025)

    # Use a stable filename prefix for downstream scripts.
    out_prefix = f"short_seq_{length}mer_sigma{range_sigma}".replace(".", "p")

    sequence_pairs_list = sc.create_sequence_pairs_pool(
        length=length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        avoid_gggg=avoid_gggg,
    )
    pairs_only = [pair for _, pair in sequence_pairs_list]

    # Compute on-target energies to define the on-target window.
    on_e_all, _, _ = sc.compute_ontarget_energies(pairs_only)
    mean_on = float(np.mean(on_e_all))
    std_on = float(np.std(on_e_all))
    window_delta = float(range_sigma) * std_on
    min_on = mean_on - window_delta
    max_on = mean_on

    # Keep only sequences within the on-target window.
    subset_pairs = []
    subset_ids = []
    subset_on = []
    for (pair_id, pair), on_e in zip(sequence_pairs_list, on_e_all):
        if min_on <= on_e <= max_on:
            subset_pairs.append(pair)
            subset_ids.append(pair_id)
            subset_on.append(on_e)

    # Compute off-target energies only for the filtered subset.
    if subset_pairs:
        off_e_subset = sc.compute_offtarget_energies(subset_pairs)
    else:
        off_e_subset = None

    # Pack everything needed for downstream analysis.
    data = {
        "length": length,
        "fivep_ext": fivep_ext,
        "threep_ext": threep_ext,
        "avoid_gggg": avoid_gggg,
        "range_sigma": float(range_sigma),
        "min_on": float(min_on),
        "max_on": float(max_on),
        "subset_ids": subset_ids,
        "subset_pairs": subset_pairs,
        "subset_on": subset_on,
        "off_energies": off_e_subset,
        "nupack_params": dict(hf.NUPACK_PARAMS),
    }

    # Write results to disk.
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{out_prefix}_subset.pkl")
    else:
        out_path = f"{out_prefix}_subset.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(data, f)

    print(f"Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    # Minimal defaults for manual runs.
    OUTPUT_DIR = "results"
    LENGTHS = [7]
    RANGE_SIGMAS = [1.0]

    for length in LENGTHS:
        for sigma in RANGE_SIGMAS:
            run_compute_short_seq(
                length=length,
                range_sigma=sigma,
                use_library=False,
                output_dir=OUTPUT_DIR,
            )
