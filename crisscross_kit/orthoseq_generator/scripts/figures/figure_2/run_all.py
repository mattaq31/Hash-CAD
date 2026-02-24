"""
Purpose:
    Minimal end-to-end run: compute -> compare -> plot.
"""

import os
import glob

from compute_short_seq_energies import run_compute_short_seq
from compare_algorithms_from_pkl import run_compare
from plot_compare_results import plot_results


def main():
    # Minimal defaults for a quick end-to-end run.
    output_dir = "results"
    lengths = [5]
    range_sigmas = [0.5]

    num_runs = 10
    offtarget_step = 0.1
    target_conflict_prob = 0.5

    # Step 1: compute energies and produce PKLs.
    pkl_paths = []
    for length in lengths:
        for sigma in range_sigmas:
            pkl_paths.append(
                run_compute_short_seq(
                    length=length,
                    range_sigma=sigma,
                    output_dir=output_dir,
                )
            )

    # Step 2: compare algorithms for each PKL.
    for pkl_path in pkl_paths:
        run_compare(
            pkl_path,
            num_runs=num_runs,
            offtarget_step=offtarget_step,
            target_conflict_prob=target_conflict_prob,
            limit=float("inf"),
            output_dir=output_dir,
            show_progress=False,
        )

    # Step 3: plot all compare results from the output folder.
    result_paths = sorted(glob.glob(os.path.join(output_dir, "*_compare_results.pkl")))
    for path in result_paths:
        plot_results(path)


if __name__ == "__main__":
    main()
