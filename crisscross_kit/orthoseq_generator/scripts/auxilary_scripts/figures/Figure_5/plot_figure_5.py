#!/usr/bin/env python3

"""
Plot the Figure 5 energy distributions for the three comparison arms.

This script plots up to three independently generated/workbook-backed datasets:
- search only / no SeqWalk prior (hardcoded benchmark workbook)
- SeqWalk max orthogonality
- SeqWalk + thermodynamic postfilter

For each available dataset it writes two publication-style SVG plots:
- on-target vs. off-target association energies
- secondary-structure energies

The visual style is intentionally matched to the Figure 1 plotting script.
"""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import (
    load_found_pairs,
    load_metadata,
    load_offtarget_matrices,
    parse_pair_label,
)


def load_energy_distributions(data_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    found_pairs = load_found_pairs(data_path)
    off_target_matrices = load_offtarget_matrices(data_path, family="selected")

    on_target = found_pairs["on_target_energy_verified"].to_numpy(dtype=float)
    self_seq = found_pairs["self_energy_seq_verified"].to_numpy(dtype=float)
    self_rc = found_pairs["self_energy_rc_seq_verified"].to_numpy(dtype=float)
    self_all = np.concatenate([self_seq, self_rc])

    off_target = np.concatenate(
        [
            off_target_matrices["handle_handle_energies"].to_numpy(dtype=float).ravel(),
            off_target_matrices["antihandle_handle_energies"].to_numpy(dtype=float).ravel(),
            off_target_matrices["antihandle_antihandle_energies"].to_numpy(dtype=float).ravel(),
        ]
    )
    off_target = off_target[off_target != 0.0]
    return on_target, off_target, self_all


def load_reference_thresholds(report_path: Path) -> dict[str, float]:
    metadata = load_metadata(report_path)
    return {
        "min_ontarget": float(metadata["search.min_ontarget"]),
        "max_ontarget": float(metadata["search.max_ontarget"]),
        "offtarget_limit": float(metadata["search.offtarget_limit"]),
        "self_energy_limit": float(metadata["search.self_energy_limit"]),
    }


def find_worst_offtarget_interaction(report_path: Path) -> dict[str, object] | None:
    found_pairs = load_found_pairs(report_path)
    pair_lookup = {}
    for _, row in found_pairs.iterrows():
        pair_lookup[int(row["global_pair_id"])] = {
            "handle": str(row["seq"]),
            "antihandle": str(row["rc_seq"]),
            "origin_seq_with_flank": str(row.get("origin_seq_with_flank"))
            if row.get("origin_seq_with_flank") is not None
            else None,
        }

    off_target_matrices = load_offtarget_matrices(report_path, family="selected")
    matrix_aliases = {
        "handle_handle_energies": "hh",
        "antihandle_handle_energies": "hah",
        "antihandle_antihandle_energies": "ahah",
    }

    worst = None
    for matrix_name, matrix_df in off_target_matrices.items():
        values = matrix_df.to_numpy(dtype=float)
        nonzero_positions = np.argwhere(values != 0.0)
        for row_idx, col_idx in nonzero_positions:
            energy = float(values[row_idx, col_idx])
            if worst is None or energy < worst["energy"]:
                row_label = str(matrix_df.index[row_idx])
                col_label = str(matrix_df.columns[col_idx])
                row_pair_id, row_strand, row_sequence = parse_pair_label(row_label)
                col_pair_id, col_strand, col_sequence = parse_pair_label(col_label)
                row_pair = pair_lookup.get(row_pair_id, {})
                col_pair = pair_lookup.get(col_pair_id, {})
                row_origin = row_pair.get("origin_seq_with_flank")
                col_origin = col_pair.get("origin_seq_with_flank")
                row_identity = "n.a."
                if row_origin is not None:
                    row_identity = "barcode" if row_sequence == row_origin else "revcombarcode"
                col_identity = "n.a."
                if col_origin is not None:
                    col_identity = "barcode" if col_sequence == col_origin else "revcombarcode"
                worst = {
                    "matrix": matrix_aliases[matrix_name],
                    "energy": energy,
                    "row_label": row_label,
                    "col_label": col_label,
                    "row_pair_id": row_pair_id,
                    "col_pair_id": col_pair_id,
                    "row_strand": row_strand,
                    "col_strand": col_strand,
                    "row_sequence": row_sequence,
                    "col_sequence": col_sequence,
                    "row_handle": row_pair.get("handle"),
                    "row_antihandle": row_pair.get("antihandle"),
                    "col_handle": col_pair.get("handle"),
                    "col_antihandle": col_pair.get("antihandle"),
                    "row_slot": "handle" if row_strand == "H" else "antihandle",
                    "col_slot": "handle" if col_strand == "H" else "antihandle",
                    "row_identity": row_identity,
                    "col_identity": col_identity,
                }
    return worst


def find_worst_secondary_structure(report_path: Path) -> dict[str, object] | None:
    found_pairs = load_found_pairs(report_path)
    worst = None

    for _, row in found_pairs.iterrows():
        pair_id = int(row["global_pair_id"])
        handle = str(row["seq"])
        antihandle = str(row["rc_seq"])
        origin = row.get("origin_seq_with_flank")
        origin = None if origin is None or str(origin) == "nan" else str(origin)

        candidates = [
            {
                "pair_id": pair_id,
                "slot": "handle",
                "sequence": handle,
                "energy": float(row["self_energy_seq_verified"]),
                "handle": handle,
                "antihandle": antihandle,
                "identity": "n.a." if origin is None else ("barcode" if handle == origin else "revcombarcode"),
            },
            {
                "pair_id": pair_id,
                "slot": "antihandle",
                "sequence": antihandle,
                "energy": float(row["self_energy_rc_seq_verified"]),
                "handle": handle,
                "antihandle": antihandle,
                "identity": "n.a." if origin is None else ("barcode" if antihandle == origin else "revcombarcode"),
            },
        ]

        for candidate in candidates:
            if worst is None or candidate["energy"] < worst["energy"]:
                worst = candidate

    return worst


def style_axes(ax: plt.Axes, *, tick_label_font_size, axis_linewidth, legend_font_size) -> None:
    ax.tick_params(axis="both", labelsize=tick_label_font_size, width=axis_linewidth, length=2)
    for spine in ax.spines.values():
        spine.set_linewidth(axis_linewidth)
    ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=legend_font_size,
        loc="upper left",
        handlelength=1.4,
    )


def plot_energy_distributions(
    data_path: Path,
    reference_thresholds: dict[str, float],
    out_dir: Path,
    output_prefix: str,
    figure_size_inches,
    onoff_x_min,
    onoff_x_max,
    secondary_x_min,
    secondary_x_max,
    bins_onoff,
    bins_self,
    title_font_size,
    axis_label_font_size,
    tick_label_font_size,
    legend_font_size,
    axis_linewidth,
    hist_edge_linewidth,
    reference_linewidth,
    reference_zorder,
    on_color,
    off_color,
    self_color,
    range_color,
    limit_color,
    onoff_title: str = "On and off-target energies",
    self_title: str = "Secondary structure energies",
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    on_target, off_target, self_all = load_energy_distributions(data_path)
    max_on_target = float(np.max(on_target)) if on_target.size else float("nan")
    min_off_target = float(np.min(off_target)) if off_target.size else float("nan")
    print(f"{output_prefix}: max on-target = {max_on_target:.3f} kcal/mol")
    print(f"{output_prefix}: min off-target = {min_off_target:.3f} kcal/mol")
    worst_offtarget = find_worst_offtarget_interaction(data_path)
    if worst_offtarget is not None:
        print(
            f"{output_prefix}: worst off-target pair = "
            f"{worst_offtarget['row_pair_id']}:{worst_offtarget['row_strand']} "
            f"vs {worst_offtarget['col_pair_id']}:{worst_offtarget['col_strand']} "
            f"({worst_offtarget['matrix']}, {worst_offtarget['energy']:.3f} kcal/mol)"
        )
        print(
            f"{output_prefix}: pair A = "
            f"({worst_offtarget['row_handle']}, {worst_offtarget['row_antihandle']})"
        )
        print(
            f"{output_prefix}: pair B = "
            f"({worst_offtarget['col_handle']}, {worst_offtarget['col_antihandle']})"
        )
        print(
            f"{output_prefix}: participant A: "
            f"sequence = {worst_offtarget['row_sequence']}, "
            f"identity = {worst_offtarget['row_identity']}, "
            f"slot = {worst_offtarget['row_slot']}"
        )
        print(
            f"{output_prefix}: participant B: "
            f"sequence = {worst_offtarget['col_sequence']}, "
            f"identity = {worst_offtarget['col_identity']}, "
            f"slot = {worst_offtarget['col_slot']}"
        )

    worst_secondary = find_worst_secondary_structure(data_path)
    if worst_secondary is not None:
        print(
            f"{output_prefix}: worst secondary-structure former = "
            f"pair {worst_secondary['pair_id']} "
            f"({worst_secondary['energy']:.3f} kcal/mol)"
        )
        print(
            f"{output_prefix}: pair = "
            f"({worst_secondary['handle']}, {worst_secondary['antihandle']})"
        )
        print(
            f"{output_prefix}: participant: "
            f"sequence = {worst_secondary['sequence']}, "
            f"identity = {worst_secondary['identity']}, "
            f"slot = {worst_secondary['slot']}"
        )

    bin_width_onoff = (onoff_x_max - onoff_x_min) / bins_onoff
    bin_edges_onoff = np.linspace(
        onoff_x_min - 0.5 * bin_width_onoff,
        onoff_x_max - 0.5 * bin_width_onoff,
        bins_onoff + 1,
    )

    fig, ax = plt.subplots(figsize=figure_size_inches)
    ax.hist(
        off_target,
        bins=bin_edges_onoff,
        density=True,
        color=off_color,
        edgecolor="black",
        linewidth=hist_edge_linewidth,
        label="Off-target",
        zorder=3,
    )
    ax.hist(
        on_target,
        bins=bin_edges_onoff,
        density=True,
        color=on_color,
        edgecolor="black",
        linewidth=hist_edge_linewidth,
        label="On-target",
        zorder=2,
    )

    ax.axvline(
        reference_thresholds["min_ontarget"],
        color=range_color,
        linestyle="--",
        linewidth=reference_linewidth,
        label="On-target range",
        zorder=reference_zorder,
    )
    ax.axvline(
        reference_thresholds["max_ontarget"],
        color=range_color,
        linestyle="--",
        linewidth=reference_linewidth,
        label="_nolegend_",
        zorder=reference_zorder,
    )
    ax.axvline(
        reference_thresholds["offtarget_limit"],
        color=limit_color,
        linestyle="--",
        linewidth=reference_linewidth,
        label="Off-target limit",
        zorder=reference_zorder,
    )

    ax.set_xlabel(r"Gibbs free energy, $\Delta G_{\mathrm{assoc}}$ (kcal/mol)", fontsize=axis_label_font_size)
    ax.set_ylabel("Density", fontsize=axis_label_font_size)
    ax.set_title(onoff_title, fontsize=title_font_size, pad=4)
    ax.set_xlim(onoff_x_min, onoff_x_max)
    style_axes(
        ax,
        tick_label_font_size=tick_label_font_size,
        axis_linewidth=axis_linewidth,
        legend_font_size=legend_font_size,
    )
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.22, top=0.90)
    onoff_path = out_dir / f"{output_prefix}_on_vs_off.svg"
    fig.savefig(onoff_path, format="svg", bbox_inches="tight")
    plt.close(fig)

    bin_edges_self = np.linspace(secondary_x_min, secondary_x_max, bins_self + 1)

    fig, ax = plt.subplots(figsize=figure_size_inches)
    ax.hist(
        self_all,
        bins=bin_edges_self,
        density=True,
        color=self_color,
        edgecolor="black",
        linewidth=hist_edge_linewidth,
        label="Secondary structure",
        zorder=2,
    )
    ax.axvline(
        reference_thresholds["self_energy_limit"],
        color=limit_color,
        linestyle="--",
        linewidth=reference_linewidth,
        label="Secondary structure limit",
        zorder=reference_zorder,
    )

    ax.set_xlabel(r"Gibbs free energy, $\Delta G_{\mathrm{sec}}$ (kcal/mol)", fontsize=axis_label_font_size)
    ax.set_ylabel("Density", fontsize=axis_label_font_size)
    ax.set_title(self_title, fontsize=title_font_size, pad=4)
    ax.set_xlim(secondary_x_min, secondary_x_max)
    style_axes(
        ax,
        tick_label_font_size=tick_label_font_size,
        axis_linewidth=axis_linewidth,
        legend_font_size=legend_font_size,
    )
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.22, top=0.90)
    self_path = out_dir / f"{output_prefix}_self_energies.svg"
    fig.savefig(self_path, format="svg", bbox_inches="tight")
    plt.close(fig)

    return onoff_path, self_path


def plot_if_present(*, data_path: Path | None, label: str, **plot_kwargs) -> None:
    if data_path is None or not data_path.exists():
        print(f"Skipping {label}: workbook not found.")
        return

    reference_thresholds = load_reference_thresholds(data_path)
    onoff_path, self_path = plot_energy_distributions(
        data_path=data_path,
        reference_thresholds=reference_thresholds,
        **plot_kwargs,
    )
    print(f"Wrote {onoff_path}")
    print(f"Wrote {self_path}")


if __name__ == "__main__":
    matplotlib.rcParams["font.family"] = "Arial"
    matplotlib.rcParams["svg.fonttype"] = "none"

    mm_per_inch = 25.4
    figure_width_mm = 177.8 * 0.5 * 1.05
    figure_height_mm = 58.0 * 1.05
    figure_size_inches = (figure_width_mm / mm_per_inch, figure_height_mm / mm_per_inch)

    title_font_size = 8
    axis_label_font_size = 8
    tick_label_font_size = 6
    legend_font_size = 6

    axis_linewidth = 0.5
    hist_edge_linewidth = 0.35
    reference_linewidth = 1.1
    reference_zorder = 4

    on_color = "#3B6FB6"
    off_color = "#B55A5A"
    self_color = "#8C6BB1"
    range_color = "#2A9D8F"
    limit_color = "#4F4F4F"

    onoff_x_min = -30.0
    onoff_x_max = 0.0
    secondary_x_min = -3.85
    secondary_x_max = 0.0
    bins_onoff = 80
    bins_self = 60

    figure_dir = Path(__file__).resolve().parent
    benchmark_search_only_path = (
        PACKAGE_DIR
        / "orthoseq_generator/scripts/benchmarking/long_seq/data/"
        / "batch_x______sigma1p0_seed41/len16/5p_none/"
        / "hybrid_len16_5p_none_limitm8p16_budget10000000_init450_seed41.xlsx"
    )
    seqwalk_postfilter_matches = sorted(
        (figure_dir / "data").glob("figure5_hybrid_len16_noflank_seqwalk_k*_seed42.xlsx")
    )
    seqwalk_postfilter_data_path = (
        seqwalk_postfilter_matches[-1] if seqwalk_postfilter_matches else None
    )
    seqwalk_max_orthogonality_matches = sorted(
        (figure_dir / "data").glob("figure5_seqwalk_max_orthogonality_len16_n*_seed42.xlsx")
    )
    seqwalk_max_orthogonality_data_path = (
        seqwalk_max_orthogonality_matches[-1] if seqwalk_max_orthogonality_matches else None
    )
    out_dir = figure_dir / "data" / "plots"

    plot_if_present(
        data_path=benchmark_search_only_path,
        label="search only benchmark",
        out_dir=out_dir,
        output_prefix="search_only_len16",
        figure_size_inches=figure_size_inches,
        onoff_x_min=onoff_x_min,
        onoff_x_max=onoff_x_max,
        secondary_x_min=secondary_x_min,
        secondary_x_max=secondary_x_max,
        bins_onoff=bins_onoff,
        bins_self=bins_self,
        title_font_size=title_font_size,
        axis_label_font_size=axis_label_font_size,
        tick_label_font_size=tick_label_font_size,
        legend_font_size=legend_font_size,
        axis_linewidth=axis_linewidth,
        hist_edge_linewidth=hist_edge_linewidth,
        reference_linewidth=reference_linewidth,
        reference_zorder=reference_zorder,
        on_color=on_color,
        off_color=off_color,
        self_color=self_color,
        range_color=range_color,
        limit_color=limit_color,
    )

    plot_if_present(
        data_path=seqwalk_max_orthogonality_data_path,
        label="SeqWalk max orthogonality",
        out_dir=out_dir,
        output_prefix="seqwalk_max_orthogonality_len16",
        figure_size_inches=figure_size_inches,
        onoff_x_min=onoff_x_min,
        onoff_x_max=onoff_x_max,
        secondary_x_min=secondary_x_min,
        secondary_x_max=secondary_x_max,
        bins_onoff=bins_onoff,
        bins_self=bins_self,
        title_font_size=title_font_size,
        axis_label_font_size=axis_label_font_size,
        tick_label_font_size=tick_label_font_size,
        legend_font_size=legend_font_size,
        axis_linewidth=axis_linewidth,
        hist_edge_linewidth=hist_edge_linewidth,
        reference_linewidth=reference_linewidth,
        reference_zorder=reference_zorder,
        on_color=on_color,
        off_color=off_color,
        self_color=self_color,
        range_color=range_color,
        limit_color=limit_color,
    )

    plot_if_present(
        data_path=seqwalk_postfilter_data_path,
        label="SeqWalk + postfilter",
        out_dir=out_dir,
        output_prefix="seqwalk_postfilter_len16",
        figure_size_inches=figure_size_inches,
        onoff_x_min=onoff_x_min,
        onoff_x_max=onoff_x_max,
        secondary_x_min=secondary_x_min,
        secondary_x_max=secondary_x_max,
        bins_onoff=bins_onoff,
        bins_self=bins_self,
        title_font_size=title_font_size,
        axis_label_font_size=axis_label_font_size,
        tick_label_font_size=tick_label_font_size,
        legend_font_size=legend_font_size,
        axis_linewidth=axis_linewidth,
        hist_edge_linewidth=hist_edge_linewidth,
        reference_linewidth=reference_linewidth,
        reference_zorder=reference_zorder,
        on_color=on_color,
        off_color=off_color,
        self_color=self_color,
        range_color=range_color,
        limit_color=limit_color,
    )
