#!/usr/bin/env python3
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Paths =========
XLSX_PATH = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_7\data\counting_results\SW119_data_python_input.xlsx")
OUT_DIR   = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_7\resources")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========= SVG output settings (keep text editable) =========
mpl.rcParams['svg.fonttype'] = 'none'
mpl.rcParams['svg.hashsalt'] = ''

# ========= Simple units/helpers =========
def mm_to_in(mm): return mm / 25.4                # millimeters → inches (for figure size)
def mm_to_pt(mm): return (mm / 25.4) * 72.0       # millimeters → points (for line widths)

# ========= STYLE (plain-English knobs you’ll likely tweak) =========
FONT_FAMILY   = "Arial"   # font throughout
LINE_MM       = 0.20      # thickness of axis and box lines (in mm)
TICK_LEN_MM   = 0.40      # length of tick marks (in mm)
FS_TICKS      = 5         # font size for axis numbers
FS_LABELS     = 6         # font size for axis labels/headers
EDGE_COLOR    = "black"   # color for axes/box lines

# Size of the actual drawing area inside each small panel
BOX_W_MM, BOX_H_MM = 19.0, 18.0   # ← inner plot width, height (was 17; now 21 mm tall)

# Extra spaces around each small panel (to make room for ticks/labels)
LEFT_SPACE_MM   = 0.3    # space on the left side inside a cell (for y tick numbers)
RIGHT_SPACE_MM  = 0.3   # space on the right side inside a cell
BOTTOM_SPACE_MM = 0.3    # space below the inner plot (for x tick numbers on bottom row)
TOP_SPACE_MM    = 0.3    # space above the inner plot

# White edge around the exported SVG
PAD_INCHES  = 0.06

# Outer frame space around the whole multi-panel figure
OUTER_MM    = 1.0

# Gaps between the small panels (inside the figure grid)
H_GAP_MM = 1.0           # gap between left and right columns
V_GAP_MM = 1.0           # gap between rows

# Column header band at the very top for “new” / “old”
TOP_HEADER_H_MM  = 5.0

# Vertical band at the far left for row labels “[MgCl₂] = … mM”
ROW_LABEL_BAND_MM = 9.0

# Colors for the two ages
AGE_COLOR = {"new": "#fb8f00", "old": "#4caf50"}

# ========= Matplotlib rc derived from style =========
lw_pt       = mm_to_pt(LINE_MM)
tick_len_pt = mm_to_pt(TICK_LEN_MM)
plt.rcParams.update({
    "font.family":     FONT_FAMILY,
    "axes.linewidth":  lw_pt,
    "lines.linewidth": lw_pt,
    "xtick.labelsize": FS_TICKS,
    "ytick.labelsize": FS_TICKS,
    "axes.labelsize":  FS_LABELS,
})

# ========= Load & reshape (keep raw strings first) =========
sheets = pd.read_excel(
    XLSX_PATH, sheet_name=None, header=None, dtype=str, engine="openpyxl"
)

rows = []
for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    m = re.match(r"(new|old)\s*(\d+h)", sheet_name.lower())
    if not m:
        continue
    age, time_label = m.groups()  # e.g., "new", "2h"

    # Second row (index 1) has Mg headers; first col is "Structure ID"
    mg_headers = df.iloc[1].tolist()
    df_data = df.iloc[2:].reset_index(drop=True)
    df_data.columns = mg_headers
    df_data.rename(columns={mg_headers[0]: "Structure ID"}, inplace=True)

    # Melt to long
    long = df_data.melt(id_vars=["Structure ID"], var_name="Mg", value_name="Count")
    long["Age"]  = age
    long["Time"] = time_label
    rows.append(long)

combined = pd.concat(rows, ignore_index=True).astype(str)

# ========= Clean: keep only rows where Count is an integer =========
mask = combined["Count"].str.match(r"^\d+$", na=False)
cleaned_combined_ = combined[mask].copy()
cleaned_combined_["Count"] = cleaned_combined_["Count"].astype(int)

# Convert "2h" → 2.0, etc. (keeps numeric x-axis)
def time_to_hours(t):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*h\s*$", str(t), flags=re.I)
    return float(m.group(1)) if m else np.nan

cleaned_combined_["Time_h"] = cleaned_combined_["Time"].map(time_to_hours)

# ========= Grid: 3 rows (Mg) × 2 columns (new/old) =========
MGS  = ["12.5", "15", "17.5"]
AGES = ["old", "new"]


# Size of one cell = inner plot + padding around it
cell_w = LEFT_SPACE_MM + BOX_W_MM + RIGHT_SPACE_MM
cell_h = BOTTOM_SPACE_MM + BOX_H_MM + TOP_SPACE_MM

# Total figure size (in mm)
fig_w_mm = OUTER_MM*2 + ROW_LABEL_BAND_MM + 2*cell_w + H_GAP_MM
fig_h_mm = OUTER_MM*2 + TOP_HEADER_H_MM + 3*cell_h + 2*V_GAP_MM

fig = plt.figure(figsize=(mm_to_in(fig_w_mm), mm_to_in(fig_h_mm)))

def mm_to_figx(mm): return mm / fig_w_mm
def mm_to_figy(mm): return mm / fig_h_mm

def add_axes_at(col, row):
    """
    Make one small axes whose INNER drawing area is exactly BOX_W_MM × BOX_H_MM.
    col: 0 (left/new) or 1 (right/old)
    row: 0 (top: 12.5 mM), 1 (middle: 15 mM), 2 (bottom: 17.5 mM)
    """
    left_mm   = OUTER_MM + ROW_LABEL_BAND_MM + col*cell_w + col*H_GAP_MM + LEFT_SPACE_MM
    bottom_mm = OUTER_MM + TOP_HEADER_H_MM + (3-1-row)*cell_h + (3-1-row)*V_GAP_MM + BOTTOM_SPACE_MM

    ax = fig.add_axes([
        mm_to_figx(left_mm),
        mm_to_figy(bottom_mm),
        mm_to_figx(BOX_W_MM),
        mm_to_figy(BOX_H_MM),
    ])
    for s in ax.spines.values():
        s.set_linewidth(lw_pt)
        s.set_edgecolor(EDGE_COLOR)
    ax.tick_params(which="both", direction="out",
                   length=tick_len_pt, width=lw_pt, colors=EDGE_COLOR)
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)
    return ax

# ---- Column headers (“new”, “old”) centered above each column ----
col_centers_mm = [
    OUTER_MM + ROW_LABEL_BAND_MM + LEFT_SPACE_MM + BOX_W_MM/2.0,
    OUTER_MM + ROW_LABEL_BAND_MM + cell_w + H_GAP_MM + LEFT_SPACE_MM + BOX_W_MM/2.0,
]
header_y_mm = fig_h_mm - OUTER_MM + 2.5  # keep same positioning
for i, age in enumerate(AGES):
    label = "Old 32" if age == "old" else "New 32"   # ← changed text
    fig.text(mm_to_figx(col_centers_mm[i]), mm_to_figy(header_y_mm),
             label, ha="center", va="top", fontsize=FS_LABELS)

# ---- Row labels (“[MgCl₂] = … mM”) along the far left, centered per row ----
row_centers_mm = [
    OUTER_MM + TOP_HEADER_H_MM + BOTTOM_SPACE_MM + BOX_H_MM/2.0 + (2*cell_h + 2*V_GAP_MM),  # row 0 (top)
    OUTER_MM + TOP_HEADER_H_MM + BOTTOM_SPACE_MM + BOX_H_MM/2.0 + (1*cell_h + 1*V_GAP_MM),  # row 1
    OUTER_MM + TOP_HEADER_H_MM + BOTTOM_SPACE_MM + BOX_H_MM/2.0,                             # row 2 (bottom)
]
for r, mg in enumerate(MGS):
    fig.text(mm_to_figx(OUTER_MM + ROW_LABEL_BAND_MM - 6), mm_to_figy(row_centers_mm[r]),
             f"[MgCl$_2$] = {mg} mM",
             ha="right", va="center", rotation=90, fontsize=FS_LABELS)

# ========= Draw panels (fixed ranges, N labels) =========
for r, mg in enumerate(MGS):
    sub_row = cleaned_combined_.loc[cleaned_combined_["Mg"] == mg]

    for c, age in enumerate(AGES):
        ax = add_axes_at(c, r)
        sub = sub_row.loc[sub_row["Age"] == age]

        # Y label only on the left column
        if c == 0:
            ax.set_ylabel("Length")


        if c == 1:
            ax.set_yticklabels([])  # hide tick labels


        # X label only on the bottom row
        if r == len(MGS) - 1:
            ax.set_xlabel("Time (h)")

        # Fixed ranges for comparability
        ax.set_ylim(0, 46)   # y-range 0..49
        ax.set_xlim(0, 14)   # x-range 0..14

        if sub.empty:
            if r != len(MGS) - 1:
                ax.set_xticklabels([])
            continue

        # Build box data per time (real x-axis)
        times = np.sort(sub["Time_h"].dropna().unique())
        groups = [sub.loc[sub["Time_h"] == th, "Count"].to_numpy() for th in times]
        Ns     = [len(g) for g in groups]

        bp = ax.boxplot(
            groups,
            positions=times,
            widths=1.4,               # box width along x
            patch_artist=True,        # allow face color
            medianprops=dict(color=EDGE_COLOR, linewidth=lw_pt),
            boxprops=dict(color=EDGE_COLOR, linewidth=lw_pt),
            whiskerprops=dict(color=EDGE_COLOR, linewidth=lw_pt),
            capprops=dict(color=EDGE_COLOR, linewidth=lw_pt),
            flierprops=dict(marker='o', markersize=2.0,
                            markeredgewidth=0.0, markerfacecolor='none')
        )
        for box in bp['boxes']:
            box.set_facecolor(AGE_COLOR[age])

        # Ticks at the observed times; hide xticks except bottom row
        ax.yaxis.labelpad = 1.0
        ax.xaxis.labelpad = 1.0
        ax.set_xticks(times)
        ax.set_xticklabels([str(int(t)) if float(t).is_integer() else f"{t:g}" for t in times])
        if r != len(MGS) - 1:
            ax.set_xticklabels([])

        # N labels above each box (slightly below the top to avoid clipping)
        label_y = 42.0
        for x_pos, n in zip(times, Ns):
            ax.text(
                x_pos, label_y, f"N\u202F=\u202F{n}",   # thin spaces around '='
                ha="center", va="bottom",
                fontsize=FS_TICKS,
                clip_on=False
            )

# ---- Save ----
OUT_SVG = OUT_DIR / "box_counts_all_Mg_new_old.svg"
fig.savefig(OUT_SVG, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
plt.close(fig)
print(f"Saved: {OUT_SVG}")
