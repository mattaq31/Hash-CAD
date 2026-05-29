#!/usr/bin/env python3
"""
Plot the canonical long-seq single-limit benchmark batches.

Each plotted batch corresponds to one 5' extension condition and one derived
off-target limit. The script reads the matching `batch_summary.toml`, loads the
saved workbook metadata, and writes one SVG per batch into `long_seq/plots/` by
default.

Within each sequence-length cluster the bar order is:

- naive
- hybrid init=900
- hybrid init=450
- hybrid init=250

The label above each cluster is the seed conflict probability reconstructed
from the `init=900` hybrid seed matrix for that length.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import tomllib

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import load_metadata, load_offtarget_matrices
from orthoseq_generator.vertex_cover_algorithms import compute_pair_conflict_probability

MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.48 * 1.10
FIGURE_HEIGHT_MM = 58.0
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 8
AXIS_LABEL_FONT_SIZE = 8
TICK_LABEL_FONT_SIZE = 6
LEGEND_FONT_SIZE = 6
ANNOTATION_FONT_SIZE = 6

AXIS_LINEWIDTH = 0.5
BAR_EDGE_LINEWIDTH = 0.5

SUMMARY_FILENAME_STEM = "long_seq_single_limit_batch_summary"


def format_limit_label(value: float) -> str:
    """Convert one off-target limit into the workbook filename token."""
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


def normalize_fivep_label(value) -> str:
    """Normalize empty or missing 5' extension metadata to the plot label `none`."""
    if value is None:
        return "none"
    text = str(value).strip()
    if not text or text.lower() in {"none", "n.a.", "na", "nan"}:
        return "none"
    return text


def parse_workbook_filename(report_path: Path) -> dict | None:
    """Parse one long-seq workbook filename into plot-relevant fields."""
    match = re.match(
        (
            r"(?P<algorithm>naive|hybrid)_len(?P<length>\d+)"
            r"_5p_(?P<fivep_label>[^_]+)"
            r"_limit(?P<limit_label>[a-z0-9]+)"
            r"(?:_budget(?P<budget>\d+))?"
            r"(?:_init(?P<init_count>\d+))?"
            r"_seed(?P<seed>\d+)\.xlsx$"
        ),
        report_path.name,
    )
    if match is None:
        return None
    init_count = match.group("init_count")
    return {
        "algorithm": match.group("algorithm"),
        "length": int(match.group("length")),
        "fivep_label": match.group("fivep_label"),
        "limit_label": match.group("limit_label"),
        "init_count": None if init_count is None else int(init_count),
    }


def load_summary(summary_path: Path) -> tuple[list[int], str, str, float, float]:
    """Load the one-limit batch layout from `batch_summary.toml`."""
    with summary_path.open("rb") as fh:
        summary = tomllib.load(fh)

    conditions = summary["conditions"]
    first = conditions[0]
    limit_value = float(first["derived_offtarget_limit"])
    lengths = sorted({int(condition["length"]) for condition in conditions})
    fivep_label = normalize_fivep_label(first.get("fivep_ext", ""))
    limit_label = format_limit_label(limit_value)
    target_fraction_bound = float(first["target_fraction_bound"])
    return lengths, fivep_label, limit_label, limit_value, target_fraction_bound


def collect_runs(data_root: Path) -> list[dict]:
    """Collect the currently available run summaries from one batch directory."""
    runs = []
    for report_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_workbook_filename(report_path)
        if parsed is None:
            continue

        metadata = load_metadata(report_path)
        algorithm_name = str(metadata.get("algorithm_name", "") or "").strip()
        algorithm = "naive" if algorithm_name == "naive_search" else "hybrid"
        init_count = None if algorithm == "naive" else int(metadata["search.initial_fresh_pair_count"])

        runs.append(
            {
                "report_path": report_path,
                "length": int(metadata["input.length"]),
                "fivep_label": normalize_fivep_label(metadata.get("input.fivep_ext", parsed["fivep_label"])),
                "limit_label": parsed["limit_label"],
                "algorithm": algorithm,
                "init_count": init_count,
                "found_pair_count": int(metadata["found_pair_count"]),
            }
        )
    return runs


def compute_conflict_probability_by_length(runs: list[dict]) -> dict[int, float]:
    """Compute one seed conflict probability per length from the `init=900` hybrid run."""
    probabilities = {}
    for run in runs:
        if run["algorithm"] != "hybrid" or run["init_count"] != 900:
            continue

        metadata = load_metadata(run["report_path"])
        seed_offtarget = load_offtarget_matrices(run["report_path"], family="seed")
        probabilities[run["length"]] = compute_pair_conflict_probability(
            seed_offtarget,
            float(metadata["search.offtarget_limit"]),
        )
    return probabilities


def compute_shared_y_max(runs: list[dict]) -> float:
    """Compute one shared y-axis maximum across the plotted long-seq batches."""
    values = [int(run["found_pair_count"]) for run in runs]
    return max(1.0, max(values) * 1.08 + 2.0) if values else 1.0


def build_summary_table(
    runs: list[dict],
    conflict_probability_by_length: dict[int, float],
    *,
    fivep_label: str,
    limit_label: str,
) -> pd.DataFrame:
    """Build the exact plotted values plus naive-relative improvements."""
    if not runs:
        return pd.DataFrame(
            columns=[
                "length",
                "fivep_label",
                "limit_label",
                "series_label",
                "algorithm",
                "init_count",
                "found_pair_count",
                "naive_found_pair_count",
                "absolute_improvement_vs_naive",
                "percent_improvement_vs_naive",
                "seed_conflict_probability",
                "report_path",
            ]
        )

    series_order = {
        ("naive", None): 0,
        ("hybrid", 900): 1,
        ("hybrid", 450): 2,
        ("hybrid", 250): 3,
    }
    series_labels = {
        ("naive", None): "Naive",
        ("hybrid", 900): "Hybrid 900",
        ("hybrid", 450): "Hybrid 450",
        ("hybrid", 250): "Hybrid 250",
    }

    summary_df = pd.DataFrame(runs).copy()
    summary_df = summary_df.loc[
        (summary_df["fivep_label"] == fivep_label) & (summary_df["limit_label"] == limit_label)
    ].copy()
    if summary_df.empty:
        return summary_df

    naive_df = summary_df.loc[
        summary_df["algorithm"] == "naive",
        ["length", "found_pair_count"],
    ].rename(columns={"found_pair_count": "naive_found_pair_count"})
    summary_df = summary_df.merge(naive_df, on="length", how="left")
    summary_df["absolute_improvement_vs_naive"] = (
        summary_df["found_pair_count"] - summary_df["naive_found_pair_count"]
    )
    summary_df["percent_improvement_vs_naive"] = summary_df["absolute_improvement_vs_naive"] * 100.0 / summary_df[
        "naive_found_pair_count"
    ]
    summary_df.loc[summary_df["algorithm"] == "naive", "absolute_improvement_vs_naive"] = 0
    summary_df.loc[summary_df["algorithm"] == "naive", "percent_improvement_vs_naive"] = 0.0
    summary_df["series_label"] = [
        series_labels.get((algorithm, init_count), str(algorithm))
        for algorithm, init_count in zip(summary_df["algorithm"], summary_df["init_count"], strict=True)
    ]
    summary_df["series_order"] = [
        series_order.get((algorithm, init_count), 999)
        for algorithm, init_count in zip(summary_df["algorithm"], summary_df["init_count"], strict=True)
    ]
    summary_df["seed_conflict_probability"] = summary_df["length"].map(conflict_probability_by_length)
    summary_df = summary_df.sort_values(["length", "series_order"], ignore_index=True)
    return summary_df[
        [
            "length",
            "fivep_label",
            "limit_label",
            "series_label",
            "algorithm",
            "init_count",
            "found_pair_count",
            "naive_found_pair_count",
            "absolute_improvement_vs_naive",
            "percent_improvement_vs_naive",
            "seed_conflict_probability",
            "report_path",
        ]
    ]


def save_summary_workbook(summary_df: pd.DataFrame, output_dir: Path, fivep_label: str) -> Path:
    """Write the exact plotted values and naive-relative improvements as XLSX."""
    output_path = output_dir / f"{SUMMARY_FILENAME_STEM}_5p_{fivep_label}.xlsx"
    summary_df.to_excel(output_path, index=False, sheet_name="summary")
    return output_path


def plot_batch(
    lengths: list[int],
    limit_label: str,
    runs: list[dict],
    conflict_probability_by_length: dict[int, float],
    fivep_label: str,
    output_dir: Path,
    shared_y_max: float,
) -> Path:
    """Render the single-limit clustered bar plot and return the output path."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    matplotlib.rcParams["font.family"] = "Arial"
    matplotlib.rcParams["svg.fonttype"] = "none"

    series_order = [("naive", None), ("hybrid", 900), ("hybrid", 450), ("hybrid", 250)]
    series_colors = {
        ("naive", None): "#808080",
        ("hybrid", 900): "#2A9D8F",
        ("hybrid", 450): "#63B7AF",
        ("hybrid", 250): "#9FD4CF",
    }
    series_labels = {
        ("naive", None): "Naive",
        ("hybrid", 900): "Hybrid 900",
        ("hybrid", 450): "Hybrid 450",
        ("hybrid", 250): "Hybrid 250",
    }

    run_lookup = {
        (run["length"], run["algorithm"], run["limit_label"], run["init_count"]): run
        for run in runs
    }

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)

    bar_width = 0.28
    cluster_gap = 0.48
    xticks = []
    xticklabels = []
    group_annotations = []
    current_x = 0.0

    for length in lengths:
        cluster_start = current_x
        group_max = 0.0
        for series_index, series_key in enumerate(series_order):
            algorithm, init_count = series_key
            x = cluster_start + series_index * bar_width
            run = run_lookup.get((length, algorithm, limit_label, init_count))
            if run is None:
                continue
            group_max = max(group_max, float(run["found_pair_count"]))
            ax.bar(
                x,
                run["found_pair_count"],
                width=bar_width,
                facecolor=series_colors[series_key],
                edgecolor="black",
                linewidth=BAR_EDGE_LINEWIDTH,
                zorder=3,
            )

        cluster_center = cluster_start + 0.5 * (len(series_order) - 1) * bar_width
        xticks.append(cluster_center)
        xticklabels.append(str(length))
        probability = conflict_probability_by_length.get(length)
        group_annotations.append((cluster_center, probability, group_max))
        current_x += len(series_order) * bar_width + cluster_gap

    ax.set_title("5' TTTT extension" if fivep_label != "none" else "No extension", fontsize=TITLE_FONT_SIZE, pad=6)
    ax.set_xlabel("Sequence length", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Number of pairs found", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_ylim(0, shared_y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=2)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=2)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    handles = [
        Patch(facecolor=series_colors[key], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label=series_labels[key])
        for key in series_order
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        handlelength=1.0,
        borderaxespad=0.2,
    )

    for x_pos, probability, group_max in group_annotations:
        label_y = min(shared_y_max * 0.98, group_max + shared_y_max * 0.10 if group_max > 0 else shared_y_max * 0.94)
        ax.text(
            x_pos,
            label_y,
            "N.A." if probability is None else f"{probability:.2f}",
            ha="center",
            va="top",
            fontsize=ANNOTATION_FONT_SIZE,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.20, top=0.88)
    output_path = output_dir / f"long_seq_single_limit_batch_5p_{fivep_label}.svg"
    fig.savefig(output_path, format="svg")
    plt.close(fig)
    return output_path


def infer_batch_layout_from_runs(runs: list[dict]) -> tuple[list[int], str, str]:
    """Infer lengths, 5' extension label, and limit label from the saved workbooks."""
    if not runs:
        raise ValueError("No workbooks found under the batch data directory.")

    lengths = sorted({int(run["length"]) for run in runs})
    fivep_labels = sorted({str(run["fivep_label"]) for run in runs})
    limit_labels = sorted({str(run["limit_label"]) for run in runs})

    if len(fivep_labels) != 1:
        raise ValueError(f"Expected exactly one 5' extension label, got {fivep_labels}.")
    if len(limit_labels) != 1:
        raise ValueError(f"Expected exactly one off-target limit label, got {limit_labels}.")

    return lengths, fivep_labels[0], limit_labels[0]


def plot_single_batch(data_root: Path, summary_path: Path | None, output_dir: Path | None, shared_y_max: float) -> Path:
    """
    Load one batch, render its plot, and print a short run summary.

    The default output location is `long_seq/plots/`, not the batch data
    directory itself.
    """
    resolved_data_root = data_root.resolve()
    resolved_summary_path = None if summary_path is None else summary_path.resolve()
    resolved_output_dir = (
        Path(__file__).resolve().parents[1] / "plots"
        if output_dir is None else output_dir.resolve()
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    runs = collect_runs(resolved_data_root)
    if resolved_summary_path is not None and resolved_summary_path.exists():
        lengths, fivep_label, limit_label, _, _ = load_summary(resolved_summary_path)
        summary_source = str(resolved_summary_path)
    else:
        lengths, fivep_label, limit_label = infer_batch_layout_from_runs(runs)
        summary_source = "inferred from workbooks"
    conflict_probability_by_length = compute_conflict_probability_by_length(runs)
    summary_df = build_summary_table(
        runs,
        conflict_probability_by_length,
        fivep_label=fivep_label,
        limit_label=limit_label,
    )

    expected_keys = {
        (length, "naive", limit_label, None) for length in lengths
    } | {
        (length, "hybrid", limit_label, init_count)
        for length in lengths
        for init_count in [900, 450, 250]
    }
    run_keys = {
        (run["length"], run["algorithm"], run["limit_label"], run["init_count"])
        for run in runs
    }
    missing_keys = sorted(expected_keys - run_keys)

    print(f"data root: {resolved_data_root}")
    print(f"batch summary: {summary_source}")
    print(f"loaded workbooks: {len(runs)}")
    print(f"expected runs: {len(expected_keys)}")
    print(f"missing runs: {len(missing_keys)}")
    print(f"computed conflict probabilities: {conflict_probability_by_length}")

    if missing_keys:
        print("missing:")
        for length, algorithm, _, init_count in missing_keys:
            label = "naive" if algorithm == "naive" else f"init{init_count}"
            print(f"  len{length} 5p_{fivep_label} {algorithm} {label}")

    summary_output_path = save_summary_workbook(summary_df, resolved_output_dir, fivep_label)
    print(f"wrote summary workbook: {summary_output_path}")

    output_path = plot_batch(
        lengths=lengths,
        limit_label=limit_label,
        runs=runs,
        conflict_probability_by_length=conflict_probability_by_length,
        fivep_label=fivep_label,
        output_dir=resolved_output_dir,
        shared_y_max=shared_y_max,
    )
    print(f"wrote plot: {output_path}")
    return output_path


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[1]
    default_data_roots = [
        module_dir / "data" / "batch_x_TTTT_sigma1p0_seed41",
        module_dir / "data" / "batch_x______sigma1p0_seed41",
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        action="append",
        default=None,
        help="Batch data folder to plot. Repeat to plot multiple batches.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        action="append",
        default=None,
        help="Matching batch_summary.toml path. Repeat to match each --data-root.",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    data_roots = default_data_roots if args.data_root is None else args.data_root
    if args.summary is None:
        summary_paths = [None] * len(data_roots)
    else:
        summary_paths = args.summary

    if len(summary_paths) != len(data_roots):
        raise SystemExit("Expected the same number of --summary and --data-root arguments.")

    all_runs = []
    for data_root in data_roots:
        all_runs.extend(collect_runs(data_root.resolve()))
    shared_y_max = compute_shared_y_max(all_runs)
    print(f"shared y max: {shared_y_max:.2f}")

    for index, (data_root, summary_path) in enumerate(zip(data_roots, summary_paths, strict=True)):
        if index:
            print()
        plot_single_batch(data_root, summary_path, args.output_dir, shared_y_max)
