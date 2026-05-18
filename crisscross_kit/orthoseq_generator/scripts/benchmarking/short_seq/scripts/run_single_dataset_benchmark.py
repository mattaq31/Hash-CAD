#!/usr/bin/env python3
"""
Run the saved-dataset benchmark workflow for one selected dataset only.

Purpose
-------
This is a focused utility for spot checks and one-off comparisons when the
full batch runner would be unnecessary. It applies the same benchmark logic as
the batch workflow, but only to the configured dataset and benchmark run name.
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_algorithms import (
    run_hybrid_search_offline_to_xlsx,
    run_naive_search_to_xlsx,
    run_vertex_cover_search_to_xlsx,
)
from benchmark_analysis import find_offtarget_limits_for_target_densities
from benchmark_dataset_tools import load_dataset


DATASET_PARENT_NAME = "len4_7_tttt5p"
DATASET_NAME = "len7"
BENCHMARK_NAME = "benchmark_test3_new_point"
TARGET_CONFLICT_DENSITIES = [0.2]
SEEDS = [41]
SELF_ENERGY_LIMIT = -2.0
RUN_NAIVE = False
RUN_VERTEX_COVER = False
RUN_HYBRID = True

VC_CORE_PARAMS = {
    "prune_fraction": 0.2,
    "vc_max_iterations": 1000,
}

HYBRID_PARAMS = {
    "initial_fresh_pair_count": 2000,
    **VC_CORE_PARAMS,
}

VERTEX_COVER_PARAMS = {
    **VC_CORE_PARAMS,
}


def read_found_pair_count(report_path: Path) -> int:
    """Read the found-pair count from a benchmark workbook."""
    selected_pairs = pd.read_excel(report_path, sheet_name="found_pairs")
    return int(len(selected_pairs))


def make_plot(summary_df: pd.DataFrame) -> None:
    """Plot the single-dataset benchmark summary currently held in memory."""
    algorithm_flags = {
        "naive": RUN_NAIVE,
        "vertex_cover": RUN_VERTEX_COVER,
        "hybrid_offline": RUN_HYBRID,
    }
    algorithms = [algorithm for algorithm, enabled in algorithm_flags.items() if enabled]
    colors = {
        "naive": "#4C78A8",
        "vertex_cover": "#F58518",
        "hybrid_offline": "#54A24B",
    }

    density_labels = [f"{density:.1f}" for density in TARGET_CONFLICT_DENSITIES]
    x = np.arange(len(TARGET_CONFLICT_DENSITIES))
    width = 0.22
    offsets = {
        "naive": -width,
        "vertex_cover": 0.0,
        "hybrid_offline": width,
    }

    fig, ax = plt.subplots(figsize=(10, 6))

    for algorithm in algorithms:
        algo_df = summary_df[summary_df["algorithm"] == algorithm]
        if algo_df.empty:
            continue
        means = []
        stds = []
        for density in TARGET_CONFLICT_DENSITIES:
            values = algo_df.loc[algo_df["target_conflict_density"] == density, "found_pair_count"].to_numpy(dtype=float)
            if len(values) == 0:
                means.append(np.nan)
                stds.append(0.0)
                continue
            means.append(float(np.mean(values)))
            stds.append(float(np.std(values, ddof=1)) if len(values) > 1 else 0.0)

        bar_x = x + offsets[algorithm]
        ax.bar(
            bar_x,
            means,
            width=width,
            yerr=stds,
            capsize=4,
            color=colors[algorithm],
            alpha=0.75,
            label=algorithm,
        )

        for density_idx, density in enumerate(TARGET_CONFLICT_DENSITIES):
            values = algo_df.loc[algo_df["target_conflict_density"] == density, "found_pair_count"].to_numpy(dtype=float)
            if len(values) == 0:
                continue
            dot_x = np.full(len(values), bar_x[density_idx])
            if len(values) > 1:
                dot_x += np.linspace(-0.04, 0.04, len(values))
            ax.scatter(dot_x, values, color="black", s=18, zorder=3)

    ax.set_title(f"Benchmark Results for {DATASET_NAME}")
    ax.set_xlabel("Target Conflict Density")
    ax.set_ylabel("Number of pairs found")
    ax.set_xticks(x)
    ax.set_xticklabels(density_labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    dataset_dir = MODULE_DIR / "data" / DATASET_PARENT_NAME / DATASET_NAME
    dataset = load_dataset(dataset_dir)
    cutoff_summaries = find_offtarget_limits_for_target_densities(dataset, TARGET_CONFLICT_DENSITIES)
    benchmark_name = BENCHMARK_NAME
    results_dir = dataset_dir / "results" / benchmark_name
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"dataset: {dataset_dir}")
    print(f"benchmark name: {benchmark_name}")
    print(f"self_energy_limit: {SELF_ENERGY_LIMIT}")
    print("cutoff summaries:")
    for summary in cutoff_summaries:
        print(summary)

    summary_rows = []

    for cutoff_summary in cutoff_summaries:
        target_density = float(cutoff_summary["target_conflict_density"])
        offtarget_limit = float(cutoff_summary["selected_offtarget_limit"])
        achieved_density = float(cutoff_summary["achieved_conflict_density"])
        density_label = str(target_density).replace(".", "p")
        cutoff_label = str(offtarget_limit).replace(".", "p")

        for seed in SEEDS:
            if RUN_NAIVE:
                print(f"running naive | target_density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                naive_path = results_dir / f"density{density_label}_naive_limit{cutoff_label}_seed{seed}.xlsx"
                run_naive_search_to_xlsx(
                    dataset_dir,
                    output_path=naive_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=SELF_ENERGY_LIMIT,
                    random_seed=seed,
                )
                summary_rows.append(
                    {
                        "dataset": DATASET_NAME,
                        "algorithm": "naive",
                        "target_conflict_density": target_density,
                        "selected_offtarget_limit": offtarget_limit,
                        "achieved_conflict_density": achieved_density,
                        "self_energy_limit": SELF_ENERGY_LIMIT,
                        "seed": seed,
                        "found_pair_count": read_found_pair_count(naive_path),
                        "report_path": str(naive_path),
                    }
                )

            if RUN_VERTEX_COVER:
                print(f"running vertex_cover | target_density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                vc_path = results_dir / f"density{density_label}_vertex_cover_limit{cutoff_label}_seed{seed}.xlsx"
                run_vertex_cover_search_to_xlsx(
                    dataset_dir,
                    output_path=vc_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=SELF_ENERGY_LIMIT,
                    random_seed=seed,
                    **VERTEX_COVER_PARAMS,
                )
                summary_rows.append(
                    {
                        "dataset": DATASET_NAME,
                        "algorithm": "vertex_cover",
                        "target_conflict_density": target_density,
                        "selected_offtarget_limit": offtarget_limit,
                        "achieved_conflict_density": achieved_density,
                        "self_energy_limit": SELF_ENERGY_LIMIT,
                        "seed": seed,
                        "found_pair_count": read_found_pair_count(vc_path),
                        "report_path": str(vc_path),
                    }
                )

            if RUN_HYBRID:
                print(f"running hybrid_offline | target_density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                hybrid_path = results_dir / f"density{density_label}_hybrid_offline_limit{cutoff_label}_seed{seed}.xlsx"
                run_hybrid_search_offline_to_xlsx(
                    dataset_dir,
                    output_path=hybrid_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=SELF_ENERGY_LIMIT,
                    random_seed=seed,
                    **HYBRID_PARAMS,
                )
                summary_rows.append(
                    {
                        "dataset": DATASET_NAME,
                        "algorithm": "hybrid_offline",
                        "target_conflict_density": target_density,
                        "selected_offtarget_limit": offtarget_limit,
                        "achieved_conflict_density": achieved_density,
                        "self_energy_limit": SELF_ENERGY_LIMIT,
                        "seed": seed,
                        "found_pair_count": read_found_pair_count(hybrid_path),
                        "report_path": str(hybrid_path),
                    }
                )

    summary_df = pd.DataFrame(summary_rows)
    make_plot(summary_df)
