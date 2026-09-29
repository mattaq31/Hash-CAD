"""Create the compact half-page DLS summary figure for Katzi020."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogFormatterMathtext, NullLocator

from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import (
    extract_handle_dicts,
    oneshot_hamming_compute,
)


def read_curves(path: Path) -> dict[tuple[str, float], tuple[np.ndarray, np.ndarray]]:
    """Read and normalize the H24 and H29 curves from a Zetasizer export."""
    curves = {}
    with path.open("r", encoding="cp1252", newline="") as stream:
        for fields in csv.reader(stream, delimiter="\t"):
            if len(fields) != 387:
                continue

            label = fields[0].strip().lower()
            if not label.startswith(("h24 ", "h29 ")):
                continue

            sample = label[:3].upper()
            temperature = float(fields[1])
            delay_us = np.asarray(fields[2:194], dtype=float)
            correlation = np.asarray(fields[195:387], dtype=float)
            curves[(sample, temperature)] = (delay_us, correlation / correlation[0])

    if len(curves) != 24:
        raise ValueError(f"Expected 24 curves, found {len(curves)} in {path}")
    return curves


def fit_tail_exponent(delay_us: np.ndarray, normalized: np.ndarray, t0_us: float) -> float:
    """Fit the exponent q in (1 + delay/t0)^(-2q)."""
    mask = np.isfinite(delay_us) & np.isfinite(normalized) & (delay_us <= 1e5)
    q_values = np.linspace(0.05, 2.0, 20_000)
    fitted = np.power(1.0 + delay_us[mask, np.newaxis] / t0_us, -2.0 * q_values)
    errors = np.mean((normalized[mask, np.newaxis] - fitted) ** 2, axis=0)
    return float(q_values[np.argmin(errors)])


def interaction_valency_counts(design_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return interaction valencies and their counts for one design."""
    slat_length = 32
    megastructure = Megastructure(import_design_file=design_path)
    slat_array = megastructure.generate_slat_occupancy_grid()
    handle_array = megastructure.generate_assembly_handle_grid()
    handle_dict, antihandle_dict = extract_handle_dicts(handle_array, slat_array)
    interaction_scores = oneshot_hamming_compute(handle_dict, antihandle_dict, slat_length)
    return np.unique(slat_length - interaction_scores, return_counts=True)


def logarithmic_marker_indices(delay_us: np.ndarray) -> np.ndarray:
    """Choose roughly evenly spaced marker positions on a logarithmic x-axis."""
    targets = np.logspace(0, 5, 22)
    return np.unique([np.abs(np.log(delay_us) - np.log(target)).argmin() for target in targets])


def make_figure(
    curves: dict[tuple[str, float], tuple[np.ndarray, np.ndarray]],
    exponents: dict[tuple[str, float], float],
    valency_counts: dict[str, tuple[np.ndarray, np.ndarray]],
    t0_us: float,
) -> mpl.figure.Figure:
    """Build the DLS curves, valency histograms, legend, and exponent summary."""
    font_size = 7.0
    line_width = 0.75
    grid_line_width = 0.50
    purple = ("#542788", "#8073AC", "#C2A5CF")
    teal = ("#01665E", "#35978F", "#80CDC1")
    temperatures = (26, 32, 38)

    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": font_size,
            "mathtext.fontset": "stix",
            "axes.labelsize": font_size,
            "axes.titlesize": font_size,
            "xtick.labelsize": font_size,
            "ytick.labelsize": font_size,
            "axes.linewidth": line_width,
            "lines.linewidth": line_width,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "path",
        }
    )

    def style_axes(axis: mpl.axes.Axes) -> None:
        axis.set_axisbelow(True)
        axis.grid(color="#D9D9D9", linewidth=grid_line_width, alpha=0.60)
        for spine in axis.spines.values():
            spine.set_linewidth(line_width)
        axis.tick_params(which="major", width=line_width, length=2.5, pad=1)
        axis.tick_params(which="minor", width=line_width, length=1.5)
        axis.xaxis.labelpad = 0
        axis.yaxis.labelpad = 2

    figure = plt.figure(figsize=(5.00, 3.60))
    grid = figure.add_gridspec(2, 3, width_ratios=(1.0, 1.55, 1.0))
    ax_h24_valency = figure.add_subplot(grid[0, 0])
    ax_h29_valency = figure.add_subplot(grid[1, 0], sharex=ax_h24_valency, sharey=ax_h24_valency)
    ax_h24 = figure.add_subplot(grid[0, 1])
    ax_h29 = figure.add_subplot(grid[1, 1], sharex=ax_h24)
    ax_legend = figure.add_subplot(grid[0, 2])
    ax_q = figure.add_subplot(grid[1, 2])
    figure.subplots_adjust(left=0.15, right=0.985, bottom=0.15, top=0.95, wspace=0.38, hspace=0.38)

    sample_settings = (
        ("H24", ax_h24, ax_h24_valency, purple, "o", "4.7"),
        ("H29", ax_h29, ax_h29_valency, teal, "s", "2.6"),
    )
    fitted_delay = np.logspace(0, 5, 300)

    for sample, correlation_axis, valency_axis, colors, marker, loss in sample_settings:
        for temperature, color in zip(temperatures, colors):
            delay_us, normalized = curves[(sample, temperature)]
            marker_indices = logarithmic_marker_indices(delay_us)
            valid = (
                (delay_us[marker_indices] >= 1.0)
                & (delay_us[marker_indices] <= 1e5)
                & (normalized[marker_indices] >= -0.03)
                & (normalized[marker_indices] <= 1.05)
            )
            indices = marker_indices[valid]
            correlation_axis.scatter(
                delay_us[indices], normalized[indices], s=4.0, marker=marker, color=color, alpha=0.48,
                edgecolors="none", zorder=2,
            )
            fitted_correlation = np.power(1.0 + fitted_delay / t0_us, -2.0 * exponents[(sample, temperature)])
            correlation_axis.plot(fitted_delay, fitted_correlation, color=color, zorder=3)

        correlation_axis.set(
            xscale="log",
            xlim=(0.8, 1.25e5),
            ylim=(-0.03, 1.05),
            xticks=(1, 100, 10000),
            yticks=(0.0, 0.5, 1.0),
            xlabel="Delay time (µs)",
            ylabel="Normalized correlation",
        )
        correlation_axis.set_title(f"Loss = {loss}", pad=1)
        correlation_axis.set_box_aspect(1 / 1.55)
        style_axes(correlation_axis)

        valencies, counts = valency_counts[sample]
        valency_axis.bar(valencies, counts, width=0.82, color=colors[1], edgecolor="black", linewidth=0.35)
        valency_axis.set(
            yscale="log",
            xlim=(-0.65, 8.65),
            ylim=(0.7, 2e5),
            xticks=(0, 4, 8),
            yticks=(1, 1e2, 1e4),
            xlabel=r"Bond count, $v$",
            ylabel=r"Slat pairs, $N_v$",
        )
        valency_axis.set_box_aspect(1)
        valency_axis.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
        valency_axis.yaxis.set_minor_locator(NullLocator())
        valency_axis.set_title("Bond-count distribution", pad=1)
        style_axes(valency_axis)
        valency_axis.grid(axis="x", visible=False)

        selected_exponents = [exponents[(sample, temperature)] for temperature in temperatures]
        ax_q.plot(temperatures, selected_exponents, color=colors[1], zorder=2)
        for temperature, color, exponent in zip(temperatures, colors, selected_exponents):
            ax_q.scatter(temperature, exponent, s=10.0, marker=marker, color=color, edgecolors="none", zorder=3)

    ax_h24.tick_params(axis="x", which="both", labelbottom=True)

    ax_legend.set_axis_off()
    legend_position = ax_legend.get_position()
    ax_legend.set_position(
        [legend_position.x0 - 0.065, legend_position.y0, legend_position.width + 0.045, legend_position.height]
    )
    ax_legend.set(xlim=(0, 1), ylim=(0, 1))
    ax_legend.text(0.46, 0.95, "Fit function:", ha="center", va="top")
    ax_legend.text(0.46, 0.78, r"$y(\tau)=\left(1+\frac{\tau}{t_0}\right)^{-2q}$", ha="center", va="top", fontsize=10)
    for center, loss, colors, marker in ((0.24, "4.7", purple, "o"), (0.74, "2.6", teal, "s")):
        ax_legend.text(center, 0.43, f"Loss = {loss}", ha="center", va="center")
        for y, temperature, color in zip((0.30, 0.18, 0.06), temperatures, colors):
            start = center - 0.17
            ax_legend.plot(
                [start, start + 0.09], [y, y], color=color, marker=marker, markersize=2.8,
                markeredgewidth=0, markevery=[1], clip_on=False,
            )
            ax_legend.text(start + 0.13, y, f"{temperature} °C", va="center")

    ax_q.set(
        xlim=(24.5, 39.5),
        ylim=(0.25, 1.25),
        xticks=temperatures,
        yticks=(0.4, 0.8, 1.2),
        xlabel="Temperature (°C)",
        ylabel="Tail exponent, q",
    )
    ax_q.set_title("Tail exponent", pad=1)
    ax_q.set_box_aspect(1)
    style_axes(ax_q)

    for axis in (ax_h24_valency, ax_h24):
        axis.set_anchor("S")
    for axis in (ax_h29_valency, ax_h29, ax_q):
        axis.set_anchor("N")

    legend_position = ax_legend.get_position()
    top_axis_position = ax_h24.get_position()
    ax_legend.set_position(
        [legend_position.x0, top_axis_position.y0, legend_position.width, top_axis_position.height]
    )
    return figure


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020"),
        help="Katzi020 directory containing data_and_plots and plots.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data_and_plots/melt_h24_h29_better_exp.txt"),
        help="Input file, absolute or relative to --data-root.",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=Path("plots/compact_dls_summary"),
        help="Output path without an extension, absolute or relative to --data-root.",
    )
    parser.add_argument(
        "--h24-design",
        type=Path,
        default=Path(
            r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance"
            r"\design_and_echo\Exports\full_designH24.xlsx"
        ),
        help="H24 design workbook used for the interaction-valency histogram.",
    )
    parser.add_argument(
        "--h29-design",
        type=Path,
        default=Path(
            r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance"
            r"\design_and_echo\Exports\full_designH29.xlsx"
        ),
        help="H29 design workbook used for the interaction-valency histogram.",
    )
    args = parser.parse_args()

    data_root = args.data_root.expanduser().resolve()
    input_path = args.input if args.input.is_absolute() else data_root / args.input
    output_base = args.output_base if args.output_base.is_absolute() else data_root / args.output_base
    t0_us = 259.0

    curves = read_curves(input_path)
    print(f"Loaded {len(curves)} curves from {input_path}", flush=True)
    exponents = {
        key: fit_tail_exponent(delay_us, normalized, t0_us)
        for key, (delay_us, normalized) in curves.items()
    }
    print("Completed tail-exponent fits", flush=True)

    valency_counts = {
        "H24": interaction_valency_counts(args.h24_design.expanduser().resolve()),
        "H29": interaction_valency_counts(args.h29_design.expanduser().resolve()),
    }
    print("Computed H24 and H29 interaction-valency histograms", flush=True)

    figure = make_figure(curves, exponents, valency_counts, t0_us)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    export_options = {"facecolor": "white", "bbox_inches": "tight", "pad_inches": 0.02}
    svg_path = output_base.with_suffix(".svg")
    png_path = output_base.with_suffix(".png")
    figure.savefig(svg_path, **export_options)
    figure.savefig(png_path, dpi=1200, **export_options)
    plt.close(figure)

    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")
    for sample in ("H24", "H29"):
        for temperature in (26, 32, 38):
            print(f"{sample} {temperature:>2} °C: q = {exponents[(sample, temperature)]:.4f}")
