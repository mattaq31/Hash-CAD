"""
Purpose:
    Plot comparison results produced by compare_algorithms_from_pkl.py.
    X axis: offtarget limit
    Y axis: independent set size
    One plot per input results file.
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt


def _format_title(df, base_name):
    # Pull one row of metadata for display.
    num_vertices = df["num_vertices"].iloc[0] if "num_vertices" in df else None
    length = df["sequence_length"].iloc[0] if "sequence_length" in df else None
    range_sigma = df["range_sigma"].iloc[0] if "range_sigma" in df else None
    min_on = df["min_on"].iloc[0] if "min_on" in df else None
    max_on = df["max_on"].iloc[0] if "max_on" in df else None

    parts = [base_name]
    if num_vertices is not None:
        parts.append(f"n={num_vertices}")
    if length is not None:
        parts.append(f"length={length}")
    if range_sigma is not None:
        parts.append(f"sigma={range_sigma}")
    if min_on is not None and max_on is not None:
        parts.append(f"on=[{min_on:.3f},{max_on:.3f}]")

    return " | ".join(parts)


def plot_results(results_path, out_dir=None):
    # Accept either PKL or CSV results.
    df = pd.read_pickle(results_path) if results_path.endswith(".pkl") else pd.read_csv(results_path)
    if df.empty:
        print(f"No data in {results_path}")
        return

    base_name = os.path.splitext(os.path.basename(results_path))[0]
    title = _format_title(df, base_name)

    fig, ax = plt.subplots(figsize=(8, 5))

    # Scatter one set of points per algorithm.
    for run_type in sorted(df["run_type"].unique()):
        subset = df[df["run_type"] == run_type]
        ax.scatter(
            subset["offtarget_limit"],
            subset["independent_set_size"],
            alpha=0.7,
            s=24,
            label=run_type,
        )

    ax.set_xlabel("Off-target limit")
    ax.set_ylabel("Independent set size")
    ax.set_title(title)
    ax.legend(frameon=False)

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Minimal defaults for manual runs.
    OUTPUT_DIR = "results"
    RESULTS_PATHS = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_compare_results.pkl")))
    RESULTS_PATHS = [os.path.join(OUTPUT_DIR,"short_seq_5mer_sigma1p0_subset_compare_results.pkl")]
    for path in RESULTS_PATHS:
        plot_results(path)
