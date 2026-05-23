#!/usr/bin/env python3
"""
Plot long-sequence live benchmark workbooks, including partial result sets.

This mirrors the batch-benchmark bar-plot structure, but the long-sequence
workflow has only two algorithms and only two fixed off-target settings. The
script reads the generated batch summaries to recover the expected plotting
layout, then fills in whichever XLSX reports are already present.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd

matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["svg.fonttype"] = "none"

MODULE_DIR = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parents[6]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from orthoseq_generator.search_report_reader import load_metadata

DATA_ROOT = MODULE_DIR / "data" / "non_canonical"
GENERATED_CONFIG_ROOT = MODULE_DIR / "configs" / "generated"
ALGORITHM_ORDER = ["naive", "hybrid"]
ALGORITHM_COLORS = {
    "naive": "#808080",
    "hybrid": "#2A9D8F",
}
ALGORITHM_LABELS = {
    "naive": "Naive",
    "hybrid": "Hybrid",
}
GROUP_TITLES = {
    False: "No extension",
    True: "5' TTTT extension",
}
OUTPUT_FILENAME_STEM = "long_seq_live_benchmark_found_pair_count"
MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.48
FIGURE_HEIGHT_MM = 58.0
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 5
AXIS_LABEL_FONT_SIZE = 5
TICK_LABEL_FONT_SIZE = 5
LEGEND_FONT_SIZE = 5

AXIS_LINEWIDTH = 0.5
GRID_LINEWIDTH = 0.5
BAR_EDGE_LINEWIDTH = 0.5


def format_limit_label(value: float) -> str:
    """Format one numeric off-target limit into the workbook filename token."""
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


def parse_limit_label(limit_label: str) -> float:
    """Decode a filename token such as `m8p16` back into a float."""
    return float(limit_label.replace("m", "-").replace("p", "."))


def slugify_title_suffix(title_suffix: str) -> str:
    """Convert a plot title suffix into a filesystem-safe filename suffix."""
    slug = title_suffix.lower()
    slug = slug.replace("5'", "5prime")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def parse_run_filename(report_path: Path) -> dict | None:
    """Parse one long-sequence workbook filename into plot-relevant fields."""
    match = re.match(
        r"(?P<algorithm>naive|hybrid)_len(?P<length>\d+)_5p_(?P<fivep_label>[^_]+)_limit(?P<cutoff>[a-z0-9]+)_seed(?P<seed>\d+)\.xlsx$",
        report_path.name,
    )
    if not match:
        return None
    return {
        "algorithm": match.group("algorithm"),
        "length": int(match.group("length")),
        "fivep_label": match.group("fivep_label"),
        "selected_offtarget_limit_label": match.group("cutoff"),
        "seed": int(match.group("seed")),
    }


def normalize_algorithm_name(value: str | None) -> str | None:
    """Map workbook metadata algorithm names onto the plotting labels."""
    if value == "naive_search":
        return "naive"
    if value == "hybrid_search":
        return "hybrid"
    return None if value is None else str(value)


def load_expected_conditions(config_root: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    """Load expected length/extension/fraction combinations from batch summaries."""
    rows = []
    limit_label_to_fraction = {}
    for summary_path in sorted(config_root.glob("*/batch_summary.toml")):
        data = tomllib.loads(summary_path.read_text(encoding="utf-8"))
        for condition in data.get("conditions", []):
            target_fraction = float(condition["target_fraction_bound"])
            derived_offtarget_limit = float(condition["derived_offtarget_limit"])
            limit_label = format_limit_label(derived_offtarget_limit)
            limit_label_to_fraction.setdefault(limit_label, target_fraction)
            rows.append(
                {
                    "length": int(condition["length"]),
                    "has_tttt5p": str(condition.get("fivep_ext", "")) == "TTTT",
                    "condition_label": f"{target_fraction:.2f}",
                    "condition_sort": target_fraction,
                }
            )
    if not rows:
        return pd.DataFrame(), limit_label_to_fraction
    expected_df = pd.DataFrame(rows).drop_duplicates().sort_values(
        ["has_tttt5p", "length", "condition_sort", "condition_label"]
    )
    return expected_df, limit_label_to_fraction


def collect_runs(data_root: Path, limit_label_to_fraction: dict[str, float]) -> pd.DataFrame:
    """Collect found-pair counts from all currently available long-seq workbooks."""
    rows = []
    for report_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_run_filename(report_path)
        if parsed is None:
            continue
        metadata = load_metadata(report_path)
        metadata_algorithm = normalize_algorithm_name(metadata.get("algorithm_name"))
        length = metadata.get("input.length")
        fivep_ext = metadata.get("input.fivep_ext")
        found_pair_count = metadata.get("found_pair_count")
        offtarget_limit = metadata.get("search.offtarget_limit")

        if metadata_algorithm is not None and metadata_algorithm != parsed["algorithm"]:
            raise ValueError(
                f"Algorithm mismatch in {report_path}: filename says {parsed['algorithm']}, "
                f"run_metadata says {metadata_algorithm}."
            )

        limit_label = parsed["selected_offtarget_limit_label"]
        limit_value = float(offtarget_limit) if offtarget_limit is not None else parse_limit_label(limit_label)
        target_fraction = limit_label_to_fraction.get(limit_label)
        condition_label = f"{target_fraction:.2f}" if target_fraction is not None else f"{limit_value:.2f}"
        condition_sort = target_fraction if target_fraction is not None else limit_value

        rows.append(
            {
                "report_path": str(report_path),
                "algorithm": metadata_algorithm or parsed["algorithm"],
                "length": int(length) if length is not None else parsed["length"],
                "fivep_ext": str(fivep_ext or ""),
                "has_tttt5p": str(fivep_ext or parsed["fivep_label"]).upper() == "TTTT",
                "seed": parsed["seed"],
                "selected_offtarget_limit_label": limit_label,
                "offtarget_limit": limit_value,
                "target_fraction_bound": target_fraction,
                "condition_label": condition_label,
                "condition_sort": condition_sort,
                "found_pair_count": int(found_pair_count),
            }
        )
    return pd.DataFrame(rows)


def build_expected_combinations(
    expected_df: pd.DataFrame,
    runs_df: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """Build the ordered set of x-axis conditions for both extension groups."""
    if not expected_df.empty:
        return expected_df.copy(), "Target off-target bound fraction"

    if runs_df.empty:
        return pd.DataFrame(), "Target off-target bound fraction"

    fallback_df = (
        runs_df[["length", "has_tttt5p", "condition_label", "condition_sort"]]
        .drop_duplicates()
        .sort_values(["has_tttt5p", "length", "condition_sort", "condition_label"])
        .reset_index(drop=True)
    )
    return fallback_df, "Off-target limit (kcal/mol)"


def compute_shared_y_max(runs_df: pd.DataFrame) -> float:
    """Compute a shared y-axis maximum across all plotted bars."""
    if runs_df.empty:
        return 1.0
    y_max = float(runs_df["found_pair_count"].max())
    return max(1.0, y_max * 1.08 + 2.0)


def summarize_missing_runs(expected_df: pd.DataFrame, runs_df: pd.DataFrame) -> pd.DataFrame:
    """Identify expected algorithm slots that do not yet have a workbook."""
    if expected_df.empty:
        return pd.DataFrame()

    expected_slots = expected_df.assign(_join_key=1).merge(
        pd.DataFrame({"algorithm": ALGORITHM_ORDER, "_join_key": 1}),
        on="_join_key",
    ).drop(columns="_join_key")
    observed_slots = runs_df[["length", "has_tttt5p", "condition_label", "algorithm"]].drop_duplicates()
    merged = expected_slots.merge(
        observed_slots,
        on=["length", "has_tttt5p", "condition_label", "algorithm"],
        how="left",
        indicator=True,
    )
    return merged.loc[merged["_merge"] == "left_only"].drop(columns="_merge")


def plot_group(
    group_df: pd.DataFrame,
    expected_group_df: pd.DataFrame,
    *,
    has_tttt5p: bool,
    shared_y_max: float,
    x_axis_label: str,
) -> tuple[plt.Figure, str] | None:
    """Plot one extension-condition subset of the live benchmark runs."""
    if group_df.empty and expected_group_df.empty:
        return None

    if expected_group_df.empty:
        lengths = sorted(group_df["length"].unique())
        condition_order = (
            group_df[["condition_label", "condition_sort"]]
            .drop_duplicates()
            .sort_values(["condition_sort", "condition_label"])
        )
    else:
        lengths = sorted(expected_group_df["length"].unique())
        condition_order = (
            expected_group_df[["condition_label", "condition_sort"]]
            .drop_duplicates()
            .sort_values(["condition_sort", "condition_label"])
        )
    condition_labels = condition_order["condition_label"].tolist()

    bars_per_length = len(condition_labels) * len(ALGORITHM_ORDER)
    bar_width = 0.38
    length_gap = 0.9
    subgroup_gap = 0.12

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    condition_xticks = []
    condition_xticklabels = []
    group_annotations = []

    for length_idx, length in enumerate(lengths):
        length_start = length_idx * (bars_per_length * bar_width + len(condition_labels) * subgroup_gap + length_gap)
        length_center = length_start + 0.5 * ((bars_per_length - 1) * bar_width + (len(condition_labels) - 1) * subgroup_gap)
        length_group_max = 0.0

        for condition_idx, condition_label in enumerate(condition_labels):
            subgroup_start = length_start + condition_idx * (len(ALGORITHM_ORDER) * bar_width + subgroup_gap)
            for algorithm_idx, algorithm in enumerate(ALGORITHM_ORDER):
                x = subgroup_start + algorithm_idx * bar_width
                values = group_df.loc[
                    (group_df["length"] == length)
                    & (group_df["condition_label"] == condition_label)
                    & (group_df["algorithm"] == algorithm),
                    "found_pair_count",
                ].to_numpy(dtype=float)
                if len(values) == 0:
                    continue

                value = float(values[-1])
                length_group_max = max(length_group_max, value)
                ax.bar(
                    x,
                    value,
                    width=bar_width,
                    color=ALGORITHM_COLORS[algorithm],
                    edgecolor="black",
                    linewidth=BAR_EDGE_LINEWIDTH,
                    alpha=1.0,
                )

            subgroup_center = subgroup_start + 0.5 * bar_width
            condition_xticks.append(subgroup_center)
            condition_xticklabels.append(condition_label)

        group_annotations.append((length_center, length, length_group_max))

    title_suffix = GROUP_TITLES[has_tttt5p]
    ax.set_title(title_suffix, fontsize=TITLE_FONT_SIZE, pad=6)
    ax.set_xlabel(x_axis_label, fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Number of pairs found", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(condition_xticks)
    ax.set_xticklabels(condition_xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_ylim(0, shared_y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=0)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=2)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    ax.grid(axis="y", color="#B5B5B5", linewidth=GRID_LINEWIDTH, alpha=0.8)
    ax.set_axisbelow(True)
    handles = [
        Patch(
            facecolor=ALGORITHM_COLORS[algorithm],
            edgecolor="black",
            linewidth=BAR_EDGE_LINEWIDTH,
            label=ALGORITHM_LABELS[algorithm],
        )
        for algorithm in ALGORITHM_ORDER
    ]
    ax.legend(
        handles,
        [handle.get_label() for handle in handles],
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
    output_path = output_dir / f"{OUTPUT_FILENAME_STEM}_{slugify_title_suffix(title_suffix)}.svg"
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    return output_path


if __name__ == "__main__":
    expected_df, limit_label_to_fraction = load_expected_conditions(GENERATED_CONFIG_ROOT)
    runs_df = collect_runs(DATA_ROOT, limit_label_to_fraction)
    plot_layout_df, x_axis_label = build_expected_combinations(expected_df, runs_df)
    missing_df = summarize_missing_runs(plot_layout_df, runs_df)
    shared_y_max = compute_shared_y_max(runs_df)

    print(f"data root: {DATA_ROOT}")
    print(f"loaded runs: {len(runs_df)}")
    if not expected_df.empty:
        print(f"expected algorithm slots: {len(plot_layout_df) * len(ALGORITHM_ORDER)}")
        print(f"missing algorithm slots: {len(missing_df)}")
    print(f"shared y max: {shared_y_max:.2f}")

    for has_tttt5p in (False, True):
        plot_result = plot_group(
            runs_df[runs_df["has_tttt5p"] == has_tttt5p],
            plot_layout_df[plot_layout_df["has_tttt5p"] == has_tttt5p],
            has_tttt5p=has_tttt5p,
            shared_y_max=shared_y_max,
            x_axis_label=x_axis_label,
        )
        if plot_result is None:
            continue
        fig, title_suffix = plot_result
        output_path = save_plot(fig, DATA_ROOT, title_suffix)
        print(f"wrote plot: {output_path}")
        plt.close(fig)
