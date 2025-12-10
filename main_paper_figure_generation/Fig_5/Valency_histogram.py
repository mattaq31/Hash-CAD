from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import read_handle_log as rhl
import numpy as np
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import intuitive_score as in_sc
import matplotlib.pyplot as plt
from math import factorial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext

# -----------------------------
# Unit helpers
# -----------------------------
MM_PER_INCH = 25.4
def mm_to_in(mm: float) -> float:
    return mm / MM_PER_INCH

def mm_to_pt(mm: float) -> float:
    # 1 in = 72 pt
    return (mm / MM_PER_INCH) * 72.0

# -----------------------------
# Centralized appearance config
# (all lengths in mm where applicable)
# -----------------------------
STYLE = {
    "LINEWIDTH_MM": 0.2,   # <- requested 0.15 mm everywhere
    "TICK_LEN_MM": 0.4,     # you had 6 (assumed "points"); now in mm for clarity
    "FONTSIZE_TICKS": 5,
    "FONTSIZE_LABELS": 6,
    "FONTSIZE_TITLE": 6,
    "FONTSIZE_LEGEND": 5,
    # Exact inner plot-box (axes) size in mm:
    "BOX_W_MM": 28,       # mm
    "BOX_H_MM": 22.0,       # mm
    # Margins around the box to fit labels/ticks (mm). Adjust to taste.
    "MARGIN_L_MM": 5.0,
    "MARGIN_R_MM": 6.0,
    "MARGIN_B_MM": 5.0,
    "MARGIN_T_MM": 6.0,
}

# -----------------------------
# Style + figure/axes creation
# -----------------------------
def set_style_and_make_box(
    box_w_mm: float = STYLE["BOX_W_MM"],
    box_h_mm: float = STYLE["BOX_H_MM"],
    margin_l_mm: float = STYLE["MARGIN_L_MM"],
    margin_r_mm: float = STYLE["MARGIN_R_MM"],
    margin_b_mm: float = STYLE["MARGIN_B_MM"],
    margin_t_mm: float = STYLE["MARGIN_T_MM"],
    linewidth_mm: float = STYLE["LINEWIDTH_MM"],
    tick_len_mm: float = STYLE["TICK_LEN_MM"],
    fontsize_ticks: int = STYLE["FONTSIZE_TICKS"],
    fontsize_labels: int = STYLE["FONTSIZE_LABELS"],
    fontsize_title: int = STYLE["FONTSIZE_TITLE"],
    fontsize_legend: int = STYLE["FONTSIZE_LEGEND"],
):
    """
    Apply mm-based style and return (fig, ax) with an axes whose *inner box*
    size is exactly (box_w_mm x box_h_mm). Output SVG will preserve this size.

    Returns
    -------
    fig, ax : matplotlib Figure and Axes
    """
    # Convert key lengths
    lw_pt = mm_to_pt(linewidth_mm)
    tick_len_pt = mm_to_pt(tick_len_mm)

    # Global rcParams
    plt.rcParams.update({
        # Keep text as text in SVG
        "svg.fonttype": "none",
        # Line widths (pt)
        "axes.linewidth": lw_pt,
        "patch.linewidth": lw_pt,
        "lines.linewidth": lw_pt,
        # Font sizes
        "xtick.labelsize": fontsize_ticks,
        "ytick.labelsize": fontsize_ticks,
        "axes.labelsize": fontsize_labels,
        "axes.titlesize": fontsize_title,
        "legend.fontsize": fontsize_legend,
    })
    plt.rcParams["font.family"] = "Arial"

    # Compute total figure size in inches from desired box + margins (in mm)
    fig_w_mm = box_w_mm + margin_l_mm + margin_r_mm
    fig_h_mm = box_h_mm + margin_b_mm + margin_t_mm
    fig_w_in = mm_to_in(fig_w_mm)
    fig_h_in = mm_to_in(fig_h_mm)

    fig = plt.figure(figsize=(fig_w_in, fig_h_in))
    # Axes position as a fraction of figure size so that inner axes equals (box_w_mm, box_h_mm)
    left   = margin_l_mm / fig_w_mm
    bottom = margin_b_mm / fig_h_mm
    ax_w   = box_w_mm / fig_w_mm
    ax_h   = box_h_mm / fig_h_mm
    ax = fig.add_axes([left, bottom, ax_w, ax_h])

    # Spines and ticks
    for spine in ax.spines.values():
        spine.set_linewidth(lw_pt)

    ax.tick_params(which="both", direction="out",
                   length=tick_len_pt, width=lw_pt)

    # Grid (off by default)
    ax.grid(False)

    # Move labels and ticks closer to the axes box
    ax.xaxis.labelpad = 0.5  # default is ~4–6 pt
    ax.yaxis.labelpad = 0.5

    ax.tick_params(
        axis="x", pad=1.2,  # distance between ticks and labels
        which="both", direction="out", length=tick_len_pt, width=lw_pt
    )
    ax.tick_params(
        axis="y", pad=1.2,
        which="both", direction="out", length=tick_len_pt, width=lw_pt
    )

    return fig, ax, lw_pt  # return lw_pt for consistent edge widths elsewhere

# -----------------------------
# Your domain helpers (unchanged)
# -----------------------------
def get_counts_in_dict(file_location):
    slat_len = 32
    megastructure = Megastructure(import_design_file=file_location)
    slat_array = megastructure.generate_slat_occupancy_grid()
    handle_array = megastructure.generate_assembly_handle_grid()
    handle_dict, antihandle_dict = extract_handle_dicts(handle_array, slat_array)
    hamming_results = oneshot_hamming_compute(handle_dict, antihandle_dict, slat_len)

    matches = -(hamming_results - slat_len)
    flat_matches = matches.flatten()
    score = in_sc(flat_matches)

    match_type, counts = np.unique(flat_matches, return_counts=True)

    results = [{
        "generation": 1,
        "match_type": match_type,
        "counts": counts,
        "score": score,
    }]
    return results

# -----------------------------
# Plot function using exact box sizing & style
# -----------------------------
def plot_valency_vs_counts(match_types, counts, savepath=None):
    """
    Plot match type counts as a bar plot (log y) with an exact inner plot-box of 32×24 mm.
    Line widths are 0.15 mm (as requested). Output is vector-perfect in SVG.
    """
    fig, ax, lw_pt = set_style_and_make_box()  # uses the 32x24 mm defaults

    # Bars
    ax.bar(match_types, counts, edgecolor="black", linewidth=lw_pt, align="center", width=0.8)

    # Labels
    ax.set_xlabel("Interaction Valency")
    ax.set_ylabel("Counts")


    # X ticks 0..8
    ax.set_xlim(-0.6, 8.6)
    ax.set_xticks(np.arange(0, 9, 1))

    # Log y

    ax.set_yscale("log")
    ax.set_ylim((0.5, 1.3e5))
    ax.yaxis.set_minor_locator(plt.NullLocator())
    # Major ticks exactly at 10^n; no minors
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=12))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))  # labels as 10^n (nice for pubs)
    ax.yaxis.set_minor_locator(plt.NullLocator())  # keep minors off

    # Save / show
    if savepath:
        fig.savefig(savepath, format="svg", bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


def alt_score_function(res_dic, fudge_dG):
    """
    Return the score on the SAME scale as the stored one:
        score = -ln(126 * avg(exp(-fudge_dG * m))) / fudge_dG
    where m are the match counts (res_dic["match_type"]) and counts are res_dic["counts"].
    """
    counts = np.asarray(res_dic["counts"], dtype=np.float64)
    matchtype = np.asarray(res_dic["match_type"], dtype=np.float64)

    # Weighted average of exp(-fudge_dG * m)
    avg = np.sum(counts * np.exp(-fudge_dG * matchtype)) *(126/ np.sum(counts))

    # Same transform as the original score
    return np.log(avg) / (-fudge_dG)
# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    dg= -10

    # these design files can be obtained from Zenodo too
    file1 = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH24.xlsx"
    r_table = get_counts_in_dict(file1)
    r_1 = r_table[0]
    counts = r_1['counts']
    match_types = r_1['match_type']

    Loss = alt_score_function(r_1, fudge_dG=dg)
    print("H24:")
    print("Loss:", Loss)
    out_svg = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_4\resources\fig_H24.svg"
    plot_valency_vs_counts(match_types, counts, savepath=out_svg)

    file1 = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH27.xlsx"
    r_table = get_counts_in_dict(file1)
    r_1 = r_table[0]
    counts = r_1['counts']
    match_types = r_1['match_type']
    Loss = alt_score_function(r_1, fudge_dG=dg)
    print("H27:")
    print("Loss:", Loss)
    out_svg = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_4\resources\fig_H27.svg"
    plot_valency_vs_counts(match_types, counts, savepath=out_svg)


    file1 = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH29.xlsx"
    r_table = get_counts_in_dict(file1)
    r_1 = r_table[0]
    counts = r_1['counts']
    match_types = r_1['match_type']
    Loss = alt_score_function(r_1, fudge_dG=dg)
    print("H29:")
    print("Loss:", Loss)
    out_svg = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_4\resources\fig_H29.svg"
    plot_valency_vs_counts(match_types, counts, savepath=out_svg)


    file1 = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH30.xlsx"
    r_table = get_counts_in_dict(file1)
    r_1 = r_table[0]
    counts = r_1['counts']
    match_types = r_1['match_type']
    Loss = alt_score_function(r_1, fudge_dG=dg)
    print("H30:")
    print("Loss:", Loss)
    out_svg = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_4\resources\fig_H30.svg"
    plot_valency_vs_counts(match_types, counts, savepath=out_svg)
