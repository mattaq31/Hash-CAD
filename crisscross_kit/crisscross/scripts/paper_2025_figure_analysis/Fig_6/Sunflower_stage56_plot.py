#!/usr/bin/env python3
# Boxplot: per-image (5+6) counts positioned by LOSS (numeric x-axis 2.5–5.5).
# Median in black. Optional per-group box face colors.

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib as mpl
import pickle

filename = "scores_random.pkl"
filename32 = "scores_random_reduced32.pkl"

with open(filename, "rb") as f:
    score_array = pickle.load(f)

# Load second dataset
with open(filename32, "rb") as f:
    score_array32 = pickle.load(f)

min_rand_Loss= score_array.min()
min_rand_Loss32= score_array32.min()


# ====== SVG settings ======
mpl.rcParams['svg.fonttype'] = 'none'
mpl.rcParams['svg.hashsalt'] = ''

# ====== paths ======
PKL_PATH = Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/Plots/hist_per_image.pkl")
OUT_DIR = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6\resources")
OUT_DIR.mkdir(parents=True, exist_ok=True)



# ====== Loss map ======


# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== Global style knobs (consistent with your latest first script) ======
BOX_W_MM    = 51
BOX_H_MM    = 28
LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_TITLE    = 6
FS_LEGEND   = 6
FONT_FAMILY = "Arial"
MARGIN_L_MM = 5.0
MARGIN_R_MM = 6.0
MARGIN_B_MM = 5.0
MARGIN_T_MM = 6.0
PAD_INCHES  = 0.07

# ====== Colors / markers ======
BOX_WIDTH_DATA  = 0.16
BOX_COLOR       = "lightblue"   # fallback if a group isn't in GROUP_COLORS
EDGE_COLOR      = "black"
MEDIAN_COLOR    = "black"       # median now black
FLIER_COLOR     = "black"
FLIER_SIZE_PT   = 0.6           # outlier dot diameter (points)

# Optional: per-group face colors (fill your real colors here)
GROUP_COLORS = {
    'V0': '#fb5a00',  # dummy
    'V1': '#fb1c00',  # dummy
    'V2': '#fb8f00',  # dummy
    # 'V3': '#d62728',  # excluded anyway
    'V4': '#ffeb00',  # dummy
    'V5': '#fbbc00',  # dummy
}

loss_map = {
    'V0': 3.60,
    'V1': 2.76,
    'V2': 3.77,
    'V3': 3.77,  # excluded
    'V4': 5.11,
    'V5': 4.69,
}

# ====== Figure factory ======
def make_fig_ax(box_w_mm, box_h_mm):
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
    ax     = fig.add_axes([left, bottom, ax_w, ax_h])

    for s in ax.spines.values():
        s.set_linewidth(lw_pt)
        s.set_edgecolor(EDGE_COLOR)

    ax.tick_params(which="both", direction="out", length=tick_len_pt, width=lw_pt, colors=EDGE_COLOR)
    ax.xaxis.labelpad = 0.5
    ax.yaxis.labelpad = 0.5
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)

    return fig, ax, lw_pt

# ====== Load and prepare data ======
hist_per_image = pd.read_pickle(PKL_PATH)
for c in [5, 6]:
    if c not in hist_per_image.columns:
        hist_per_image[c] = 0

five_six = hist_per_image[[5, 6]].sum(axis=1)
present_groups = set(hist_per_image.index.get_level_values('Group'))
groups = sorted((present_groups & set(loss_map.keys())) - {'V3'})

x_positions = [loss_map[g] for g in groups]
data        = [five_six.xs(g, level='Group').values for g in groups]

# ====== Plot ======
fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)



bp = ax.boxplot(
    data,
    positions=x_positions,
    widths=BOX_WIDTH_DATA,
    patch_artist=True,
    manage_ticks=False,
    flierprops=dict(
        marker='o',
        markersize=FLIER_SIZE_PT,
        color=FLIER_COLOR,
        markerfacecolor=FLIER_COLOR,
        markeredgecolor=FLIER_COLOR,
        linestyle='none'
    ),
)

# style boxes/lines
for box, g in zip(bp['boxes'], groups):
    fill = GROUP_COLORS.get(g, BOX_COLOR)
    box.set(facecolor=fill, linewidth=lw_pt, edgecolor=EDGE_COLOR)

for w in bp['whiskers']:
    w.set(linewidth=lw_pt, color=EDGE_COLOR)
for c in bp['caps']:
    c.set(linewidth=lw_pt, color=EDGE_COLOR)
for m in bp['medians']:
    m.set(color=MEDIAN_COLOR, linewidth=lw_pt)

# No mean markers (removed)

# Axis labels & limits
ax.set_xlabel("Loss")
ax.set_ylabel("Structures per Image")
ax.set_xlim(2.4, 5.6)
ax.set_xticks(np.arange(2.5, 5.6, 0.5))
ax.set_ylim(-3, 95)

# Add gray shaded region starting at Loss = 4.2
ax.axvspan(min_rand_Loss, ax.get_xlim()[1], color='black', alpha=0.17, zorder=0)
ax.axvspan(min_rand_Loss32, ax.get_xlim()[1], color='black', alpha=0.17, zorder=0)
# Legend (only median; optional — comment out if not needed)
#median_proxy = Line2D([], [], color=MEDIAN_COLOR, linewidth=lw_pt, label='Median')
#ax.legend([median_proxy], ["Median"], frameon=False, loc='best')

# Save
out_svg = OUT_DIR / "boxplot_5plus6_vs_loss_numeric.svg"
fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
plt.close(fig)
print(f"Saved: {out_svg}")
