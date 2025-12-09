#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from scripts.paper_2025_figure_analysis.Fig_6.Sunflower_stage56_plot import mm_to_pt

# ----------------- paths -----------------
PKL_PATH = Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/Plots/hist_per_image.pkl")
OUT_DIR = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_6\resources")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_SVG  = OUT_DIR / "fraction_complete.svg"

# ----------------- config ----------------
# Loss for ordering (low → high). V3 excluded.
LOSS = {'V0': 3.60, 'V1': 2.76, 'V2': 3.77, 'V3': 3.77, 'V4': 5.11, 'V5': 4.69}
EXCLUDE = {'V3'}

# Exact group colors (by name)
GROUP_COLORS = {
    'V0': '#fb5a00',
    'V1': '#fb1c00',
    'V2': '#fb8f00',
    'V5': '#fbbc00',
    'V4': '#ffeb00',
}

# ----------------- mm helpers ------------
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ----------------- style -----------------
BOX_W_MM    = 88.0        # exact plot box width
BOX_H_MM    = 28.0        # adjust as needed
MARGIN_L_MM = 6.0         # margins do NOT count toward box size
MARGIN_R_MM = 4.0
MARGIN_B_MM = 7.0
MARGIN_T_MM = 5.0

LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_LEGEND   = 6
FONT_FAMILY = "Arial"
EDGE_COLOR  = "black"
PAD_INCHES  = 0.06

# Text stays text in SVG
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

    # Spine/ ticks
    for s in ax.spines.values():
        s.set_linewidth(lw_pt)
        s.set_edgecolor(EDGE_COLOR)
    ax.tick_params(which="both", direction="out",
                   length=tick_len_pt, width=lw_pt, colors=EDGE_COLOR)
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)

    # NEW: axis-title paddings (in points)
    ax.xaxis.labelpad = XLABEL_PAD_PT
    ax.yaxis.labelpad = YLABEL_PAD_PT

    return fig, ax, lw_pt

# ----------------- data ------------------
hist = pd.read_pickle(PKL_PATH)

# Ensure columns 1..6 exist
for c in (1,2,3,4,5,6):
    if c not in hist.columns:
        hist[c] = 0

# Normalize group labels robustly, then aggregate per group
df = hist.reset_index()
df['Group'] = (
    df['Group'].astype(str)
               .str.replace('\u00A0', ' ', regex=False)  # NBSP -> space
               .str.strip()
               .str.upper()
)
sum_by_group = df.groupby('Group')[[1,2,3,4,5,6]].sum()

# Select groups that exist, are in LOSS, not excluded; order by LOSS
groups_present = [g for g in sum_by_group.index if g in LOSS and g not in EXCLUDE]
groups = sorted(groups_present, key=lambda g: (LOSS[g], g))  # stable tie-break
groups = list(reversed(groups))


# Sanity: require color for every plotted group
missing = [g for g in groups if g not in GROUP_COLORS]
if missing:
    raise SystemExit(f"Missing colors for groups: {missing}")

# Relative frequencies for bins [1,2,3,4,5/6]
labels_bins = ["1","2","3","4","5/6"]
rel_by_group = {}
totals_by_group = {}
for g in groups:
    row    = sum_by_group.loc[g, [1,2,3,4,5,6]]
    c56    = int(row[5] + row[6])
    counts = [int(row[1]), int(row[2]), int(row[3]), int(row[4]), c56]
    total  = sum(counts)
    rel_by_group[g] = [0.0]*5 if total == 0 else [c/total for c in counts]
    totals_by_group[g] = int(row.sum())  # == sum(counts)





# ----------------- layout knobs ------------------


# Axis-label paddings (in points, affect only the "x/y axis titles")
XLABEL_PAD_PT = 2.0   # previously ~1.2
YLABEL_PAD_PT = 2.0

# "N=…" annotation styling
SHOW_TOTALS     = True
TOTALS_FS       = FS_LABELS   # font size for the N labels
TOTALS_Y_OFFSET = 0.03        # vertical offset above the top (y=1.0) in data units



LEFT_OFFSET   = 0.25   # whitespace from first bar-edge to left axis
RIGHT_OFFSET  = 0.25   # whitespace from last  bar-edge to right axis

BAR_W         = 0.2   # bar thickness (x units)
BAR_GAP       = 0.00   # gap between bars *inside* each cluster (x units)

OUTER_GAP     = 0.5   # <<< whitespace between the outer bars of adjacent clusters

SHOW_SEPARATORS   = True
SEPARATOR_ALPHA   = 0.25
SEPARATOR_LW_MULT = 1

XTICK_LABEL_PAD = 1.5
XTICK_ROTATION  = 0

# ----------------- plot ------------------
fig, ax, lw_pt = make_fig_ax()

n_groups  = len(groups)
n_bins    = len(labels_bins)

# Within-cluster geometry (depends ONLY on BAR_W and BAR_GAP)
intra_step = (BAR_W + BAR_GAP)
offsets    = (np.arange(n_bins) - (n_bins - 1)/2.0) * intra_step

# Half-span from cluster center to its outer bar edge
half_span  = np.max(np.abs(offsets)) + BAR_W/2.0

# Build cluster centers so that the gap between OUTER edges is OUTER_GAP
x_centers = np.zeros(n_groups, dtype=float)
for i in range(1, n_groups):
    # move from previous center to next center by: outer edge -> gap -> outer edge
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

# Optional thin gray separators halfway between cluster outer edges
if SHOW_SEPARATORS and n_groups > 1:
    for i in range(1, n_groups):
        # separator placed halfway between the two outer edges
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

# Edge margins only here:
left_lim  = x_centers[0]  - half_span - LEFT_OFFSET
right_lim = x_centers[-1] + half_span + RIGHT_OFFSET
ax.set_xlim(left_lim, right_lim)
ax.set_ylim(0, 1.0)

ax.set_ylabel("Relative Frequency")
ax.set_xlabel("Growth Stages")

ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels, rotation=XTICK_ROTATION)
ax.tick_params(axis='x', pad=XTICK_LABEL_PAD)


# ---- Total counts N inside the plot ----
if SHOW_TOTALS:
    N_Y = 0.79  # vertical position inside plot (0 = bottom, 1 = top)
    for i, g in enumerate(groups):
        ax.text(
            x_centers[i]+0.07,
            N_Y,                       # SAME exact baseline for every group
            f"N\u202F=\u202F{totals_by_group[g]}",
            ha="center", va="bottom",
            fontsize=FS_TICKS,        # same size as labels
            fontfamily="Arial",        # enforce Arial
            color="black",
            clip_on=False              # show even if close to border
        )


# ----------------- save ------------------
fig.savefig(OUT_SVG, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
plt.close(fig)
print("Order:", groups)
print(f"Saved: {OUT_SVG}")




