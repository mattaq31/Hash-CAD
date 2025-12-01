# ====== imports ======
from pathlib import Path
import os
import csv
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatter
from matplotlib.ticker import LogLocator, LogFormatterMathtext

# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== global style knobs (from your file) ======
BOX_W_MM    = 30.0   # <- use these exact values
BOX_H_MM    = 22.0

LINE_MM_DATA = 0.33

LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_TITLE    = 6
FS_LEGEND   = 5
FONT_FAMILY = "Arial"

# margins (matter only if saving without tight bbox; still used to size inner axes)
MARGIN_L_MM = 5.0
MARGIN_R_MM = 6.0
MARGIN_B_MM = 5.0
MARGIN_T_MM = 6.0

PAD_INCHES  = 0.02

# ====== figure factory (exact inner box size) ======
def make_fig_ax(box_w_mm, box_h_mm):
    """Return (fig, ax, lw_pt) with an inner axes of box_w_mm × box_h_mm (mm)."""
    lw_pt       = mm_to_pt(LINE_MM)
    tick_len_pt = mm_to_pt(TICK_LEN_MM)

    plt.rcParams.update({
        "svg.fonttype": "none",
        "font.family":  FONT_FAMILY,
        "axes.linewidth": lw_pt,
        "lines.linewidth": lw_pt,
        "xtick.labelsize": FS_TICKS,
        "ytick.labelsize": FS_TICKS,
        "legend.title_fontsize": FS_LEGEND,
        "axes.labelsize":  FS_LABELS,
        "axes.titlesize":  FS_TITLE,
        "legend.fontsize": FS_LEGEND,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
    })

    fig_w_mm = box_w_mm + MARGIN_L_MM + MARGIN_R_MM
    fig_h_mm = box_h_mm + MARGIN_B_MM + MARGIN_T_MM
    fig = plt.figure(figsize=(mm_to_in(fig_w_mm), mm_to_in(fig_h_mm)))

    left   = MARGIN_L_MM / fig_w_mm
    bottom = MARGIN_B_MM / fig_h_mm
    ax_w   = box_w_mm / fig_w_mm
    ax_h   = box_h_mm / fig_h_mm
    ax = fig.add_axes([left, bottom, ax_w, ax_h])

    for s in ax.spines.values():
        s.set_linewidth(lw_pt)

    ax.tick_params(which="both", direction="out", length=tick_len_pt, width=lw_pt)
    ax.xaxis.labelpad = -0.4
    ax.yaxis.labelpad = 0.3
    ax.tick_params(axis="x", pad=1.9)
    ax.tick_params(axis="y", pad=1.2)

    return fig, ax, lw_pt

# ====== data loading ======
def load_match_histogram(path):
    """
    Load a CSV of match histograms into a 2D NumPy array + header list.
    - Reads header to get target column count
    - Pads short rows with zeros
    - Casts to float
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    rows = []
    with path.open(newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        n_cols = len(header)
        for row in reader:
            nums = [float(x) if x else 0.0 for x in row]
            if len(nums) < n_cols:
                nums += [0.0] * (n_cols - len(nums))
            rows.append(nums)

    data = np.asarray(rows, dtype=float)
    return data, header

def find_match_columns(header, start_match=0, end_match=10):
    """
    Find indices of '{k} Matches' columns for k in [start_match, end_match], if present.
    Returns list of (name, index, k_int) sorted by k.
    """
    found = []
    name_to_idx = {h.strip(): i for i, h in enumerate(header)}
    for k in range(start_match, end_match + 1):
        key = f"{k} Matches"
        if key in name_to_idx:
            found.append((key, name_to_idx[key], k))
    # In case headers vary like '1 Matches', '2 Matches', etc. with stray spaces:
    if not found:
        # fallback: regex scan for k Matches
        rx = re.compile(r"^\s*(\d+)\s+Matches\s*$")
        for i, h in enumerate(header):
            m = rx.match(h)
            if m:
                k = int(m.group(1))
                if start_match <= k <= end_match:
                    found.append((h, i, k))
        found.sort(key=lambda t: t[2])
    return found

def plot_loglog_matches_vs_index(
    data,
    header,
    start_match=1,
    end_match=4,
    title="Hier könnte ihr Titel stehen",
    output_svg=None,
    colors=None,
):
    sel = find_match_columns(header, start_match, end_match)
    if not sel:
        raise ValueError("No requested match columns found in header.")

    n = data.shape[0]
    x = np.arange(n, dtype=float) + 1.0

    fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

    if colors is None:
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    colors = (colors * ((len(sel) + len(colors) - 1) // len(colors)))[:len(sel)]

    for (name, idx, k), color in zip(sel, colors):
        y = data[:, idx].astype(float)
        y = np.where(y <= 0, 0.1, y)
        # label by k only (e.g., "1", "2", "3", ...)
        ax.loglog(x, y, label=str(k), color=color, linewidth=mm_to_pt(LINE_MM_DATA))

    ax.set_xlabel("Generation")
    ax.set_ylabel("Counts")
    ax.set_title(title, pad=2.7)
    # Grid: horizontal lines only, thinner
    ax.grid(
        True,  # enable grid
        which="major",  # major ticks only
        axis="x",  # only y-direction (horizontal lines)
        linewidth=mm_to_pt(0.10),  # thinner than your default lines
        color="black",  # or e.g. "#999999" for lighter gray
        alpha=0.3  # transparency for softer appearance
    )
    ax.minorticks_off()
    ax.set_xlim(1e0, 1e5)
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=6))
    ax.xaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=()))
    ax.set_ylim(0.65, 3.0*10**6)

    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=7))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))


    # legend with title "Valency"
    ax.legend(
        title="Valency",
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(1., 0.89),
        ncol=1,  # two columns
        columnspacing=0.7,  # horizontal spacing between columns
        handlelength=1.4,  # shorten line length
        handletextpad=0.4,  # space between line and label
        borderaxespad=0.5,  # move closer to plot
        labelspacing=0.35
    )

    if output_svg:
        out_path = Path(output_svg)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    return fig, ax

def compute_scores_from_hist(data, fudge_dG, start_match=0, scale_const=126.0):
    '''Compute 1D score array from raw match histogram data.'''
    # per-row compensator
    compensator = np.sum(data, axis=1) / scale_const

    # select columns starting at start_match
    data = data[:, start_match:]
    k = np.arange(start_match, start_match + data.shape[1])
    weights = np.exp(-fudge_dG * k)

    # weighted sum and score
    num = np.sum(data * weights, axis=1)
    avg = num / compensator
    avg[avg == 0] = np.nan  # avoid log(0)
    return -np.log(avg) / fudge_dG


def plot_scores_overview(
    all_scores,
    title="Score vs Generation",
    output_svg=None,
    x_left=1.0,
    colors=None,
):
    """
    Plot multiple score arrays (one per key in all_scores) on a shared log–x scale.

    Parameters
    ----------
    all_scores : dict[str, np.ndarray]
        Mapping: name -> 1D array of scores
    title : str
        Plot title
    output_svg : str | Path | None
        If given, save SVG to this path (tight bbox)
    x_left : float
        Lower x-limit (default 1.0)
    colors : list[str] | None
        Optional list of line colors (cycled if fewer than series)

    Returns
    -------
    (fig, ax)
    """
    fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

    names = list(all_scores.keys())
    if colors is None:
        colors = ["#004455", "#0088AA", "#00AAD4", "#55DDFF", "#AAEEFF", "#4477AA"]
    colors = (colors * ((len(names) + len(colors) - 1) // len(colors)))[:len(names)]

    for name, color in zip(names, colors):
        s = all_scores[name]
        n = len(s)
        x = np.arange(1, n + 1, dtype=float)
        m = np.isfinite(s)
        if np.any(m):
            ax.plot(
                x[m],
                s[m],
                label=name,
                color=color,
                linewidth=mm_to_pt(LINE_MM_DATA),
            )

    # Axes settings
    ax.set_xscale("log")     # log–x
    ax.set_xlabel("Generation")
    ax.set_ylabel("Loss")
    ax.set_title(title, pad=2.7)
    # Grid: horizontal lines only, thinner
    ax.grid(
        True,  # enable grid
        which="major",  # major ticks only
        axis="x",  # only y-direction (horizontal lines)
        linewidth=mm_to_pt(0.10),  # thinner than your default lines
        color="black",  # or e.g. "#999999" for lighter gray
        alpha=0.3  # transparency for softer appearance
    )
    ax.minorticks_off()
    ax.set_xlim(1e0, 1e5)
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=6))
    ax.xaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=()))



    # Compact legend
    ax.legend(
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(1., 0.89),
        ncol=1,
        columnspacing=0.8,
        handlelength=1.3,
        handletextpad=0.4,
        borderaxespad=0.35,
        borderpad=0.2,
        labelspacing=0.25,
    )

    # Save
    if output_svg:
        out_path = Path(output_svg)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    return fig, ax


# ====== run ======
if __name__ == "__main__":
    # for score now called loss
    start = 0
    all_scores = {}









    CSV_PATH = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\figure_4_example_runs\evo_runs\bird_long_fast\match_histograms.csv"

    name = "Bird"
    OUT_SVG = "C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6/resources/" + name + "_valencies.svg"

    data, header = load_match_histogram(CSV_PATH)
    data_Bird = data
    custom_colors = ["#600700", "#9f241a", "#dc482e", "#f1968f", "#f4cac8"]
    scores = compute_scores_from_hist(data, -10.0, start_match=start, scale_const=126.0)


    # add scores with key Hexagon to all_scores
    all_scores[name] = scores

    fig, ax = plot_loglog_matches_vs_index(
        data,
        header,
        start_match=1,
        end_match=10,
        title="Elimination of Parasitic Interaction",
        output_svg=OUT_SVG,
        colors=custom_colors
    )
    plt.show()

























    CSV_PATH = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\figure_4_example_runs\evo_runs\sunflower_long_fast\match_histograms.csv"

    name = "Sunflower"
    OUT_SVG = "C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6/resources/" + name + "_valencies.svg"

    data, header = load_match_histogram(CSV_PATH)
    data_sunflower = data
    custom_colors = ["#593f00", "#9e7300", "#d6a000", "#fbbe00","#ffdba0"]
    scores = compute_scores_from_hist(data, -10.0, start_match=start, scale_const=126.0)


    # add scores with key Hexagon to all_scores
    all_scores[name] = scores

    fig, ax = plot_loglog_matches_vs_index(
        data,
        header,
        start_match=1,
        end_match=10,
        title="Elimination of Parasitic Interaction",
        output_svg=OUT_SVG,
        colors=custom_colors
    )
    plt.show()

    CSV_PATH = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\figure_4_example_runs\evo_runs\square_long_fast\match_histograms.csv"

    name = "Square"
    OUT_SVG = "C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6/resources/" + name + "_valencies.svg"

    data, header = load_match_histogram(CSV_PATH)
    data_square = data
    custom_colors = ["#004455", "#0088AA", "#46bde2", "#a8dff5"]
    scores = compute_scores_from_hist(data, -10.0, start_match=start, scale_const=126.0)

    # add scores with key Hexagon to all_scores
    all_scores[name] = scores

    fig, ax = plot_loglog_matches_vs_index(
        data,
        header,
        start_match=1,
        end_match=10,
        title="Elimination of Parasitic Interaction",
        output_svg=OUT_SVG,
        colors=custom_colors
    )
    plt.show()







    OUT_SCORES_SVG = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6\resources/scores_overview.svg"
    series_colors = ["#dc482e", "#fbbe00" , "#46bde2"]

    fig, ax = plot_scores_overview(
        all_scores,
        title="Loss Optimization",
        output_svg=OUT_SCORES_SVG,
        x_left=1.0,
        colors=series_colors,
    )
    plt.show()














    CSV_PATH = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\figure_4_example_runs\evo_runs\hexagon_long\match_histograms.csv"

    name = "Hexagon"
    OUT_SVG  = "C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6/resources/" + name +"_valencies.svg"

    data, header = load_match_histogram(CSV_PATH)
    data_hexagon = data
    custom_colors = ["#004455","#0088AA", "#00AAD4", "#55DDFF", "#AAEEFF" ]
    scores = compute_scores_from_hist(data, -10.0, start_match=start, scale_const=126.0)


    # add scores with key Hexagon to all_scores
    all_scores[name] = scores

    fig, ax = plot_loglog_matches_vs_index(
        data,
        header,
        start_match=1,
        end_match=10,
        title="Elimination of Parasitic Interaction",
        output_svg=OUT_SVG,
        colors=custom_colors
    )
    plt.show()