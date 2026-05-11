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

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


DATASET_PARENT_NAME = "len4_7_tttt5p"
BENCHMARK_NAME = "benchmark_2"
ALGORITHM_ORDER = ["naive", "vertex_cover", "hybrid_offline"]
ALGORITHM_COLORS = {
    "naive": "#808080",
    "vertex_cover": "#3B6FB6",
    "hybrid_offline": "#2A9D8F",
}
ALGORITHM_LABELS = {
    "naive": "Naive",
    "vertex_cover": "Vertex cover",
    "hybrid_offline": "Hybrid",
}
OUTPUT_FILENAME_STEM = "batch_benchmark_found_pair_count"
MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.48
FIGURE_HEIGHT_MM = 58.0
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 5
AXIS_LABEL_FONT_SIZE = 5
TICK_LABEL_FONT_SIZE = 5
LEGEND_FONT_SIZE = 5
DENSITY_LABEL_FONT_SIZE = 5

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


def find_latest_benchmark_dirs(parent_dir: Path) -> list[Path]:
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
        r"density(?P<density>[0-9p]+)_(?P<algorithm>naive|vertex_cover|hybrid_offline)_limit(?P<cutoff>[-0-9p]+)_seed(?P<seed>\d+)\.xlsx$",
        report_path.name,
    )
    if not match:
        return None
    return {
        "target_conflict_density": float(match.group("density").replace("p", ".")),
        "algorithm": match.group("algorithm"),
        "selected_offtarget_limit_label": match.group("cutoff"),
        "seed": int(match.group("seed")),
    }


def read_metadata_value(metadata_df: pd.DataFrame, key: str):
    """Return one value from the workbook metadata sheet by key."""
    rows = metadata_df.loc[metadata_df["key"] == key, "value"]
    if rows.empty:
        return None
    return rows.iloc[0]


def read_metadata_value_with_fallback(metadata_df: pd.DataFrame, primary_key: str, fallback_key: str):
    """Read one metadata value, falling back to a legacy key when needed."""
    primary_value = read_metadata_value(metadata_df, primary_key)
    return primary_value if primary_value is not None else read_metadata_value(metadata_df, fallback_key)


def collect_runs(parent_dir: Path) -> pd.DataFrame:
    """Collect plotted benchmark rows from all datasets in the parent."""
    rows = []
    for benchmark_dir in find_latest_benchmark_dirs(parent_dir):
        dataset_dir = benchmark_dir.parent.parent
        for report_path in sorted(benchmark_dir.glob("*.xlsx")):
            parsed = parse_run_filename(report_path)
            if parsed is None:
                continue
            metadata_df = pd.read_excel(report_path, sheet_name="run_metadata")
            length = read_metadata_value_with_fallback(metadata_df, "input.length", "dataset.length")
            fivep_ext = read_metadata_value_with_fallback(metadata_df, "input.fivep_ext", "dataset.fivep_ext")
            rows.append(
                {
                    "dataset_name": dataset_dir.name,
                    "length": int(length),
                    "fivep_ext": str(fivep_ext or ""),
                    "has_tttt5p": str(fivep_ext or "") == "TTTT",
                    "algorithm": parsed["algorithm"],
                    "seed": parsed["seed"],
                    "target_conflict_density": parsed["target_conflict_density"],
                    "found_pair_count": int(read_metadata_value(metadata_df, "found_pair_count")),
                    "report_path": str(report_path),
                }
            )
    return pd.DataFrame(rows)


def compute_shared_y_max(runs_df: pd.DataFrame) -> float:
    """Compute a shared y-axis maximum across all grouped benchmark bars."""
    grouped = (
        runs_df.groupby(["has_tttt5p", "length", "target_conflict_density", "algorithm"])["found_pair_count"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    if grouped.empty:
        return 1.0

    grouped["std"] = grouped["std"].fillna(0.0)
    grouped["sem"] = grouped["std"] / np.sqrt(grouped["count"].clip(lower=1))
    y_max = float((grouped["mean"] + grouped["sem"]).max())
    return max(1.0, y_max * 1.08 + 2.0)


def slugify_title_suffix(title_suffix: str) -> str:
    """Convert a plot title suffix into a filesystem-safe filename suffix."""
    slug = title_suffix.lower()
    slug = slug.replace("5'", "5prime")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def plot_group(group_df: pd.DataFrame, *, has_tttt5p: bool, shared_y_max: float) -> tuple[plt.Figure, str] | None:
    """Plot one extension-condition subset of the benchmark runs."""
    if group_df.empty:
        return None

    lengths = sorted(group_df["length"].unique())
    densities = sorted(group_df["target_conflict_density"].unique())

    bars_per_length = len(densities) * len(ALGORITHM_ORDER)
    bar_width = 0.34
    length_gap = 0.9
    subgroup_gap = 0.12

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    density_xticks = []
    density_xticklabels = []
    group_annotations = []

    for length_idx, length in enumerate(lengths):
        length_start = length_idx * (bars_per_length * bar_width + len(densities) * subgroup_gap + length_gap)
        length_center = length_start + 0.5 * ((bars_per_length - 1) * bar_width + (len(densities) - 1) * subgroup_gap)
        length_group_max = 0.0

        for density_idx, density in enumerate(densities):
            subgroup_start = length_start + density_idx * (len(ALGORITHM_ORDER) * bar_width + subgroup_gap)
            for algorithm_idx, algorithm in enumerate(ALGORITHM_ORDER):
                x = subgroup_start + algorithm_idx * bar_width
                values = group_df.loc[
                    (group_df["length"] == length)
                    & (group_df["target_conflict_density"] == density)
                    & (group_df["algorithm"] == algorithm),
                    "found_pair_count",
                ].to_numpy(dtype=float)
                if len(values) == 0:
                    continue

                mean_value = float(np.mean(values))
                std_value = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
                sem_value = std_value / np.sqrt(len(values)) if len(values) > 1 else 0.0
                length_group_max = max(length_group_max, mean_value + sem_value)

                ax.bar(
                    x,
                    mean_value,
                    width=bar_width,
                    yerr=sem_value,
                    capsize=1,
                    color=ALGORITHM_COLORS[algorithm],
                    edgecolor="black",
                    linewidth=BAR_EDGE_LINEWIDTH,
                    error_kw={"elinewidth": ERRORBAR_LINEWIDTH, "capthick": ERRORBAR_LINEWIDTH},
                    alpha=1.0,
                    label=algorithm if (length_idx == 0 and density_idx == 0) else None,
                )

            subgroup_center = subgroup_start + bar_width
            density_xticks.append(subgroup_center)
            density_xticklabels.append(f"{density:.1f}")

        group_annotations.append((length_center, length, length_group_max))

    title_suffix = GROUP_TITLES[has_tttt5p]
    ax.set_title(title_suffix, fontsize=TITLE_FONT_SIZE, pad=6)
    ax.set_xlabel("Conflict probability", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Number of pairs found", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(density_xticks)
    ax.set_xticklabels(density_xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_ylim(0, shared_y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=0)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=2)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    ax.grid(axis="y", color="#B5B5B5", linewidth=GRID_LINEWIDTH, alpha=0.8)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        [ALGORITHM_LABELS.get(label, label) for label in labels],
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        handlelength=1.0,
        borderaxespad=0.2,
    )

    for x_pos, length, group_max in group_annotations:
        label_y = min(shared_y_max * 0.97, group_max + shared_y_max * 0.08)
        ax.text(
            x_pos,
            label_y,
            f"Length = {length}",
            ha="center",
            va="top",
            fontsize=TICK_LABEL_FONT_SIZE,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.20, top=0.88)
    return fig, title_suffix


def save_plot(fig: plt.Figure, output_dir: Path, title_suffix: str) -> Path:
    """Write one benchmark plot SVG and return its output path."""
    benchmark_slug = slugify_title_suffix(BENCHMARK_NAME)
    output_path = output_dir / f"{OUTPUT_FILENAME_STEM}_{benchmark_slug}_{slugify_title_suffix(title_suffix)}.svg"
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    return output_path


if __name__ == "__main__":
    parent_dir = MODULE_DIR / "data" / DATASET_PARENT_NAME
    runs_df = collect_runs(parent_dir)
    shared_y_max = compute_shared_y_max(runs_df)

    print(f"dataset parent: {parent_dir}")
    print(f"loaded runs: {len(runs_df)}")
    print(f"shared y max: {shared_y_max:.2f}")

    for has_tttt5p in (False, True):
        plot_result = plot_group(
            runs_df[runs_df["has_tttt5p"] == has_tttt5p],
            has_tttt5p=has_tttt5p,
            shared_y_max=shared_y_max,
        )
        if plot_result is None:
            continue
        fig, title_suffix = plot_result
        output_path = save_plot(fig, parent_dir, title_suffix)
        print(f"wrote plot: {output_path}")
        plt.close(fig)
