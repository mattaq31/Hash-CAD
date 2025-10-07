from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure
from crisscross.scripts.evolution_analysis.analyse_evo import read_handle_log as rhl
import numpy as np
from crisscross.scripts.evolution_analysis.analyse_evo import intuitive_score as in_sc
import matplotlib.pyplot as plt
from math import factorial



# --- Core math (unchanged) ---
def omega_array(l: int, s: int) -> np.ndarray:
    i = np.arange(1, l + s)  # 1..l+s-1
    return np.maximum(0, np.minimum.reduce([i, np.full_like(i, s), (l + s) - i]))

def aggregated_pmf_poisson(l: int, s: int, n: int, m_max=None):
    omega = omega_array(l, s)
    lam = omega / n
    lam_max = lam.max()
    if m_max is None:
        m_max = int(max(8, np.ceil(lam_max + 6 * np.sqrt(max(lam_max, 1e-12)))))
    m_vals = np.arange(0, m_max + 1)

    fact = np.array([factorial(mi) for mi in m_vals], dtype=float)
    lam_pow = np.stack([np.power(lam, mi) for mi in m_vals], axis=1)
    terms = np.exp(-lam)[:, None] * lam_pow / fact[None, :]
    pmf = terms.mean(axis=0)
    pmf /= pmf.sum()
    return m_vals, pmf

# --- Styled like your empirical plot ---
def plot_theoretical_match_type_counts(l, s, n, x_slats, y_slats,
                                       xrange=(0, 8), yrange=None, savepath=None):
    """
    Bar plot of theoretical counts (frequencies) using Poisson mixture,
    styled to match plot_match_type_counts: same figsize, axes, ticks, log-y.
    """
    # aggregated pmf
    m, pmf = aggregated_pmf_poisson(l, s, n)
    # restrict to desired x range so bars don't get cut off
    m_mask = (m >= xrange[0]) & (m <= xrange[1])
    m = m[m_mask]
    pmf = pmf[m_mask]

    # scale to frequencies
    realizations = 126 * x_slats * y_slats
    freq = pmf * realizations

    # compute y-limits if not provided (give some headroom above max bar)
    if yrange is None:
        ymax = float(freq.max())
        if ymax <= 0:
            ymax = 1.0
        ymax_decade = 10 ** np.ceil(np.log10(ymax * 1.05))
        yrange = (0.5, ymax_decade)

    # draw
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(m, freq, color="steelblue", edgecolor="black", width=0.8, align="center")

    ax.set_xlabel("Match Type")
    ax.set_ylabel("Counts")
    ax.set_title("Theoretical Match Type Distribution (Poisson mixture)")

    # x styling to match
    ax.set_xlim(xrange[0]-0.5, xrange[1]+0.5)
    ax.set_xticks(np.arange(xrange[0], xrange[1] + 1, 1))

    # y styling to match
    ax.set_yscale("log")
    ax.set_ylim(*yrange)

    if savepath:
        fig.savefig(savepath, dpi=300, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()
    return m, freq, yrange


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

    # Store as a plain dict for easy pickling/consumption later
    results = []
    results.append(
        {
            "generation": 1,
            "match_type": match_type,
            "counts": counts,
            "score": score,
        }
    )
    return results

def create_empirical_distribution(file_location):
    megastructure = Megastructure(import_design_file=file_location)


    results = []
    results.append(
        {
            "generation": 1,
            "match_type": match_type,
            "counts": counts,
            "score": score,
        }
    )




def plot_match_type_counts(match_types, counts, savepath=None, yrange=(0.5, 1e5)):
    """
    Plot match type counts as a bar plot with logarithmic y-axis.

    Parameters
    ----------
    match_types : array-like
        Match type categories (e.g., 0,1,2,...).
    counts : array-like
        Corresponding counts for each match type.
    savepath : str, optional
        Path to save the figure. If None, shows the plot.
    yrange : tuple, optional
        (ymin, ymax) for the y-axis. Default = (0.5, 1e6).
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Force x range [0,8] inclusive with bins
    ax.bar(match_types, counts, color="steelblue", edgecolor="black", width=0.8, align="center")

    ax.set_xlabel("Match Type")
    ax.set_ylabel("Counts")
    ax.set_title("Match Type Distribution")

    # X-axis ticks from 0 to 8
    ax.set_xlim(-0.5, 8.5)
    ax.set_xticks(np.arange(0, 9, 1))

    # Y-axis log scale with fixed range
    ax.set_yscale("log")
    ax.set_ylim(yrange)

    #ax.grid(axis="y", which="both", linestyle="--", linewidth=0.5)

    if savepath:
        plt.savefig(savepath, dpi=300, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()

if __name__ == '__main__':
    slat_len =32
    file1="C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports/full_designH24.xlsx"
    r_table= get_counts_in_dict(file1)
    r_1= r_table[0]
    counts = r_1['counts']
    match_types = r_1['match_type']
    plot_match_type_counts(match_types, counts)

    l, s, n = 32, 32, 32
    x_slats, y_slats = 32, 32

    # Example: pass your color array from earlier plots
    #colors = plt.cm.viridis(np.linspace(0, 1, 9))

    m, freq, auto_yrange = plot_theoretical_match_type_counts(l, s, n, x_slats, y_slats, xrange=(0, 8))
    auto_yrange


