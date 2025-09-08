from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pickle

# --- Style Settings (from your standards) ---
LINEWIDTH = 3.5
LINEWIDTH_AXIS = LINEWIDTH*0.75
LINEWIDTH_LINE = LINEWIDTH*0.75
TICK_WIDTH = LINEWIDTH*0.75
TICK_LENGTH = 6

FONTSIZE_TICKS = 16
FONTSIZE_LABELS = 19
FONTSIZE_TITLE = 19
FONTSIZE_LEGEND = 16

FIGSIZE = (8, 5)


def load_results_pkl(in_path):
    """
    Load results previously saved with save_results_pkl(...).
    """
    with open(in_path, "rb") as f:
        return pickle.load(f)


def alt_score_function(res_dic, fudge_dG):
    """
    Return the score on the SAME scale as the stored one:
        score = -ln(126 * avg(exp(-fudge_dG * m))) / fudge_dG
    where m are the match counts (res_dic["match_type"]) and counts are res_dic["counts"].
    """
    counts = np.asarray(res_dic["counts"], dtype=np.float64)
    matchtype = np.asarray(res_dic["match_type"], dtype=np.float64)

    # Weighted average of exp(-fudge_dG * m)
    avg = np.sum(counts * np.exp(-fudge_dG * matchtype)) / np.sum(counts)

    # Same transform as the original score
    return -np.log(avg) / fudge_dG



def tm_from_data_cal(
    res_dic,
    C,                               # concentration in M
    delta_H_cal      = -44000.0,     # cal/mol   (AT-rich 7-mer ballpark)
    delta_S_eff_cal  = -126.0,       # cal/(mol·K)
    delta_S_init_cal = -100.0,        # cal/(mol·K)  (larger initiation penalty)
    u = 126.0,
    Rcal = 1.987204258               # cal/(mol·K)
):
    counts  = np.asarray(res_dic["counts"], dtype=float)
    match_i = np.asarray(res_dic["match_type"], dtype=float)

    # dominant contact multiplicity i*
    i_star = int(np.max(match_i[counts > 0]))
    print(delta_H_cal/(delta_S_eff_cal)-273.15)
    # weights
    A        = counts.sum()
    a_i_star = counts[match_i == i_star].sum()

    s0  = delta_S_init_cal / Rcal
    chi = A / (u * a_i_star * C)  # effective 1/C scaled by A/(u a_i*)
    TmK = delta_H_cal / (delta_S_eff_cal - (Rcal / i_star) * (np.log(chi) - s0))
    return  TmK - 273.15

def _iter_records(results):
    """
    Yield (generation, match_types, counts, score) from dict or tuple records.
    """
    for rec in results:
        if isinstance(rec, dict):
            yield rec["generation"], rec["match_type"], rec["counts"], rec["score"]
        else:
            gen, mt, cnt, sc = rec
            yield gen, mt, cnt, sc


def extract_match_type_at_elimination(m_type,results):
    data = {}
    for generation, match_types, counts, _score in _iter_records(results):
        for m, c in zip(match_types, counts):
            data.setdefault(int(m), {})[int(generation)] = int(c)


    match_types_sorted = sorted(data.keys())
    last_eliminated = m_type-1
    mask = data

    return mask

def plot_match_counts(
    results,
    logscaley=True,
    logscalex=True,
    savepath=None,
    colors=None,
    x_range=None
):
    data = {}
    for generation, match_types, counts, _score in _iter_records(results):
        for m, c in zip(match_types, counts):
            data.setdefault(int(m), {})[int(generation)] = int(c)


    match_types_sorted = sorted(data.keys())

    # if no custom colors provided: dark red → red → gray → green → dark green
    if colors is None:
        colors = ["#8b0000", "#e31a1c", "#aaaaaa", "#33a02c", "#006400"]

    # build a smooth colormap from the provided anchors
    cmap = mcolors.LinearSegmentedColormap.from_list("custom", colors, N=256)
    norm = plt.Normalize(min(match_types_sorted), max(match_types_sorted))

    fig, ax = plt.subplots(figsize=FIGSIZE)
    for m in match_types_sorted:
        gen_dict = data[m]
        gens = sorted(gen_dict.keys())
        vals = [gen_dict[g] for g in gens]
        color = cmap(norm(m))
        ax.plot(
            gens,
            vals,
            linestyle="-",
            linewidth=LINEWIDTH_LINE,
            label=f"{m} Binding Sites",
            color=color,
        )

    if x_range is not None:
        ax.set_xlim(x_range)
    ax.set_xlabel("Generation", fontsize=FONTSIZE_LABELS)
    ax.set_ylabel("Occurrences", fontsize=FONTSIZE_LABELS)
    ax.set_title("Elimination of Pairwise Interaction Modes",
                 fontsize=FONTSIZE_TITLE, pad=10)

    if logscaley:
        ax.set_yscale("log")
    if logscalex:
        ax.set_xscale("log")

    ax.tick_params(axis="both", which="major",
                   labelsize=FONTSIZE_TICKS, width=TICK_WIDTH, length=TICK_LENGTH)
    for spine in ax.spines.values():
        spine.set_linewidth(LINEWIDTH_AXIS)

    ax.legend(fontsize=FONTSIZE_LEGEND, loc="best")
    plt.tight_layout()
    if savepath:
        plt.savefig(savepath, bbox_inches="tight")
    else:
        plt.show()



def plot_stored_score(
    results,
    logscalex=False,
    logscaley=False,
    savepath=None,
    color="crimson",
    yrange=None,
):
    """Plot the stored score vs generation."""
    gens, scores = [], []
    for generation, _mt, _cnt, score in _iter_records(results):
        gens.append(generation)
        scores.append(float(score))
    if not gens:
        raise ValueError("No score data found.")

    order = np.argsort(gens)
    gens = np.asarray(gens, float)[order]
    scores = np.asarray(scores, float)[order]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(gens, scores, "-", linewidth=LINEWIDTH_LINE, color=color, label="Stored")

    ax.set_xlabel("Generation", fontsize=FONTSIZE_LABELS)
    ax.set_ylabel("Score", fontsize=FONTSIZE_LABELS)
    ax.set_title("Score vs Generation (stored)", fontsize=FONTSIZE_TITLE, pad=10)

    if logscaley: ax.set_yscale("log")
    if logscalex: ax.set_xscale("log")
    if yrange is not None: ax.set_ylim(*yrange)

    ax.tick_params(axis="both", which="major",
                   labelsize=FONTSIZE_TICKS, width=TICK_WIDTH, length=TICK_LENGTH)
    for s in ax.spines.values(): s.set_linewidth(LINEWIDTH_AXIS)
    ax.legend(fontsize=FONTSIZE_LEGEND)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches="tight") if savepath else plt.show()


def plot_alt_score(
    results,
    fudge_dG,
    logscalex=False,
    logscaley=False,
    savepath=None,
    color="#1a0261",
    yrange=None,
    xrange=None
):
    """Plot the alternative score (recomputed from histogram, same scale)."""
    gens, scores = [], []
    for generation, match_types, counts, _score in _iter_records(results):
        rec = {"match_type": match_types, "counts": counts}
        gens.append(generation)
        scores.append(alt_score_function(rec, fudge_dG))
    if not gens:
        raise ValueError("No histogram data found.")

    order = np.argsort(gens)
    gens = np.asarray(gens, float)[order]
    scores = np.asarray(scores, float)[order]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(gens, scores, linewidth=LINEWIDTH_LINE, color=color, label="Evaluations")
    ax.grid(axis='y')
    ax.grid(axis='x')
    # manually add gridlines where you want them
    #for y in range(0, int(ax.get_ylim()[1]) + 1, 1):  # every 2 units, for example
    #    ax.axhline(y=y, color="gray", linewidth=1.2, linestyle="-", zorder=0)


    ax.set_xlabel("Generation", fontsize=FONTSIZE_LABELS)
    ax.set_ylabel("Number of Binding Sites", fontsize=FONTSIZE_LABELS)
    ax.set_title("Mean Pairwise Interaction vs Generation", fontsize=FONTSIZE_TITLE, pad=10)

    if logscaley: ax.set_yscale("log")
    if logscalex: ax.set_xscale("log")
    if yrange is not None: ax.set_ylim(*yrange)
    if xrange is not None: ax.set_xlim(*xrange)

    ax.tick_params(axis="both", which="major",
                   labelsize=FONTSIZE_TICKS, width=TICK_WIDTH, length=TICK_LENGTH)
    for s in ax.spines.values(): s.set_linewidth(LINEWIDTH_AXIS)
    ax.legend(fontsize=FONTSIZE_LEGEND, loc="best", frameon=False)
    plt.tight_layout()
    plt.tight_layout()
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches="tight") if savepath else plt.show()

def plot_tm_vs_generation(
    results,
    C,                  # concentration in M
    fudge_params=None,  # dict with delta_H_cal, delta_S_eff_cal, etc. (optional)
    logscalex=False,
    logscaley=False,
    savepath=None,
    color="teal",
    yrange=None,
):
    """
    Plot melting temperature (Tm, °C) vs generation.

    Parameters
    ----------
    results : list
        Results list (dict or tuple format).
    C : float
        Concentration in M.
    fudge_params : dict, optional
        Overrides for tm_from_data_cal parameters.
    """
    gens, tms = [], []

    for generation, match_types, counts, _score in _iter_records(results):
        rec = {"match_type": match_types, "counts": counts}
        # forward kwargs if provided
        if fudge_params is None:
            tm = tm_from_data_cal(rec, C)
        else:
            tm = tm_from_data_cal(rec, C, **fudge_params)
        gens.append(generation)
        tms.append(tm)

    if not gens:
        raise ValueError("No Tm data found.")

    order = np.argsort(gens)
    gens = np.asarray(gens, float)[order]
    tms = np.asarray(tms, float)[order]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(gens, tms, "-", linewidth=LINEWIDTH_LINE, color=color, label="Tm")

    ax.set_xlabel("Generation", fontsize=FONTSIZE_LABELS)
    ax.set_ylabel("Tm (°C)", fontsize=FONTSIZE_LABELS)
    ax.set_title("Melting Temperature vs Generation", fontsize=FONTSIZE_TITLE, pad=10)

    if logscaley: ax.set_yscale("log")
    if logscalex: ax.set_xscale("log")
    if yrange is not None: ax.set_ylim(*yrange)

    ax.tick_params(axis="both", which="major",
                   labelsize=FONTSIZE_TICKS, width=TICK_WIDTH, length=TICK_LENGTH)
    for s in ax.spines.values(): s.set_linewidth(LINEWIDTH_AXIS)
    ax.legend(fontsize=FONTSIZE_LEGEND)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches="tight") if savepath else plt.show()


if __name__ == "__main__":
    pkl_path1 = Path(r"D:\Wyss_experiments\Evolution_analysis/evo_run_hexagon_2/evolution_results2.pkl")
    results1 = load_results_pkl(pkl_path1)

    pkl_path2 = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\katzi_long_term_hexa_evo_renamed2\evolution_results24000_onwards.pkl")
    results2 = load_results_pkl(pkl_path2)
    results = results1 + results2
    # use your own color anchors
    my_colors = ["#800000", "#a52a2a", "#555555", "#006400", "#2e8b57"]


    plot_match_counts(
        results,
        colors = my_colors,
        logscalex=True,
        savepath=r"D:\Wyss_experiments\Evolution_analysis/match_counts_hexagon.pdf",
        x_range=[1,1000000]
    )


    # stored
    plot_stored_score(
        results,
        savepath=r"D:\Wyss_experiments\Evolution_analysis/stored_score_hexagon.pdf",
        color="crimson",
        yrange=(1.7, 5.2),
    )

    # alt (same scale)
    fudge_dGs = [-15]  # <- same value used when saving the original scores

    for fudge_dG in fudge_dGs:
        plot_alt_score(
            results,
            fudge_dG=fudge_dG,
            logscalex=True,
            savepath=r"D:\Wyss_experiments\Evolution_analysis\score_hexagon_alt_score"+ str(fudge_dG) +".pdf",
            color="#83399e",
            yrange=[2,4.5],
            xrange=[0.75,30000]
        )

    fudge = dict(delta_H_cal=-46500.0, delta_S_eff_cal=-138.0, delta_S_init_cal=-30.0)
    plot_tm_vs_generation(
        results,
        C=0.8e-6,  # example concentration
        fudge_params=fudge,
        logscalex=True,
        savepath=r"D:\Wyss_experiments\Evolution_analysis\tm_vs_generation_hexagon.pdf",
        color="teal",
    )


    tes =  extract_match_type_at_elimination(2,results)