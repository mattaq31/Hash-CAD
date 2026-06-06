#!/usr/bin/env python3

"""
Plot the Figure 1 energy distributions from the saved selection-free workbook.

This script reads the workbook produced by `prepare_data_f1.py` and writes two
publication-style SVG plots:
- on-target vs. off-target association energies
- secondary-structure energies

The vertical reference lines reuse the long-sequence benchmark thresholds so
the random sampled dataset can be compared visually to the search regime.
"""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PACKAGE_DIR = Path(__file__).resolve().parents[4]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import (
    load_found_pairs,
    load_metadata,
    load_offtarget_matrices,
)

matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["svg.fonttype"] = "none"

MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.5 * 1.05
FIGURE_HEIGHT_MM = 58.0 * 1.05
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 8
AXIS_LABEL_FONT_SIZE = 8
TICK_LABEL_FONT_SIZE = 6
LEGEND_FONT_SIZE = 6

AXIS_LINEWIDTH = 0.5
HIST_EDGE_LINEWIDTH = 0.35
REFERENCE_LINEWIDTH = 1.1
REFERENCE_ZORDER = 4

ON_COLOR = "#3B6FB6"
OFF_COLOR = "#B55A5A"
SELF_COLOR = "#8C6BB1"
RANGE_COLOR = "#2A9D8F"
LIMIT_COLOR = "#4F4F4F"

ONOFF_X_MIN = -24.0
ONOFF_X_MAX = 0.0
SECONDARY_X_MIN = -3.85
SECONDARY_X_MAX = 0.0
BINS_ONOFF = 80
BINS_SELF = 60

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


def style_axes(ax: plt.Axes) -> None:
    ax.tick_params(axis="both", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=2)
    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)
    ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        loc="upper left",
        handlelength=1.4,
    )


def plot_energy_distributions(
    data_path: Path,
    reference_thresholds: dict[str, float],
    out_dir: Path,
    output_prefix: str,
    onoff_title: str = "On and off-target energies",
    self_title: str = "Secondary structure energies",
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    on_target, off_target, self_all = load_energy_distributions(data_path)

    bin_width_onoff = (ONOFF_X_MAX - ONOFF_X_MIN) / BINS_ONOFF
    bin_edges_onoff = np.linspace(
        ONOFF_X_MIN - 0.5 * bin_width_onoff,
        ONOFF_X_MAX - 0.5 * bin_width_onoff,
        BINS_ONOFF + 1,
    )

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    ax.hist(
        off_target,
        bins=bin_edges_onoff,
        density=True,
        color=OFF_COLOR,
        edgecolor="black",
        linewidth=HIST_EDGE_LINEWIDTH,
        label="Off-target",
        zorder=3,
    )
    ax.hist(
        on_target,
        bins=bin_edges_onoff,
        density=True,
        color=ON_COLOR,
        edgecolor="black",
        linewidth=HIST_EDGE_LINEWIDTH,
        label="On-target",
        zorder=2,
    )

    ax.axvline(
        reference_thresholds["min_ontarget"],
        color=RANGE_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="On-target range",
        zorder=REFERENCE_ZORDER,
    )
    ax.axvline(
        reference_thresholds["max_ontarget"],
        color=RANGE_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="_nolegend_",
        zorder=REFERENCE_ZORDER,
    )
    ax.axvline(
        reference_thresholds["offtarget_limit"],
        color=LIMIT_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="Off-target limit",
        zorder=REFERENCE_ZORDER,
    )

    ax.set_xlabel(r"Gibbs free energy, $\Delta G_{\mathrm{assoc}}$ (kcal/mol)", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Density", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_title(onoff_title, fontsize=TITLE_FONT_SIZE, pad=4)
    ax.set_xlim(ONOFF_X_MIN, ONOFF_X_MAX)
    style_axes(ax)
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.22, top=0.90)
    onoff_path = out_dir / f"{output_prefix}_on_vs_off.svg"
    fig.savefig(onoff_path, format="svg", bbox_inches="tight")
    plt.close(fig)

    bin_edges_self = np.linspace(SECONDARY_X_MIN, SECONDARY_X_MAX, BINS_SELF + 1)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    ax.hist(
        self_all,
        bins=bin_edges_self,
        density=True,
        color=SELF_COLOR,
        edgecolor="black",
        linewidth=HIST_EDGE_LINEWIDTH,
        label="Secondary structure",
        zorder=2,
    )
    ax.axvline(
        reference_thresholds["self_energy_limit"],
        color=LIMIT_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="Secondary structure limit",
        zorder=REFERENCE_ZORDER,
    )

    ax.set_xlabel(r"Gibbs free energy, $\Delta G_{\mathrm{sec}}$ (kcal/mol)", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Density", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_title(self_title, fontsize=TITLE_FONT_SIZE, pad=4)
    ax.set_xlim(SECONDARY_X_MIN, SECONDARY_X_MAX)
    style_axes(ax)
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.22, top=0.90)
    self_path = out_dir / f"{output_prefix}_self_energies.svg"
    fig.savefig(self_path, format="svg", bbox_inches="tight")
    plt.close(fig)

    return onoff_path, self_path


if __name__ == "__main__":
    figure_dir = Path(__file__).resolve().parent

    figure1_data_path = (
        figure_dir
        / "data"
        / "figure1_len12_noflank_random_1000pairs_seed41.xlsx"
    )
    hybrid_data_path = (
        figure_dir.parent.parent
        / "benchmarking"
        / "long_seq"
        / "data"
        / "batch_x______sigma1p0_seed41"
        / "len12"
        / "5p_none"
        / "hybrid_len12_5p_none_limitm8p16_budget10000000_init900_seed41.xlsx"
    )

    out_dir = figure_dir / "data" / "plots"
    reference_thresholds = load_reference_thresholds(hybrid_data_path)

    onoff_path, self_path = plot_energy_distributions(
        data_path=figure1_data_path,
        reference_thresholds=reference_thresholds,
        out_dir=out_dir,
        output_prefix="figure1",
    )
    print(f"Wrote {onoff_path}")
    print(f"Wrote {self_path}")

    onoff_path, self_path = plot_energy_distributions(
        data_path=hybrid_data_path,
        reference_thresholds=reference_thresholds,
        out_dir=out_dir,
        output_prefix="hybrid_len12_5p_none",
    )
    print(f"Wrote {onoff_path}")
    print(f"Wrote {self_path}")
