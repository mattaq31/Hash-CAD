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

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import load_metadata, load_offtarget_matrices
from orthoseq_generator.vertex_cover_algorithms import compute_pair_conflict_probability


def format_limit_label(value: float) -> str:
    """Convert one off-target limit into the workbook filename token."""
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


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
    fivep_label = str(first.get("fivep_ext", "")) or "none"
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
                "fivep_label": str(metadata.get("input.fivep_ext", "")) or parsed["fivep_label"],
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


def plot_batch(
    lengths: list[int],
    limit_label: str,
    runs: list[dict],
    conflict_probability_by_length: dict[int, float],
    fivep_label: str,
    output_dir: Path,
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
        ("hybrid", 900): "H900",
        ("hybrid", 450): "H450",
        ("hybrid", 250): "H250",
    }

    figure_width_mm = 177.8 * 0.48
    figure_height_mm = 58.0
    figure_size_inches = (figure_width_mm / 25.4, figure_height_mm / 25.4)

    run_lookup = {
        (run["length"], run["algorithm"], run["limit_label"], run["init_count"]): run
        for run in runs
    }

    values = [run["found_pair_count"] for run in runs]
    y_max = max(1.0, max(values) * 1.08 + 2.0) if values else 1.0

    fig, ax = plt.subplots(figsize=figure_size_inches)

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
                linewidth=0.5,
                zorder=3,
            )

        cluster_center = cluster_start + 0.5 * (len(series_order) - 1) * bar_width
        xticks.append(cluster_center)
        xticklabels.append(str(length))
        probability = conflict_probability_by_length.get(length)
        group_annotations.append((cluster_center, probability, group_max))
        current_x += len(series_order) * bar_width + cluster_gap

    ax.set_title("5' TTTT extension" if fivep_label != "none" else "No extension", fontsize=6, pad=6)
    ax.set_xlabel("Sequence length", fontsize=6)
    ax.set_ylabel("Number of pairs found", fontsize=6)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=6)
    ax.set_ylim(0, y_max)
    ax.tick_params(axis="y", labelsize=6, width=0.5, length=2)
    ax.tick_params(axis="x", width=0.5, length=0, pad=2)

    for spine in ax.spines.values():
        spine.set_linewidth(0.5)

    handles = [
        Patch(facecolor=series_colors[key], edgecolor="black", linewidth=0.5, label=series_labels[key])
        for key in series_order
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=6,
        handlelength=1.0,
        borderaxespad=0.2,
    )

    for x_pos, probability, group_max in group_annotations:
        label_y = min(y_max * 0.98, group_max + y_max * 0.10 if group_max > 0 else y_max * 0.94)
        ax.text(
            x_pos,
            label_y,
            "N.A." if probability is None else f"{probability:.2f}",
            ha="center",
            va="top",
            fontsize=6,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.20, top=0.88)
    output_path = output_dir / f"long_seq_single_limit_batch_5p_{fivep_label}.svg"
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    return output_path


def infer_summary_path(data_root: Path, module_dir: Path) -> Path:
    """Infer the generated batch summary path from one batch data directory."""
    return module_dir / "configs" / "generated" / data_root.name / "batch_summary.toml"


def plot_single_batch(data_root: Path, summary_path: Path, output_dir: Path | None) -> Path:
    """
    Load one batch, render its plot, and print a short run summary.

    The default output location is `long_seq/plots/`, not the batch data
    directory itself.
    """
    resolved_data_root = data_root.resolve()
    resolved_summary_path = summary_path.resolve()
    resolved_output_dir = (
        Path(__file__).resolve().parents[1] / "plots"
        if output_dir is None else output_dir.resolve()
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    lengths, fivep_label, limit_label, _, _ = load_summary(resolved_summary_path)
    runs = collect_runs(resolved_data_root)
    conflict_probability_by_length = compute_conflict_probability_by_length(runs)

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
    print(f"batch summary: {resolved_summary_path}")
    print(f"loaded workbooks: {len(runs)}")
    print(f"expected runs: {len(expected_keys)}")
    print(f"missing runs: {len(missing_keys)}")
    print(f"computed conflict probabilities: {conflict_probability_by_length}")

    if missing_keys:
        print("missing:")
        for length, algorithm, _, init_count in missing_keys:
            label = "naive" if algorithm == "naive" else f"init{init_count}"
            print(f"  len{length} 5p_{fivep_label} {algorithm} {label}")

    output_path = plot_batch(
        lengths=lengths,
        limit_label=limit_label,
        runs=runs,
        conflict_probability_by_length=conflict_probability_by_length,
        fivep_label=fivep_label,
        output_dir=resolved_output_dir,
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
        summary_paths = [infer_summary_path(data_root, module_dir) for data_root in data_roots]
    else:
        summary_paths = args.summary

    if len(summary_paths) != len(data_roots):
        raise SystemExit("Expected the same number of --summary and --data-root arguments.")

    for index, (data_root, summary_path) in enumerate(zip(data_roots, summary_paths, strict=True)):
        if index:
            print()
        plot_single_batch(data_root, summary_path, args.output_dir)
