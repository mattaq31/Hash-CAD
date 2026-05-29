#!/usr/bin/env python3
"""
Plot saved benchmark workbooks for one named batch benchmark run.

Purpose
-------
This script is the final reporting step of the saved-dataset benchmark
workflow. It reads the XLSX outputs produced by `run_batch_benchmark.py` for
the configured benchmark run name, groups the results by extension condition,
and writes the summary SVG plots at the dataset-parent level.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["svg.fonttype"] = "none"

MODULE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from orthoseq_generator.search_report_reader import load_metadata


DATASET_PARENT_NAME = "len4_7_tttt5p_noGGGG"
BENCHMARK_NAME = "benchmark_x"
ALGORITHM_ORDER = ["naive", "vertex_cover", "hybrid_offline"]
ALGORITHM_COLORS = {
    "naive": "#808080",
    "vertex_cover": "#3B6FB6",
    "hybrid_offline": "#2A9D8F",
}
HYBRID_VARIANT_COLORS = [
    "#2A9D8F",
    "#63B7AF",
    "#9FD4CF",
    "#BFE3DE",
    "#D7EFEB",
]
ALGORITHM_LABELS = {
    "naive": "Naive",
    "vertex_cover": "Vertex cover",
    "hybrid_offline": "Hybrid",
}
OUTPUT_FILENAME_STEM = "batch_benchmark_found_pair_count"
SUMMARY_FILENAME_STEM = "batch_benchmark_found_pair_count_summary"
MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.48 * 1.10
FIGURE_HEIGHT_MM = 58.0
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 8
AXIS_LABEL_FONT_SIZE = 8
TICK_LABEL_FONT_SIZE = 6
LEGEND_FONT_SIZE = 6
DENSITY_LABEL_FONT_SIZE = 6

AXIS_LINEWIDTH = 0.5
GRID_LINEWIDTH = 0.5
BAR_EDGE_LINEWIDTH = 0.5
ERRORBAR_LINEWIDTH = 0.5

GROUP_TITLES = {
    False: "No extension",
    True: "5' TTTT extension",
}


def dataset_sort_key(dataset_dir: Path):
    """Sort datasets by extension condition, then length, then name."""
    name = dataset_dir.name
    match = re.match(r"len(\d+)(?:_tttt5p)?$", name)
    length = int(match.group(1)) if match else 999
    has_tttt5p = name.endswith("_tttt5p")
    return (has_tttt5p, length, name)


def find_benchmark_dirs(parent_dir: Path) -> list[Path]:
    """Find the per-dataset result directories for the configured benchmark run."""
    benchmark_name = BENCHMARK_NAME
    benchmark_dirs = []
    dataset_dirs = sorted(
        [
            child
            for child in parent_dir.iterdir()
            if child.is_dir() and (child / "dataset.toml").exists() and (child / "dataset.npz").exists()
        ],
        key=dataset_sort_key,
    )
    for dataset_dir in dataset_dirs:
        benchmark_dir = dataset_dir / "results" / benchmark_name
        if not benchmark_dir.exists():
            continue
        benchmark_dirs.append(benchmark_dir)
    return benchmark_dirs


def parse_run_filename(report_path: Path) -> dict | None:
    """Parse one benchmark workbook filename into its run parameters."""
    match = re.match(
        r"density(?P<density>[0-9p]+)_(?P<algorithm>naive|vertex_cover|hybrid_offline)_limit(?P<cutoff>[-0-9p]+)(?:_(?P<variant>.+?))?_seed(?P<seed>\d+)\.xlsx$",
        report_path.name,
    )
    if not match:
        return None
    return {
        "target_conflict_density": float(match.group("density").replace("p", ".")),
        "algorithm": match.group("algorithm"),
        "selected_offtarget_limit_label": match.group("cutoff"),
        "variant_label": match.group("variant"),
        "seed": int(match.group("seed")),
    }


def build_plot_series_specs(runs_df: pd.DataFrame) -> list[dict]:
    """Build the ordered bar series shown in each density subgroup."""
    series_specs = [
        {
            "key": "naive",
            "algorithm": "naive",
            "initial_fresh_pair_count": None,
            "label": ALGORITHM_LABELS["naive"],
            "color": ALGORITHM_COLORS["naive"],
        },
        {
            "key": "vertex_cover",
            "algorithm": "vertex_cover",
            "initial_fresh_pair_count": None,
            "label": ALGORITHM_LABELS["vertex_cover"],
            "color": ALGORITHM_COLORS["vertex_cover"],
        },
    ]

    hybrid_df = runs_df[runs_df["algorithm"] == "hybrid_offline"]
    if hybrid_df.empty:
        return series_specs

    hybrid_inits = sorted(
        {
            int(value)
            for value in hybrid_df["initial_fresh_pair_count"].dropna().unique().tolist()
        },
        reverse=True,
    )
    if hybrid_inits:
        for idx, init_count in enumerate(hybrid_inits):
            series_specs.append(
                {
                    "key": f"hybrid_offline_init{init_count}",
                    "algorithm": "hybrid_offline",
                    "initial_fresh_pair_count": int(init_count),
                    "label": f"Hybrid {int(init_count)}",
                    "color": HYBRID_VARIANT_COLORS[idx % len(HYBRID_VARIANT_COLORS)],
                }
            )
        return series_specs

    series_specs.append(
        {
            "key": "hybrid_offline",
            "algorithm": "hybrid_offline",
            "initial_fresh_pair_count": None,
            "label": ALGORITHM_LABELS["hybrid_offline"],
            "color": ALGORITHM_COLORS["hybrid_offline"],
        }
    )
    return series_specs


def build_plot_series_key(algorithm: str, initial_fresh_pair_count: int | None) -> str:
    """Build the grouping key used for plot aggregation."""
    if algorithm != "hybrid_offline" or initial_fresh_pair_count is None:
        return algorithm
    return f"hybrid_offline_init{int(initial_fresh_pair_count)}"


def collect_runs(parent_dir: Path) -> pd.DataFrame:
    """Collect plotted benchmark rows from all datasets in the parent."""
    rows = []
    for benchmark_dir in find_benchmark_dirs(parent_dir):
        dataset_dir = benchmark_dir.parent.parent
        for report_path in sorted(benchmark_dir.glob("*.xlsx")):
            parsed = parse_run_filename(report_path)
            if parsed is None:
                continue
            metadata = load_metadata(report_path)
            length = metadata.get("input.length")
            if length is None:
                length = metadata.get("dataset.length")
            fivep_ext = metadata.get("input.fivep_ext")
            if fivep_ext is None:
                fivep_ext = metadata.get("dataset.fivep_ext")
            initial_fresh_pair_count = metadata.get("search.initial_fresh_pair_count")
            rows.append(
                {
                    "dataset_name": dataset_dir.name,
                    "length": int(length),
                    "fivep_ext": str(fivep_ext or ""),
                    "has_tttt5p": str(fivep_ext or "") == "TTTT",
                    "algorithm": parsed["algorithm"],
                    "variant_label": parsed["variant_label"],
                    "initial_fresh_pair_count": initial_fresh_pair_count,
                    "plot_series_key": build_plot_series_key(
                        parsed["algorithm"],
                        initial_fresh_pair_count,
                    ),
                    "seed": parsed["seed"],
                    "target_conflict_density": parsed["target_conflict_density"],
                    "found_pair_count": int(metadata["found_pair_count"]),
                    "report_path": str(report_path),
                }
            )
    return pd.DataFrame(rows)


def format_count(value: float) -> str:
    """Format one plotted count for compact labels and summary output."""
    rounded = round(float(value))
    if abs(float(value) - rounded) < 1e-9:
        return str(int(rounded))
    return f"{float(value):.1f}".rstrip("0").rstrip(".")


def build_summary_table(runs_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate plotted values and compute improvements versus naive."""
    grouped = (
        runs_df.groupby(
            ["has_tttt5p", "length", "target_conflict_density", "plot_series_key", "algorithm"],
            dropna=False,
        )["found_pair_count"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(
            columns={
                "mean": "mean_found_pair_count",
                "std": "std_found_pair_count",
                "count": "run_count",
            }
        )
    )
    if grouped.empty:
        return grouped

    grouped["std_found_pair_count"] = grouped["std_found_pair_count"].fillna(0.0)
    grouped["sem_found_pair_count"] = grouped["std_found_pair_count"] / np.sqrt(grouped["run_count"].clip(lower=1))

    naive_means = grouped.loc[
        grouped["plot_series_key"] == "naive",
        ["has_tttt5p", "length", "target_conflict_density", "mean_found_pair_count"],
    ].rename(columns={"mean_found_pair_count": "naive_mean_found_pair_count"})
    grouped = grouped.merge(
        naive_means,
        on=["has_tttt5p", "length", "target_conflict_density"],
        how="left",
    )
    grouped["absolute_improvement_vs_naive"] = (
        grouped["mean_found_pair_count"] - grouped["naive_mean_found_pair_count"]
    )
    grouped["percent_improvement_vs_naive"] = np.where(
        grouped["naive_mean_found_pair_count"] > 0,
        100.0 * grouped["absolute_improvement_vs_naive"] / grouped["naive_mean_found_pair_count"],
        np.nan,
    )
    grouped.loc[grouped["plot_series_key"] == "naive", "absolute_improvement_vs_naive"] = 0.0
    grouped.loc[grouped["plot_series_key"] == "naive", "percent_improvement_vs_naive"] = 0.0
    return grouped


def build_export_table(summary_df: pd.DataFrame, series_specs: list[dict]) -> pd.DataFrame:
    """Build a human-readable Excel table for the plotted summary values."""
    if summary_df.empty:
        return summary_df

    series_order = {spec["key"]: idx for idx, spec in enumerate(series_specs)}
    series_labels = {spec["key"]: spec["label"] for spec in series_specs}
    export_df = summary_df.copy()
    export_df["series_label"] = export_df["plot_series_key"].map(series_labels).fillna(export_df["plot_series_key"])
    export_df["extension_condition"] = export_df["has_tttt5p"].map(GROUP_TITLES)
    export_df["series_order"] = export_df["plot_series_key"].map(series_order).fillna(len(series_specs))
    export_df = export_df.sort_values(
        ["has_tttt5p", "length", "target_conflict_density", "series_order"],
        ignore_index=True,
    )
    export_df["mean_found_pair_count"] = export_df["mean_found_pair_count"].map(format_count)
    export_df["std_found_pair_count"] = export_df["std_found_pair_count"].map(format_count)
    export_df["sem_found_pair_count"] = export_df["sem_found_pair_count"].map(format_count)
    export_df["naive_mean_found_pair_count"] = export_df["naive_mean_found_pair_count"].map(format_count)
    export_df["absolute_improvement_vs_naive"] = export_df["absolute_improvement_vs_naive"].map(format_count)
    export_df["percent_improvement_vs_naive"] = export_df["percent_improvement_vs_naive"].map(
        lambda value: "" if pd.isna(value) else f"{float(value):+.1f}%"
    )
    return export_df[
        [
            "extension_condition",
            "length",
            "target_conflict_density",
            "series_label",
            "algorithm",
            "run_count",
            "mean_found_pair_count",
            "sem_found_pair_count",
            "std_found_pair_count",
            "naive_mean_found_pair_count",
            "absolute_improvement_vs_naive",
            "percent_improvement_vs_naive",
        ]
    ]


def compute_plot_y_max(summary_df: pd.DataFrame) -> float:
    """Compute the y-axis maximum for one plotted benchmark subset."""
    if summary_df.empty:
        return 1.0

    y_max = float((summary_df["mean_found_pair_count"] + summary_df["sem_found_pair_count"]).max())
    return max(1.0, y_max * 1.08 + 2.0)


def slugify_title_suffix(title_suffix: str) -> str:
    """Convert a plot title suffix into a filesystem-safe filename suffix."""
    slug = title_suffix.lower()
    slug = slug.replace("5'", "5prime")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def plot_group(
    group_summary_df: pd.DataFrame,
    *,
    has_tttt5p: bool,
    shared_y_max: float,
    series_specs: list[dict],
) -> tuple[plt.Figure, str] | None:
    """Plot one extension-condition subset of the benchmark runs."""
    if group_summary_df.empty:
        return None

    lengths = sorted(group_summary_df["length"].unique())
    densities = sorted(group_summary_df["target_conflict_density"].unique())

    bars_per_length = len(densities) * len(series_specs)
    bar_width = 0.45
    length_gap = 0.9
    subgroup_gap = 0.3

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    length_xticks = []
    length_xticklabels = []
    subgroup_annotations = []

    for length_idx, length in enumerate(lengths):
        length_start = length_idx * (bars_per_length * bar_width + len(densities) * subgroup_gap + length_gap)
        length_center = length_start + 0.5 * ((bars_per_length - 1) * bar_width + (len(densities) - 1) * subgroup_gap)
        length_xticks.append(length_center)
        length_xticklabels.append(str(length))

        for density_idx, density in enumerate(densities):
            subgroup_start = length_start + density_idx * (len(series_specs) * bar_width + subgroup_gap)
            subgroup_max = 0.0
            for series_idx, series_spec in enumerate(series_specs):
                x = subgroup_start + series_idx * bar_width
                summary_row = group_summary_df.loc[
                    (group_summary_df["length"] == length)
                    & (group_summary_df["target_conflict_density"] == density)
                    & (group_summary_df["plot_series_key"] == series_spec["key"])
                ]
                if summary_row.empty:
                    continue
                summary = summary_row.iloc[0]

                mean_value = float(summary["mean_found_pair_count"])
                sem_value = float(summary["sem_found_pair_count"])
                subgroup_max = max(subgroup_max, mean_value + sem_value)

                ax.bar(
                    x,
                    mean_value,
                    width=bar_width,
                    yerr=sem_value,
                    capsize=1,
                    color=series_spec["color"],
                    edgecolor="black",
                    linewidth=BAR_EDGE_LINEWIDTH,
                    error_kw={"elinewidth": ERRORBAR_LINEWIDTH, "capthick": ERRORBAR_LINEWIDTH},
                    alpha=1.0,
                    label=series_spec["label"] if (length_idx == 0 and density_idx == 0) else None,
                )

            subgroup_center = subgroup_start + 0.5 * ((len(series_specs) - 1) * bar_width)
            subgroup_annotations.append((subgroup_center, density, subgroup_max))

    title_suffix = GROUP_TITLES[has_tttt5p]
    ax.set_title(title_suffix, fontsize=TITLE_FONT_SIZE, pad=6)
    ax.set_xlabel("Sequence length", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Number of pairs found", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(length_xticks)
    ax.set_xticklabels(length_xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_ylim(0, shared_y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=2)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=2)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        handlelength=1.0,
        borderaxespad=0.2,
    )

    for x_pos, density, subgroup_max in subgroup_annotations:
        label_y = min(shared_y_max * 0.98, subgroup_max + shared_y_max * 0.10 if subgroup_max > 0 else shared_y_max * 0.94)
        ax.text(
            x_pos,
            label_y,
            f"{density:.1f}",
            ha="center",
            va="top",
            fontsize=DENSITY_LABEL_FONT_SIZE,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.20, top=0.88)
    return fig, title_suffix


def save_plot(fig: plt.Figure, output_dir: Path, title_suffix: str) -> Path:
    """Write one benchmark plot SVG and return its output path."""
    benchmark_slug = slugify_title_suffix(BENCHMARK_NAME)
    output_path = output_dir / f"{OUTPUT_FILENAME_STEM}_{benchmark_slug}_{slugify_title_suffix(title_suffix)}.svg"
    fig.savefig(output_path, format="svg")
    return output_path


def save_summary_workbook(summary_df: pd.DataFrame, output_dir: Path, series_specs: list[dict]) -> Path:
    """Write the plot summary values and naive-relative improvements as XLSX."""
    benchmark_slug = slugify_title_suffix(BENCHMARK_NAME)
    output_path = output_dir / f"{SUMMARY_FILENAME_STEM}_{benchmark_slug}.xlsx"
    export_df = build_export_table(summary_df, series_specs)
    export_df.to_excel(output_path, index=False, sheet_name="summary")
    return output_path


if __name__ == "__main__":
    parent_dir = MODULE_DIR / "data" / DATASET_PARENT_NAME
    runs_df = collect_runs(parent_dir)
    series_specs = build_plot_series_specs(runs_df)
    summary_df = build_summary_table(runs_df)
    shared_y_max = compute_plot_y_max(summary_df)

    print(f"dataset parent: {parent_dir}")
    print(f"loaded runs: {len(runs_df)}")
    print(f"plot series: {[spec['label'] for spec in series_specs]}")
    print(f"shared y max: {shared_y_max:.2f}")
    summary_path = save_summary_workbook(summary_df, parent_dir, series_specs)
    print(f"wrote summary workbook: {summary_path}")

    for has_tttt5p in (False, True):
        plot_result = plot_group(
            summary_df[summary_df["has_tttt5p"] == has_tttt5p],
            has_tttt5p=has_tttt5p,
            shared_y_max=shared_y_max,
            series_specs=series_specs,
        )
        if plot_result is None:
            continue
        fig, title_suffix = plot_result
        output_path = save_plot(fig, parent_dir, title_suffix)
        print(f"wrote plot: {output_path}")
        plt.close(fig)
