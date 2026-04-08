from math import comb
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogFormatterMathtext, LogLocator

from crisscross.core_functions.megastructures import Megastructure
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import read_handle_log
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import intuitive_score as in_sc
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import (
    extract_handle_dicts,
    oneshot_hamming_compute,
)


MM_PER_INCH = 25.4
SLAT_LEN = 32


def mm_to_in(mm: float) -> float:
    return mm / MM_PER_INCH


def mm_to_pt(mm: float) -> float:
    return (mm / MM_PER_INCH) * 72.0


STYLE = {
    "LINEWIDTH_MM": 0.2,
    "TICK_LEN_MM": 0.4,
    "FONTSIZE_TICKS": 5,
    "FONTSIZE_LABELS": 6,
    "FONTSIZE_TITLE": 6,
    "FONTSIZE_BLOCK_TITLE": 8,
    "FONTSIZE_LEGEND": 5,
    "BOX_W_MM": 28.0,
    "BOX_H_MM": 22.0,
    "MARGIN_L_MM": 5.0,
    "MARGIN_R_MM": 6.0,
    "MARGIN_B_MM": 5.0,
    "MARGIN_T_MM": 6.0,
    "PANEL_GAP_MM": 5.0,
    "ROW_GAP_MM": 6.0,
    "DESIGN_GAP_MM": 16.0,
    "THEORY_LINEWIDTH_MM": 0.3,
}


HANDLE_COUNTS = [8, 16, 32, 48, 64]
DEFAULT_OUTPUT = Path(
    r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\final_figures\revision\figure_SA\plot_distribution_A_theory_test.svg"
)
DESIGNS = [
    {
        "name": "square",
        "input_root": Path(
            r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\library_size_sweep\square"
        ),
        "base_design_file": Path(
            r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\library_size_sweep\square\basic_square.xlsx"
        ),
        "bar_color": "steelblue",
        "display_name": "Square",
    },
    {
        "name": "sunflower",
        "input_root": Path(
            r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\library_size_sweep\sunflower"
        ),
        "base_design_file": Path(
            r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\library_size_sweep\sunflower\basic_sunflower.xlsx"
        ),
        "bar_color": "#b8860b",
        "display_name": "Sunflower",
    },
]


def apply_plot_style() -> tuple[float, float, float]:
    lw_pt = mm_to_pt(STYLE["LINEWIDTH_MM"])
    tick_len_pt = mm_to_pt(STYLE["TICK_LEN_MM"])
    theory_lw_pt = mm_to_pt(STYLE["THEORY_LINEWIDTH_MM"])
    plt.rcParams.update(
        {
            "svg.fonttype": "none",
            "axes.linewidth": lw_pt,
            "patch.linewidth": lw_pt,
            "lines.linewidth": lw_pt,
            "xtick.labelsize": STYLE["FONTSIZE_TICKS"],
            "ytick.labelsize": STYLE["FONTSIZE_TICKS"],
            "axes.labelsize": STYLE["FONTSIZE_LABELS"],
            "axes.titlesize": STYLE["FONTSIZE_TITLE"],
            "legend.fontsize": STYLE["FONTSIZE_LEGEND"],
            "font.family": "Arial",
        }
    )
    return lw_pt, tick_len_pt, theory_lw_pt


def make_panel_figure(n_designs: int, ncols: int, rows_per_design: int = 2):
    lw_pt, tick_len_pt, theory_lw_pt = apply_plot_style()
    nrows = n_designs * rows_per_design

    fig_w_mm = (
        ncols * STYLE["BOX_W_MM"]
        + (ncols - 1) * STYLE["PANEL_GAP_MM"]
        + STYLE["MARGIN_L_MM"]
        + STYLE["MARGIN_R_MM"]
    )
    fig_h_mm = (
        nrows * STYLE["BOX_H_MM"]
        + n_designs * (rows_per_design - 1) * STYLE["ROW_GAP_MM"]
        + (n_designs - 1) * STYLE["DESIGN_GAP_MM"]
        + STYLE["MARGIN_B_MM"]
        + STYLE["MARGIN_T_MM"]
    )

    fig = plt.figure(figsize=(mm_to_in(fig_w_mm), mm_to_in(fig_h_mm)))

    left = STYLE["MARGIN_L_MM"] / fig_w_mm
    ax_w = STYLE["BOX_W_MM"] / fig_w_mm
    ax_h = STYLE["BOX_H_MM"] / fig_h_mm
    col_gap = STYLE["PANEL_GAP_MM"] / fig_w_mm

    axes = []
    row_bottoms = []
    current_bottom_mm = fig_h_mm - STYLE["MARGIN_T_MM"] - STYLE["BOX_H_MM"]
    for row in range(nrows):
        row_bottoms.append(current_bottom_mm / fig_h_mm)
        if row < nrows - 1:
            if (row + 1) % rows_per_design == 0:
                current_bottom_mm -= STYLE["BOX_H_MM"] + STYLE["DESIGN_GAP_MM"]
            else:
                current_bottom_mm -= STYLE["BOX_H_MM"] + STYLE["ROW_GAP_MM"]

    for row in range(nrows):
        row_axes = []
        row_bottom = row_bottoms[row]
        for col in range(ncols):
            col_left = left + col * (ax_w + col_gap)
            row_axes.append(fig.add_axes([col_left, row_bottom, ax_w, ax_h]))
        axes.append(row_axes)

    for row_axes in axes:
        for ax in row_axes:
            for spine in ax.spines.values():
                spine.set_linewidth(lw_pt)
            ax.tick_params(
                axis="both",
                which="both",
                direction="out",
                length=tick_len_pt,
                width=lw_pt,
                pad=1.2,
            )
            ax.grid(False)
            ax.xaxis.labelpad = 0.5
            ax.yaxis.labelpad = 0.5

    return fig, axes, lw_pt, theory_lw_pt


def omega_array(l: int, s: int) -> np.ndarray:
    i = np.arange(1, l + s)
    return np.maximum(0, np.minimum.reduce([i, np.full_like(i, s), (l + s) - i]))


def aggregated_pmf_binomial(l: int, s: int, n: int, m_max: int) -> tuple[np.ndarray, np.ndarray]:
    omega = omega_array(l, s)
    m_vals = np.arange(0, m_max + 1)
    success_prob = 1.0 / n
    terms = np.zeros((omega.shape[0], m_vals.shape[0]), dtype=float)

    for idx, overlap in enumerate(omega):
        for jdx, m in enumerate(m_vals):
            if m <= overlap:
                terms[idx, jdx] = (
                    comb(int(overlap), int(m))
                    * (success_prob ** m)
                    * ((1.0 - success_prob) ** (int(overlap) - int(m)))
                )

    pmf = terms.mean(axis=0)
    pmf /= pmf.sum()
    return m_vals, pmf


def theoretical_counts(handle_count: int, total_count: int, xmax: int) -> tuple[np.ndarray, np.ndarray]:
    m_vals, pmf = aggregated_pmf_binomial(SLAT_LEN, SLAT_LEN, handle_count, xmax)
    return m_vals, pmf * total_count


def get_counts_in_dict(handle_array_file: Path, slat_array: np.ndarray) -> dict:
    handle_array = read_handle_log(str(handle_array_file))
    handle_dict, antihandle_dict = extract_handle_dicts(handle_array, slat_array)
    hamming_results = oneshot_hamming_compute(handle_dict, antihandle_dict, SLAT_LEN)

    matches = -(hamming_results - SLAT_LEN)
    flat_matches = matches.flatten()
    score = in_sc(flat_matches)
    match_type, counts = np.unique(flat_matches, return_counts=True)

    return {
        "match_type": match_type,
        "counts": counts,
        "score": score,
        "total_count": int(np.sum(counts)),
    }


def collect_all_distributions(input_root: Path, slat_array: np.ndarray) -> list[dict]:
    all_data = []
    for handle_count in HANDLE_COUNTS:
        run_dir = input_root / f"handles_{handle_count}"
        initial_data = get_counts_in_dict(run_dir / "best_handle_array_initial.xlsx", slat_array)
        final_data = get_counts_in_dict(
            run_dir / "best_handle_array_generation_2000.xlsx",
            slat_array,
        )
        all_data.append(
            {
                "handle_count": handle_count,
                "initial": initial_data,
                "final": final_data,
            }
        )
    return all_data


def draw_histogram(
    ax,
    match_types,
    counts,
    title,
    lw_pt,
    ymax,
    xmax,
    score,
    bar_color,
    handle_count,
    theory_lw_pt,
    show_theory,
    y_limits,
):
    ax.bar(
        match_types,
        counts,
        color=bar_color,
        edgecolor="black",
        linewidth=lw_pt,
        align="center",
        width=0.8,
    )

    if show_theory:
        theory_x, theory_y = theoretical_counts(handle_count, int(np.sum(counts)), xmax)
        ax.plot(
            theory_x,
            theory_y,
            color="black",
            linewidth=theory_lw_pt,
            zorder=5,
            label="Predicted",
        )
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(0.12, 1.01),
            frameon=False,
            handlelength=1.5,
            borderaxespad=0.2,
        )

    ax.set_title(title)
    ax.set_xlim(-0.6, xmax + 0.6)
    ax.set_xticks(np.arange(0, xmax + 1, 1))
    ax.set_yscale("log")
    ax.set_ylim(y_limits)
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=12))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.yaxis.set_minor_locator(plt.NullLocator())
    ax.text(
        0.98,
        0.955,
        f"Loss = {score:.2f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=STYLE["FONTSIZE_LEGEND"],
    )


def plot_grid(all_design_data: list[dict], savepath: Path) -> None:
    fig, axes, lw_pt, theory_lw_pt = make_panel_figure(
        n_designs=len(all_design_data),
        ncols=len(HANDLE_COUNTS),
    )

    global_ymax = max(
        np.max(dataset[state]["counts"])
        for design_data in all_design_data
        for dataset in design_data["distributions"]
        for state in ("initial", "final")
    )
    global_ymax = 10 ** np.ceil(np.log10(global_ymax * 1.1))

    for design_index, design_data in enumerate(all_design_data):
        top_row = 2 * design_index
        bottom_row = top_row + 1
        xmax = int(
            max(
                np.max(dataset[state]["match_type"])
                for dataset in design_data["distributions"]
                for state in ("initial", "final")
            )
        )
        if design_data["name"] == "square":
            y_limits = (0.5, 3e5)
        else:
            y_limits = (0.5, global_ymax)

        for col, dataset in enumerate(design_data["distributions"]):
            draw_histogram(
                axes[top_row][col],
                dataset["initial"]["match_type"],
                dataset["initial"]["counts"],
                f'{dataset["handle_count"]} Handles',
                lw_pt,
                global_ymax,
                xmax,
                dataset["initial"]["score"],
                design_data["bar_color"],
                dataset["handle_count"],
                theory_lw_pt,
                design_data["name"] == "square",
                y_limits,
            )
            draw_histogram(
                axes[bottom_row][col],
                dataset["final"]["match_type"],
                dataset["final"]["counts"],
                "",
                lw_pt,
                global_ymax,
                xmax,
                dataset["final"]["score"],
                design_data["bar_color"],
                dataset["handle_count"],
                theory_lw_pt,
                design_data["name"] == "square",
                y_limits,
            )

        axes[top_row][2].text(
            0.5,
            1.22,
            design_data["display_name"],
            transform=axes[top_row][2].transAxes,
            ha="center",
            va="bottom",
            fontsize=STYLE["FONTSIZE_BLOCK_TITLE"],
        )

        for col in range(len(design_data["distributions"])):
            axes[top_row][col].set_xlabel("Bond Count")
            axes[bottom_row][col].set_xlabel("Bond Count")
            if col > 0:
                axes[top_row][col].set_yticklabels([])
                axes[bottom_row][col].set_yticklabels([])

        axes[top_row][0].set_ylabel("Initial\nCounts")
        axes[bottom_row][0].set_ylabel("Generation 2000\nCounts")

    savepath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(savepath, format="svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    all_design_data = []
    for design in DESIGNS:
        megastructure = Megastructure(import_design_file=str(design["base_design_file"]))
        slat_array = megastructure.generate_slat_occupancy_grid()
        distributions = collect_all_distributions(design["input_root"], slat_array)
        all_design_data.append(
            {
                "name": design["name"],
                "display_name": design["display_name"],
                "bar_color": design["bar_color"],
                "distributions": distributions,
            }
        )

    plot_grid(all_design_data, DEFAULT_OUTPUT)
    print(f"Saved: {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    main()
