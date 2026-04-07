"""
Purpose:
    Recompute on/off-target energies for sigma=1.0 and plot histograms per mer.

Notes:
    - Reads min_on/max_on (and num_vertices) from *_compare_results.csv files.
    - Recomputes energies because PKL files are not compatible with the current pandas.
"""

import glob
import os
import random
import numpy as np
import pandas as pd

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


SIGMA_TARGET = 1.0
RANDOM_SEED = 42
MAX_SIZE = 200
AVOID_GGGG = False
FIVEP_EXT = ""
THREEP_EXT = ""
USE_LIBRARY = False
SELF_ENERGY_MIN = -np.inf
TIMEOUT_S = 20
SHOW_PLOT = False


def _find_csvs(results_dir):
    pattern = os.path.join(results_dir, "*_compare_results.csv")
    return sorted(glob.glob(pattern))


def _extract_metadata(csv_path, sigma_target=SIGMA_TARGET):
    df = pd.read_csv(csv_path)
    if df.empty:
        return None

    if "range_sigma" not in df:
        return None

    sigma_vals = pd.to_numeric(df["range_sigma"], errors="coerce")
    keep = sigma_vals.apply(lambda x: np.isfinite(x) and np.isclose(x, sigma_target))
    df = df[keep]
    if df.empty:
        return None

    length = int(df["sequence_length"].dropna().iloc[0])
    min_on = float(df["min_on"].dropna().iloc[0])
    max_on = float(df["max_on"].dropna().iloc[0])
    num_vertices = None
    if "num_vertices" in df and not df["num_vertices"].dropna().empty:
        num_vertices = int(df["num_vertices"].dropna().iloc[0])

    return {
        "csv_path": csv_path,
        "length": length,
        "min_on": min_on,
        "max_on": max_on,
        "num_vertices": num_vertices,
    }


def _run_for_length(meta):
    length = meta["length"]
    min_on = meta["min_on"]
    max_on = meta["max_on"]
    num_vertices = meta["num_vertices"]

    random.seed(RANDOM_SEED)

    hf.choose_precompute_library(f"short_seq_{length}mers.pkl")
    hf.USE_LIBRARY = USE_LIBRARY
    hf.set_nupack_params(material="dna", celsius=37, sodium=0.05, magnesium=0.025)

    sequence_pairs = sc.create_sequence_pairs_pool(
        length=length,
        fivep_ext=FIVEP_EXT,
        threep_ext=THREEP_EXT,
        avoid_gggg=AVOID_GGGG,
    )

    max_size = MAX_SIZE

    subset_pairs, subset_ids, _, _ = sc.select_subset_in_energy_range(
        sequence_pairs,
        energy_min=min_on,
        energy_max=max_on,
        self_energy_min=SELF_ENERGY_MIN,
        max_size=max_size,
        Use_Library=USE_LIBRARY,
        timeout_s=TIMEOUT_S,
    )

    if not subset_pairs:
        print(f"No sequences selected for {length} mer (min_on={min_on}, max_on={max_on}).")
        return

    on_e_subset, _, _ = sc.compute_ontarget_energies(subset_pairs)
    off_e_subset = sc.compute_offtarget_energies(subset_pairs)

    fivep_tag = FIVEP_EXT if FIVEP_EXT else "none"
    threep_tag = THREEP_EXT if THREEP_EXT else "none"
    out_name = f"hist_sigma1_{length}mer_5p-{fivep_tag}_3p-{threep_tag}.svg"
    out_path = os.path.join(OUT_DIR, out_name) if OUT_DIR else out_name

    print(
        f"Plotting {length} mer (n={len(subset_pairs)}) -> {out_path}"
    )
    sc.plot_on_off_target_histograms(
        on_e_subset,
        off_e_subset,
        output_path=out_path,
        show_plot=SHOW_PLOT,
        vlines={"min_ontarget": min_on, "max_ontarget": max_on},
    )


def main():
    csv_paths = _find_csvs(RESULTS_DIR)
    if not csv_paths:
        raise FileNotFoundError(f"No CSVs found in {RESULTS_DIR}")

    if OUT_DIR:
        os.makedirs(OUT_DIR, exist_ok=True)

    metas = []
    for path in csv_paths:
        meta = _extract_metadata(path, sigma_target=SIGMA_TARGET)
        if meta is not None:
            metas.append(meta)

    if not metas:
        raise ValueError(f"No sigma={SIGMA_TARGET} CSVs found in {RESULTS_DIR}")

    for meta in sorted(metas, key=lambda m: m["length"]):
        _run_for_length(meta)


if __name__ == "__main__":
    RESULTS_DIR = os.path.join(os.path.dirname(__file__), "data", "noflank_results")
    OUT_DIR = os.path.join(RESULTS_DIR, "plots_explore")
    main()
