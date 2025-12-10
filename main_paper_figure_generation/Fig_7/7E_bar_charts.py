#!/usr/bin/env python3
# Boxplot: per-image (5+6) counts for V1, V2, V3 on a categorical x-axis.
# Median in black. No shaded regions, no numeric loss axis.

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib as mpl

# ====== SVG settings ======
mpl.rcParams['svg.fonttype'] = 'none'
mpl.rcParams['svg.hashsalt'] = ''

# ====== paths ======
# this data comes from the Fig_6 folder
PKL_PATH = Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/Plots/hist_per_image.pkl")
OUT_DIR = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_7\resources")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== Global style knobs ======
BOX_W_MM    = 28.0           # <- narrower inner plot width
BOX_H_MM    = 28.0
LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_TITLE    = 6
FS_LEGEND   = 6
FONT_FAMILY = "Arial"
MARGIN_L_MM = 6.0
MARGIN_R_MM = 6.0
MARGIN_B_MM = 6.0
MARGIN_T_MM = 7.0            # bit of headroom for title
PAD_INCHES  = 0.07

# ====== Colors / markers ======
BOX_WIDTH_CAT  = 0.3        # width in categorical units (0–1 spacing)
EDGE_COLOR     = "black"
MEDIAN_COLOR   = "black"
FLIER_COLOR    = "black"
FLIER_SIZE_PT  = 0.6

GROUP_COLORS = {
    "V1": "#fb1c00",  # new 64
    "V2": "#fb8f00",  # new 32
    "V3": "#4caf50",  # old 32 (green)
}

# Categorical order (left -> right) and their x labels
GROUPS_ORDER   = ["V3", "V2", "V1"]              # old 32, new 32, new 64
X_LABELS       = ["old 32", "new 32", "new 64"]  # shown on x-axis

def make_fig_ax(box_w_mm, box_h_mm):
    lw_pt       = mm_to_pt(LINE_MM)
    tick_len_pt = mm_to_pt(TICK_LEN_MM)

    plt.rcParams.update({
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

    ax.tick_params(which="both", direction="out",
                   length=tick_len_pt, width=lw_pt, colors=EDGE_COLOR)
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)

    return fig, ax, lw_pt

# ====== Load and prepare data ======
hist = pd.read_pickle(PKL_PATH)
for c in (5, 6):
    if c not in hist.columns:
        hist[c] = 0

# Normalize group labels to be safe
df = hist.reset_index()
df['Group'] = (
    df['Group'].astype(str)
               .str.replace('\u00A0', ' ', regex=False)
               .str.strip()
               .str.upper()
)

# Per-image stage 5+6 counts
five_six = df[[5, 6]].sum(axis=1)

# Build data arrays in the requested categorical order (skip missing groups)
present = set(df['Group'].unique())
groups  = [g for g in GROUPS_ORDER if g in present]
labels  = [X_LABELS[GROUPS_ORDER.index(g)] for g in groups]
positions = np.arange(len(groups), dtype=float)

data = []
for g in groups:
    vals = five_six[df['Group'] == g].values
    data.append(vals)

# ====== Plot ======
fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

bp = ax.boxplot(
    data,
    positions=positions,
    widths=BOX_WIDTH_CAT,
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

# Style boxes & lines
for box, g in zip(bp['boxes'], groups):
    box.set(facecolor=GROUP_COLORS.get(g, "white"),
            linewidth=lw_pt, edgecolor=EDGE_COLOR)
for w in bp['whiskers']:
    w.set(linewidth=lw_pt, color=EDGE_COLOR)
for c in bp['caps']:
    c.set(linewidth=lw_pt, color=EDGE_COLOR)
for m in bp['medians']:
    m.set(color=MEDIAN_COLOR, linewidth=lw_pt)

# Axes: categorical x, numeric y
ax.set_xticks(positions)
ax.set_xlim(-0.55, len(groups)-1 + 0.55)
ax.set_xticklabels(labels)
ax.set_xlabel("")  # no numeric x-label
ax.set_ylabel("Structures per Image")

# Reasonable y-limits (keep your previous headroom)
ax.set_ylim(-3, 95)

# Title (top)
ax.set_title("Completed Structure (Stage 5/6)", fontsize=FS_TITLE, pad=3.5, y=1.02)

# Save
out_svg = OUT_DIR / "boxplot_stage56_by_label.svg"
fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
plt.close(fig)
print(f"Saved: {out_svg}")
