import pickle as pkl
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- mm helpers (same idea as your other script) ----------
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ---------- style knobs borrowed from the other plot ----------
BOX_W_MM    = 51.0
BOX_H_MM    = 28.0
MARGIN_L_MM = 6.0
MARGIN_R_MM = 4.0
MARGIN_B_MM = 7.0
MARGIN_T_MM = 5.0
TITLE_PAD_PT = 3.5
LINE_MM     = 0.20
TICK_LEN_MM = 0.40
FS_TICKS    = 5
FS_LABELS   = 6
FS_LEGEND   = 6
FS_TITLE    = 6
FONT_FAMILY = "Arial"
EDGE_COLOR  = "black"
PAD_INCHES  = 0.06

import matplotlib as mpl
# Keep text as text in SVG (harmless for PNG too)
mpl.rcParams['svg.fonttype'] = 'none'
mpl.rcParams['svg.hashsalt'] = ''

def make_fig_ax():
    lw_pt       = mm_to_pt(LINE_MM)
    tick_len_pt = mm_to_pt(TICK_LEN_MM)

    plt.rcParams.update({
        "font.family":     FONT_FAMILY,
        "axes.linewidth":  lw_pt,
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

    # Spines + tick styling
    for s in ax.spines.values():
        s.set_linewidth(lw_pt)
        s.set_edgecolor(EDGE_COLOR)
    ax.tick_params(which="both", direction="out",
                   length=tick_len_pt, width=lw_pt, colors=EDGE_COLOR)
    ax.tick_params(axis="x", pad=1.2)
    ax.tick_params(axis="y", pad=1.2)

    return fig, ax, lw_pt

def _snap_to_bin_left(val, edges):
    i = np.searchsorted(edges, val, side="right") - 1
    i = max(0, min(i, len(edges)-2))
    return edges[i]

def _snap_to_bin_right(val, edges):
    j = np.searchsorted(edges, val, side="left")
    j = max(1, min(j, len(edges)-1))
    return edges[j]

def plot_histograms(on_data, off_data, x_range, ymax, bin_edges, save_path, title="hier könnte ihr titel stehen",
                    add_guides=False, on_color=None, off_color=None):
    fig, ax, lw_pt = make_fig_ax()

    if on_color is None:  on_color  = "#4C78A8"  # blue
    if off_color is None: off_color = "#ca0a56"  # orange

    # --- Bars ---
    ax.hist(on_data, bins=bin_edges, range=x_range, density=True,
            alpha=1, label="On-target", edgecolor="black",
            linewidth=lw_pt, color=on_color)
    ax.hist(off_data, bins=bin_edges, range=x_range, density=True,
            alpha=1, label="Off-target", edgecolor="black",
            linewidth=lw_pt, color=off_color)

    # --- Guide lines (only for NEW figure) ---
    if add_guides and len(on_data) > 0 and len(off_data) > 0:
        on_min = float(np.min(on_data))
        on_max = float(np.max(on_data))
        off_min = float(np.min(off_data))

        on_min_x = _snap_to_bin_left(on_min, bin_edges)
        on_max_x = _snap_to_bin_right(on_max, bin_edges)
        off_min_x = _snap_to_bin_left(off_min, bin_edges)

        # On-target range (two lines but one legend handle)
        ax.axvline(on_min_x, color=on_color, linewidth=lw_pt * 1.2,
                   zorder=0)  # behind bars
        ax.axvline(on_max_x, color=on_color, linewidth=lw_pt * 1.2,
                   label="On-target range", zorder=0)

        # Off-target cutoff (single line)
        ax.axvline(off_min_x, color=off_color, linewidth=lw_pt * 1.2,
                   label="Off-target cutoff", zorder=0)
    ax.set_xlim(x_range)
    ax.set_ylim(0, ymax)
    ax.set_xlabel("ΔG (kcal/mol)", labelpad=1)
    ax.set_ylabel("Probability density", labelpad=1)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title(title, fontsize=FS_TITLE, pad=TITLE_PAD_PT)

    save_path = save_path.with_suffix(".svg")
    fig.savefig(save_path, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    plt.close(fig)
    print(f"Saved: {save_path}")





def give_array_back(off_e_new):
    ah_ah = off_e_new['antihandle_antihandle_energies']
    ah_h  = off_e_new['antihandle_handle_energies']
    h_h   = off_e_new['handle_handle_energies']
    combined = np.concatenate([ah_ah.ravel(), ah_h.ravel(), h_h.ravel()])
    return combined[combined != 0]

def flatten_nonzero(x):
    x = np.asarray(x).ravel()
    return x[x != 0]



if __name__ == "__main__":

    path = 'C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/Figures/Figure_7/data/energies_handles/'

    # load new
    on_e_new = pkl.load(open(path + 'on_e_new64.pkl', "rb"))
    off_e_new = give_array_back(pkl.load(open(path + 'off_e_new64.pkl', "rb")))

    # load old
    on_e_old = pkl.load(open(path + 'on_e_old32.pkl', "rb"))
    off_e_old = give_array_back(pkl.load(open(path + 'off_e_old32.pkl', "rb")))

    # prepare flattened nonzero
    on_new = flatten_nonzero(on_e_new)
    off_new = off_e_new
    on_old = flatten_nonzero(on_e_old)
    off_old = off_e_old

    # shared x-range
    NBINS = 50
    xmin, xmax = -10.75, -3.00
    x_range = (xmin, xmax)

    # fixed identical bin edges for ALL histograms
    BIN_EDGES = np.linspace(xmin, xmax, NBINS + 1)

    # ---- styled plots (same basenames; saved as .svg) ----
    ymax = 2.4
    plot_histograms(on_new, off_new, x_range, ymax, BIN_EDGES,
                    Path(path) / "hist_new_on_off.png", title = "64 New Handle/Anti-Handle Pairs",
                    add_guides=True)  # <-- guides only here

    ymax = 1.5
    plot_histograms(on_old, off_old, x_range, ymax, BIN_EDGES,
                    Path(path) / "hist_old_on_off.png",title = "32 Old Handle/Anti-Handle Pairs",
                    add_guides=True)