#!/usr/bin/env python3
# Overlayed time-series boxplots for two conditions at the EXACT same x (no offsets).
# Implementation uses ONE ax.boxplot call with duplicated positions [t, t, t2, t2, ...]
# to eliminate any per-call alignment drift. Dark outlines & outliers; light interiors.
# Legend entries: "Loss = …". Wider Y range is adopted automatically.

# ====== imports ======
import os, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== style knobs (adjust here) ======
BOX_W_MM    = 75
BOX_H_MM    = 36.0

LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 6
FS_LABELS   = 7
FS_TITLE    = 7
FS_LEGEND   = 6
FONT_FAMILY = "Arial"

MARGIN_L_MM = 5.0
MARGIN_R_MM = 6.0
MARGIN_B_MM = 5.0
MARGIN_T_MM = 6.0

PAD_INCHES  = 0.02

# ---- overlay-specific knobs ----
A_FACE      = "#cfe8ff"     # light interior for condition A
A_EDGE      = "#1557a6"     # dark outline/outliers for condition A
B_FACE      = "#ffd3c9"     # light interior for condition B
B_EDGE      = "#9f241a"     # dark outline/outliers for condition B
A_ALPHA     = 1         # face transparency A (0..1)
B_ALPHA     = 1          # face transparency B (0..1)

BOX_WIDTH_DATA   = 2.2      # width of each box in data-space units (time)
FLIER_SIZE_PT    = 1.2      # outlier marker size (pt)
MEDIAN_LW_SCALE  = 1.0      # multiply base line width for median line
WHISKER_CAP_SCALE= 1.0      # multiply base line width for whiskers/caps
SHOW_MEAN_MARKERS= False    # (not typical with overlayed boxes)

X_MAX_DEFAULT    = 120      # fallback x max if needed
XTICK_STEP       = 10       # step spacing for x ticks

def make_fig_ax(box_w_mm=BOX_W_MM, box_h_mm=BOX_H_MM):
    """Create a figure/axis with mm/pt-consistent sizing and line widths."""
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
        "legend.title_fontsize": FS_LEGEND,
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
    ax.xaxis.labelpad = 0.8
    ax.yaxis.labelpad = 0.5
    ax.tick_params(axis="x", pad=1.4)
    ax.tick_params(axis="y", pad=1.2)
    return fig, ax, lw_pt

# ---------- data prep for ONE condition ----------
def load_condition_counts(data_folder, condition):
    """
    Build a counts table for a single condition.
    Returns: times_sorted (list[int]), data (list[np.ndarray]), means (list[float]), y_max (float)
    """
    time_to_counts = {}
    for fn in os.listdir(data_folder):
        if not fn.endswith('_pick_data.csv'):
            continue
        try:
            parts = fn.split('_')[0].split()
            cond = parts[0]
            t = int(parts[1].replace('h', ''))
        except Exception:
            continue
        if cond != condition:
            continue
        try:
            df = pd.read_csv(Path(data_folder, fn))
            time_to_counts.setdefault(t, []).append(len(df))
        except Exception as e:
            print(f"Error reading {fn}: {e}")

    if not time_to_counts:
        raise ValueError(f"No files found for condition '{condition}'.")

    df_counts = pd.DataFrame({t: pd.Series(c) for t, c in time_to_counts.items()})
    df_counts.replace(0, np.nan, inplace=True)

    times_sorted = sorted(df_counts.columns)
    data = [df_counts[t].dropna().values for t in times_sorted]
    means = [np.nanmean(d) for d in data]
    y_max = float(np.nanmax(df_counts.values)) * 1.05 if np.isfinite(df_counts.values).any() else 1.0
    return times_sorted, data, means, y_max

# ---------- single-call overlay plotting ----------
def plot_two_conditions_overlay_singlecall(
    *,
    condition_A, times_A, data_A, y_max_A, loss_A,
    condition_B, times_B, data_B, y_max_B, loss_B,
    output_svg,
    title=None,
    x_max=None,
    xtick_step=XTICK_STEP,
):
    """
    Overlay two sets by calling ax.boxplot ONCE with positions duplicated per time.
    For each time t in the union, we append [data_A_at_t (if any), data_B_at_t (if any)]
    and positions [t, t]. Then color boxes by index (A, B).
    """
    fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

    # Make a unified, sorted list of all times
    all_times = sorted(set(times_A) | set(times_B))
    if x_max is None:
        x_max = max(all_times) if all_times else X_MAX_DEFAULT

    # Build concatenated data & positions: [A@t, B@t] for each t
    map_A = dict(zip(times_A, data_A))
    map_B = dict(zip(times_B, data_B))

    concat_data = []
    concat_pos  = []
    concat_tags = []  # 'A' or 'B' per box, to assign colors reliably

    for t in all_times:
        if t in map_B and len(map_B[t]) > 0:
            concat_data.append(map_B[t])
            concat_pos.append(float(t))
            concat_tags.append('B')
        if t in map_A and len(map_A[t]) > 0:
            concat_data.append(map_A[t])
            concat_pos.append(float(t))
            concat_tags.append('A')


    # Draw ALL boxes in one call -> ensures identical centers for equal t
    bp = ax.boxplot(
        concat_data,
        positions=concat_pos,
        widths=BOX_WIDTH_DATA,
        patch_artist=True,
        manage_ticks=False,
        medianprops=dict(linewidth=lw_pt*MEDIAN_LW_SCALE),
        whiskerprops=dict(linewidth=lw_pt*WHISKER_CAP_SCALE),
        capprops=dict(linewidth=lw_pt*WHISKER_CAP_SCALE),
        flierprops=dict(
            marker='o',
            markersize=FLIER_SIZE_PT,
            linestyle='none',
        ),
        zorder=3
    )

    # Apply per-box styling based on tag (A or B)
    for i, (box, tag) in enumerate(zip(bp['boxes'], concat_tags)):
        if tag == 'A':
            box.set(facecolor=A_FACE, edgecolor=A_EDGE, linewidth=lw_pt*WHISKER_CAP_SCALE, alpha=A_ALPHA)
            bp['medians'][i].set(color=A_EDGE)
            bp['whiskers'][2*i].set(color=A_EDGE)      # each box has 2 whiskers
            bp['whiskers'][2*i+1].set(color=A_EDGE)
            bp['caps'][2*i].set(color=A_EDGE)          # and 2 caps
            bp['caps'][2*i+1].set(color=A_EDGE)
        else:
            box.set(facecolor=B_FACE, edgecolor=B_EDGE, linewidth=lw_pt*WHISKER_CAP_SCALE, alpha=B_ALPHA)
            bp['medians'][i].set(color=B_EDGE)
            bp['whiskers'][2*i].set(color=B_EDGE)
            bp['whiskers'][2*i+1].set(color=B_EDGE)
            bp['caps'][2*i].set(color=B_EDGE)
            bp['caps'][2*i+1].set(color=B_EDGE)

    # Outliers (fliers) come in order as well; set colors accordingly
    # Note: fliers length can vary; safest is to iterate and color by matching box tag index where possible.
    # Matplotlib groups fliers per box; bp['fliers'][i] is a Line2D for box i.
    for i, (fl, tag) in enumerate(zip(bp.get('fliers', []), concat_tags[:len(bp.get('fliers', []))])):
        if tag == 'A':
            fl.set(markerfacecolor=A_EDGE, markeredgecolor=A_EDGE)
        else:
            fl.set(markerfacecolor=B_EDGE, markeredgecolor=B_EDGE)

    # Labels, ticks, limits
    if title:
        ax.set_title(title, pad=4)
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Particles per Image")

    ax.set_xlim(-1, x_max + 1)
    ax.set_xticks(np.arange(0, x_max + 1, xtick_step))

    tick_set = set(ax.get_xticks())
    ax.set_xticks(sorted(tick_set))

    # Adopt the wider Y range
    y_max = max(y_max_A, y_max_B)
    ax.set_ylim(0, y_max)

    lw_pt = mm_to_pt(LINE_MM)

    legend_handles = [
        Patch(
            facecolor=A_FACE,
            edgecolor=A_EDGE,
            label=f"Loss = {loss_A}",
            alpha=A_ALPHA,
            linewidth=lw_pt * WHISKER_CAP_SCALE
        ),
        Patch(
            facecolor=B_FACE,
            edgecolor=B_EDGE,
            label=f"Loss = {loss_B}",
            alpha=B_ALPHA,
            linewidth=lw_pt * WHISKER_CAP_SCALE
        ),
    ]

    ax.legend(handles=legend_handles, frameon=False, loc='lower right')

    # Save
    out_path = Path(output_svg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    plt.close(fig)

# ---------------------- HOW TO CALL ----------------------
if __name__ == "__main__":
    DATA_FOLDER = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1B_hamming_time_square_counting\results"
    OUT_DIR     = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_5\Figure_5_more_data"

    # condition A
    condA = "H24"
    timesA, dataA, meansA, yMaxA = load_condition_counts(DATA_FOLDER, condA)
    lossA = 7.3  # <- set your actual value

    # condition B
    condB = "H29"
    timesB, dataB, meansB, yMaxB = load_condition_counts(DATA_FOLDER, condB)
    lossB = 2.6  # <- set your actual value

    plot_two_conditions_overlay_singlecall(
        condition_A=condA, times_A=timesA, data_A=dataA, y_max_A=yMaxA, loss_A=lossA,
        condition_B=condB, times_B=timesB, data_B=dataB, y_max_B=yMaxB, loss_B=lossB,
        output_svg=Path(OUT_DIR) / f"boxplot_{condA}_vs_{condB}.svg",
        title="Yield vs Time",
        x_max=109,                # or None to infer from data
        xtick_step=XTICK_STEP,
    )
