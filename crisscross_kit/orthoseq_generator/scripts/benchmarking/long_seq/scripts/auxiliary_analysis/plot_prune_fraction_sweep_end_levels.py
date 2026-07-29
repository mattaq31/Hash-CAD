#!/usr/bin/env python3
"""
Plot final retained pair counts from the prune-fraction sweep outputs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_plot_tables(report_paths):
    result_rows = []
    baseline_rows = []
    for report_path in report_paths:
        results_df = pd.read_excel(report_path, sheet_name="results")
        trajectories_df = pd.read_excel(report_path, sheet_name="trajectories")
        result_rows.append(results_df)
        baseline_rows.append(
            trajectories_df[trajectories_df["iteration"] == 0][
                [
                    "report_name",
                    "sequence_length",
                    "init_count",
                    "prune_fraction",
                    "independent_set_size",
                ]
            ].drop_duplicates()
        )
    return (
        pd.concat(result_rows, ignore_index=True),
        pd.concat(baseline_rows, ignore_index=True),
    )


def summarize_results(results_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        results_df.groupby(
            ["sequence_length", "init_count", "prune_fraction"],
            as_index=False,
        )
        .agg(
            retained_pair_count_mean=("retained_pair_count", "mean"),
            retained_pair_count_std=("retained_pair_count", "std"),
        )
    )
    summary["retained_pair_count_std"] = summary["retained_pair_count_std"].fillna(0.0)
    return summary


def summarize_baseline(baseline_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        baseline_df.groupby(
            ["sequence_length", "init_count"],
            as_index=False,
        )
        .agg(
            independent_set_size_mean=("independent_set_size", "mean"),
            independent_set_size_std=("independent_set_size", "std"),
        )
    )
    summary["independent_set_size_std"] = summary["independent_set_size_std"].fillna(0.0)
    return summary


def make_plot(results_df, baseline_df, output_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matplotlib.rcParams["font.family"] = "Arial"
    matplotlib.rcParams["svg.fonttype"] = "none"

    init_colors = {
        250: "#0072B2",
        450: "#D55E00",
        900: "#009E73",
    }
    init_markers = {
        250: "o",
        450: "s",
        900: "^",
    }
    baseline_linestyles = {
        250: "--",
        450: "-.",
        900: ":",
    }

    results_summary_df = summarize_results(results_df)
    baseline_summary_df = summarize_baseline(baseline_df)

    figure_width_mm = 177.8
    figure_height_mm = 58.0
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(figure_width_mm / 25.4, figure_height_mm / 25.4),
        sharey=False,
    )

    for ax, length in zip(axes, [10, 16, 20], strict=True):
        for init_count in [250, 450, 900]:
            subset = results_summary_df[
                (results_summary_df["sequence_length"] == length)
                & (results_summary_df["init_count"] == init_count)
            ].sort_values("prune_fraction")
            baseline_subset = baseline_summary_df[
                (baseline_summary_df["sequence_length"] == length)
                & (baseline_summary_df["init_count"] == init_count)
            ]

            ax.errorbar(
                subset["prune_fraction"],
                subset["retained_pair_count_mean"],
                yerr=subset["retained_pair_count_std"],
                color=init_colors[init_count],
                marker=init_markers[init_count],
                linestyle="-",
                linewidth=1.0,
                markersize=3.0,
                elinewidth=0.8,
                capsize=1.8,
                label=f"Subset size = {init_count}",
            )
            if not baseline_subset.empty:
                baseline_mean = float(baseline_subset["independent_set_size_mean"].iloc[0])
                baseline_std = float(baseline_subset["independent_set_size_std"].iloc[0])
                ax.axhline(
                    baseline_mean,
                    color=init_colors[init_count],
                    linestyle=baseline_linestyles[init_count],
                    linewidth=1.0,
                    alpha=1.0,
                )
                if baseline_std > 0.0:
                    ax.axhspan(
                        baseline_mean - baseline_std,
                        baseline_mean + baseline_std,
                        color=init_colors[init_count],
                        alpha=0.10,
                        linewidth=0.0,
                    )
        ax.axvline(0.2, color="black", linestyle="--", linewidth=0.8, alpha=0.8)
        ax.set_title(f"Length = {length}", fontsize=8, pad=4)
        ax.set_xlabel("Prune fraction", fontsize=6)
        ax.tick_params(axis="both", labelsize=6, width=0.5, length=2)

        for spine in ax.spines.values():
            spine.set_linewidth(0.5)

    axes[0].set_ylabel("Orthogonal pairs found", fontsize=6)
    axes[-1].legend(
        loc="best",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=6,
        handlelength=1.5,
        borderaxespad=0.2,
    )

    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.22, top=0.88, wspace=0.18)
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = (
        module_dir
        / "data"
        / "batch_x_TTTT_sigma1p0_seed41"
        / "auxiliary_analysis"
        / "prune_fraction_sweep"
    )
    plot_output_dir = module_dir / "plots"
    plot_output_dir.mkdir(parents=True, exist_ok=True)

    report_paths = sorted(output_dir.glob("hybrid_len*_5p_TTTT_limitm8p16_budget10000000_init*_seed41_prune_fraction_sweep*.xlsx"))

    results_df, baseline_df = load_plot_tables(report_paths)
    output_path = plot_output_dir / "prune_fraction_sweep_end_levels.svg"
    make_plot(results_df, baseline_df, output_path)
    print(f"wrote plot: {output_path}")
