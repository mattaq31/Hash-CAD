# ====== imports ======
from pathlib import Path
import os
import csv
import re
import numpy as np
import matplotlib.pyplot as plt

# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== global style knobs (from your file) ======
BOX_W_MM    = 38.0   # <- use these exact values
BOX_H_MM    = 22.0

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
    ax.tick_params(axis="x", pad=1.7)
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

def find_match_columns(header, start_match=1, end_match=4):
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

# ====== plotting ======
def plot_loglog_matches_vs_index(data, header, start_match=1, end_match=4,
                                 title="Match counts vs row index (log–log)",
                                 output_svg=None):
    """
    Make a log–log plot of selected “k Matches” columns vs (row index + 1),
    styled using your make_fig_ax() and sizing constants.
    """
    sel = find_match_columns(header, start_match, end_match)
    if not sel:
        raise ValueError("No requested match columns found in header.")

    n = data.shape[0]
    x = np.arange(n, dtype=float) + 1.0  # +1 to avoid log(0) on x

    fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

    for name, idx, k in sel:
        y = data[:, idx].astype(float)
        # treat non-positive as NaN to avoid -inf on log scale
        y = np.where(y <= 0, np.nan, y)
        ax.loglog(x, y, label=f"Valency = {k}")
    ax.minorticks_off()

    ax.set_xlabel("Row index + 1")
    ax.set_ylabel("Counts")
    ax.set_title(title, pad=6)
    ax.legend(frameon=False, loc='best')
    ax.grid(False)

    if output_svg:
        out_path = Path(output_svg)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    return fig, ax

# ====== run ======
if __name__ == "__main__":
    CSV_PATH = r"C:\Users\Flori\Dropbox\CrissCross\Crisscross Designs\CB015_3d_cube\evolution_runs\corner_v1\match_histograms.csv"
    OUT_SVG  = r"C:\Users\Flori\Dropbox\CrissCross\Crisscross Designs\CB015_3d_cube\evolution_runs\corner_v1\match_loglog.svg"

    data, header = load_match_histogram(CSV_PATH)
    fig, ax = plot_loglog_matches_vs_index(
        data,
        header,
        start_match=1,
        end_match=4,
        title="Match counts vs row index (log–log)",
        output_svg=OUT_SVG
    )
    plt.show()
