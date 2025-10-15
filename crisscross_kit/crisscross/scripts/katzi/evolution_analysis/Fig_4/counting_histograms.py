# ====== imports ======
from pathlib import Path
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ====== paths & config (edit these) ======
DATA_FOLDER = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\counting_results")
OUTPUT_DIR  = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_4")
SELECTED_CONDITIONS = [24, 27, 29, 30]

# scores (x positions)
SCORE_MAP = {
    24: 7.3068,
    27: 4.7475,
    29: 2.6407,
    30: 2.0565,
}

# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== global style knobs ======
# inner plot-box size used for HISTOGRAMS (boxplot uses 16:9 @ 22mm height)
BOX_W_MM    = 38.0
BOX_H_MM    = 22.0

# lines & fonts
LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_TITLE    = 6
FS_LEGEND   = 5
FONT_FAMILY = "Arial"

# margins (matter only if you save WITHOUT bbox_inches='tight')
MARGIN_L_MM = 5.0
MARGIN_R_MM = 6.0
MARGIN_B_MM = 5.0
MARGIN_T_MM = 6.0

# legend saving
PAD_INCHES  = 0.02   # small pad to avoid clipping with tight bbox

# ====== boxplot visual knobs ======
BOX_WIDTH_DATA   = 0.35     # width of each box in x-axis data units
BOX_COLOR        = "lightblue"
MEDIAN_COLOR     = "green"
MEAN_COLOR       = "red"
FLIER_COLOR      = "black"
FLIER_SIZE_PT    = 1.5      # outlier dot diameter (points)
MEAN_AREA_PT2    = 2.0      # mean diamond area (pt^2) in the PLOT
MEAN_LEGEND_PT   = 3.0      # mean diamond diameter (pt) in the LEGEND

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
        "axes.labelsize":  FS_LABELS,
        "axes.titlesize":  FS_TITLE,
        "legend.fontsize": FS_LEGEND,
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
    ax.xaxis.labelpad = 0.5
    ax.yaxis.labelpad = 0.5
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)

    return fig, ax, lw_pt

# ====== data loading ======
def load_counts_dataframe(data_folder, selected_conditions):
    """Read *_pick_data.csv files, count rows per file. Columns = conditions."""
    raw = {cond: [] for cond in selected_conditions}
    for fn in os.listdir(data_folder):
        if not fn.endswith("_pick_data.csv"):
            continue
        parts = fn.split("_")
        try:
            cond = int(parts[0])
        except (ValueError, IndexError):
            continue
        if cond not in selected_conditions:
            continue
        try:
            df = pd.read_csv(data_folder / fn)
            raw[cond].append(float(len(df)))
        except Exception as e:
            print(f"Error reading {fn}: {e}")

    # pad to equal length
    max_len = max((len(v) for v in raw.values()), default=0)
    for k, v in raw.items():
        if len(v) < max_len:
            v += [np.nan] * (max_len - len(v))
    return pd.DataFrame(raw)

# ====== histograms (one svg per condition) ======
def compute_global_hist_ymax(df_counts, bins):
    ymax = 0.0
    for cond in df_counts.columns:
        counts, _ = np.histogram(df_counts[cond].dropna(), bins=bins)
        if counts.size:
            ymax = max(ymax, float(counts.max()))
    return ymax * 1.10

def save_histograms_per_condition(df_counts, score_map, output_dir, bins=None):
    if bins is None:
        bins = np.arange(0, 160, 5)
    ymax = compute_global_hist_ymax(df_counts, bins)
    output_dir.mkdir(parents=True, exist_ok=True)

    for cond in df_counts.columns:
        data = df_counts[cond].dropna().values
        fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

        ax.hist(data, bins=bins, edgecolor="black", color="lightblue", linewidth=lw_pt)
        ax.set_xlabel("Particles per Image")
        ax.set_ylabel("Counts")
        ax.set_title(f"Score = {score_map.get(int(cond), np.nan):.3f}", pad=6)
        ax.set_xlim(0, 160)
        ax.set_xticks(np.arange(0, 161, 20))
        ax.set_ylim(0, ymax)

        out_svg = output_dir / f"hist_{int(cond)}.svg"
        fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
        plt.close(fig)

def save_boxplot_svg(df_counts, score_map, output_dir):
    """Boxplot (16:9 width, fixed 22 mm height) — same marker sizes, no legend box."""
    scores = [score_map[c] for c in df_counts.columns]
    data   = [df_counts[c].dropna().values for c in df_counts.columns]
    means  = [np.nanmean(d) for d in data]

    # figure
    box_h_mm = BOX_H_MM*1.15
    box_w_mm = (16 / 9) * box_h_mm
    fig, ax, lw_pt = make_fig_ax(box_w_mm, box_h_mm)

    bp = ax.boxplot(
        data,
        positions=scores,
        widths=0.5,  # simple box width
        patch_artist=True,
        manage_ticks=False,
        flierprops=dict(
            marker='o',
            markersize=1.0,
            color='black',
            markerfacecolor='black',
            markeredgecolor='black',
            linestyle='none'
        ),
    )

    for b in bp['boxes']:     b.set(facecolor='lightblue', linewidth=lw_pt)
    for w in bp['whiskers']:  w.set(linewidth=lw_pt)
    for c in bp['caps']:      c.set(linewidth=lw_pt)
    for m in bp['medians']:   m.set(color='green', linewidth=lw_pt)

    # identical mean marker size everywhere
    mean_size = 1
    ax.scatter(scores, means, color='red', marker='D', s=mean_size, zorder=3, label='Mean')

    ax.set_xlabel("Effective Parasitic Interaction Valency")
    ax.set_ylabel("Structures per Image")
    ax.set_xlim(1.35, max(scores) + 1)
    max_tick = int(round(max(scores), 0))
    ax.set_xticks(range(2, max_tick + 2))
    ax.set_xticklabels(range(2, max_tick + 2))

    ax.set_ylim(0, 170)


    # clean legend — same marker size, no border
    median_line = Line2D([], [], color='green', linewidth=lw_pt, label='Median')
    mean_proxy  = Line2D([], [], color='red', marker='D', linestyle='none',
                         markersize=math.sqrt(mean_size), label='Mean')
    leg = ax.legend([median_line, mean_proxy], ["Median", "Mean"],
                    frameon=False, loc='best')

    out_svg = output_dir / "boxplot_score_with_mean_median.svg"
    fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=0.07)
    print(ax.xaxis.label.get_size())
    plt.close(fig)


# ====== run ======
if __name__ == "__main__":
    df_counts = load_counts_dataframe(DATA_FOLDER, SELECTED_CONDITIONS)
    df_counts = df_counts[SELECTED_CONDITIONS]  # enforce column order

    save_histograms_per_condition(df_counts, SCORE_MAP, OUTPUT_DIR)
    save_boxplot_svg(df_counts, SCORE_MAP, OUTPUT_DIR)

