#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ----------------- paths -----------------
# this data comes from the Fig_6 folder
PKL_PATH = Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/Plots/hist_per_image.pkl")
OUT_DIR = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_7\resources")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_SVG  = OUT_DIR / "fraction_complete_oldnew.svg"

# ----------------- config ----------------
GROUPS_WANTED = ["V3", "V2", "V1"]  # <-- ensures left→right clusters: V3, V2, V1

GROUP_COLORS = {
    "V1": "#fb1c00",
    "V2": "#fb8f00",
    "V3": "#4caf50",   # green kept
}

# Cluster labels (V3 label intentionally removed)
CLUSTER_LABELS = {
    "V1": "",
    "V2": "",
    "V3": "",          # ← no label for old 32
}

# ----------------- mm helpers ------------
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ----------------- style -----------------
BASE_BOX_W_MM = 88.0
N_BASE = 5
N_TARGET = len(GROUPS_WANTED)
BOX_W_MM    = BASE_BOX_W_MM * (N_TARGET / N_BASE)

BOX_H_MM    = 28.0
MARGIN_L_MM = 6.0
MARGIN_R_MM = 4.0
MARGIN_B_MM = 7.0
MARGIN_T_MM = 5.0  # increase if you add a long title later

LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_LEGEND   = 6
FONT_FAMILY = "Arial"
EDGE_COLOR  = "black"
PAD_INCHES  = 0.06

# Axis-label paddings (in points)
XLABEL_PAD_PT = 2.0
YLABEL_PAD_PT = 2.0

FS_TITLE = 6

# Optional title padding (only used if you call ax.set_title)
TITLE_PAD_PT = 3.5

# Totals label styling
SHOW_TOTALS     = True
TOTALS_FS       = FS_LABELS
TOTALS_Y_OFFSET = 0.03

LEFT_OFFSET   = 0.25
RIGHT_OFFSET  = 0.25

BAR_W         = 0.20
BAR_GAP       = 0.00
OUTER_GAP     = 0.50

SHOW_SEPARATORS   = True
SEPARATOR_ALPHA   = 0.25
SEPARATOR_LW_MULT = 1

XTICK_LABEL_PAD = 1.5
XTICK_ROTATION  = 0

mpl.rcParams['svg.fonttype'] = 'none'
mpl.rcParams['svg.hashsalt'] = ''

def make_fig_ax():
    lw_pt       = mm_to_pt(LINE_MM)
    tick_len_pt = mm_to_pt(TICK_LEN_MM)

    plt.rcParams.update({
        "font.family":  FONT_FAMILY,
        "axes.linewidth": lw_pt,
        "lines.linewidth": lw_pt,
        "xtick.labelsize": FS_TICKS,
        "ytick.labelsize": FS_TICKS,
        "axes.labelsize":  FS_LABELS,
        "legend.fontsize": FS_LEGEND,
    })

    fig_w_mm = BOX_W_MM + MARGIN_L_MM + MARGIN_R_MM
    fig_h_mm = BOX_H_MM + MARGIN_T_MM + MARGIN_B_MM
    fig = plt.figure(figsize=(mm_to_in(fig_w_mm), mm_to_in(fig_h_mm)))

    left   = MARGIN_L_MM / fig_w_mm
    bottom = MARGIN_B_MM / fig_h_mm
    ax_w   = BOX_W_MM / fig_w_mm
    ax_h   = BOX_H_MM / fig_h_mm
    ax     = fig.add_axes([left, bottom, ax_w, ax_h])

    for s in ax.spines.values():
        s.set_linewidth(lw_pt)
        s.set_edgecolor(EDGE_COLOR)
    ax.tick_params(which="both", direction="out",
                   length=tick_len_pt, width=lw_pt, colors=EDGE_COLOR)
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)

    ax.xaxis.labelpad = XLABEL_PAD_PT
    ax.yaxis.labelpad = YLABEL_PAD_PT

    # If you want a (top) title, uncomment:
    # ax.set_title("Fraction complete", fontsize=FS_LABELS, pad=TITLE_PAD_PT)

    return fig, ax, lw_pt

# ----------------- data ------------------
hist = pd.read_pickle(PKL_PATH)

for c in (1,2,3,4,5,6):
    if c not in hist.columns:
        hist[c] = 0

df = hist.reset_index()
df['Group'] = (
    df['Group'].astype(str)
               .str.replace('\u00A0', ' ', regex=False)
               .str.strip()
               .str.upper()
)
sum_by_group = df.groupby('Group')[[1,2,3,4,5,6]].sum()

groups = [g for g in GROUPS_WANTED if g in sum_by_group.index]

missing_colors = [g for g in groups if g not in GROUP_COLORS]
missing_labels = [g for g in groups if g not in CLUSTER_LABELS]
if missing_colors:
    raise SystemExit(f"Missing colors for groups: {missing_colors}")
if missing_labels:
    raise SystemExit(f"Missing cluster labels for groups: {missing_labels}")

labels_bins = ["1", "2", "3", "4", "5/6"]
rel_by_group = {}
totals_by_group = {}
for g in groups:
    row    = sum_by_group.loc[g, [1,2,3,4,5,6]]
    c56    = int(row[5] + row[6])
    counts = [int(row[1]), int(row[2]), int(row[3]), int(row[4]), c56]
    total  = sum(counts)
    rel_by_group[g]    = [0.0]*5 if total == 0 else [c/total for c in counts]
    totals_by_group[g] = int(row.sum())

# ----------------- plot ------------------
fig, ax, lw_pt = make_fig_ax()

n_groups  = len(groups)
n_bins    = len(labels_bins)

intra_step = (BAR_W + BAR_GAP)
offsets    = (np.arange(n_bins) - (n_bins - 1)/2.0) * intra_step
half_span  = np.max(np.abs(offsets)) + BAR_W/2.0

x_centers = np.zeros(n_groups, dtype=float)
for i in range(1, n_groups):
    x_centers[i] = x_centers[i-1] + (2 * half_span) + OUTER_GAP

xticks = []
xticklabels = []

for i, g in enumerate(groups):
    x_pos  = x_centers[i] + offsets
    yvals  = rel_by_group[g]
    hexcol = GROUP_COLORS[g]

    bars = ax.bar(
        x_pos, yvals,
        width=BAR_W,
        edgecolor=EDGE_COLOR,
        linewidth=lw_pt,
        color=hexcol,
        align='center'
    )
    for j, p in enumerate(bars):
        p.set_gid(f"bar_{g}_{labels_bins[j].replace('/', '-')}")
    xticks.extend(x_pos.tolist())
    xticklabels.extend(labels_bins)

if SHOW_SEPARATORS and n_groups > 1:
    for i in range(1, n_groups):
        left_outer  = x_centers[i-1] + half_span
        right_outer = x_centers[i]   - half_span
        sep_x = 0.5 * (left_outer + right_outer)
        ax.axvline(
            sep_x, ymin=0, ymax=1,
            color=EDGE_COLOR,
            linewidth=lw_pt * SEPARATOR_LW_MULT,
            alpha=SEPARATOR_ALPHA,
            zorder=0
        )

left_lim  = x_centers[0]  - half_span - LEFT_OFFSET
right_lim = x_centers[-1] + half_span + RIGHT_OFFSET
ax.set_xlim(left_lim, right_lim)
ax.set_ylim(0, 1.0)

ax.set_ylabel("Relative Frequency")
ax.set_xlabel("Growth Stages")

ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels, rotation=XTICK_ROTATION)
ax.tick_params(axis='x', pad=XTICK_LABEL_PAD)

ax.set_title("Growth Stage Distribution per Handle Assignment ", fontsize=FS_TITLE, pad=TITLE_PAD_PT)


# ---- Cluster labels (skip empties) ----
for i, g in enumerate(groups):
    label = CLUSTER_LABELS[g]
    if label:  # ← V3 is "", so nothing is drawn
        ax.text(
            x_centers[i], -0.10,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center", va="top",
            fontsize=FS_LABELS,
            fontfamily="Arial",
            color="black",
            clip_on=False
        )

# ---- Total counts N inside the plot ----
if SHOW_TOTALS:
    N_Y = 0.79
    for i, g in enumerate(groups):
        ax.text(
            x_centers[i] + 0.07, N_Y,
            f"N\u202F=\u202F{totals_by_group[g]}",
            ha="center", va="bottom",
            fontsize=FS_TICKS,
            fontfamily="Arial",
            color="black",
            clip_on=False
        )

# ----------------- save ------------------
fig.savefig(OUT_SVG, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
plt.close(fig)
print("Order:", groups)
print(f"Saved: {OUT_SVG}")
