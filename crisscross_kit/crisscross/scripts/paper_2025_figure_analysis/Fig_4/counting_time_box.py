# ====== imports ======
import os, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

# ====== mm helpers ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

# ====== style knobs (your updated values) ======
BOX_W_MM    = 75   # scaled up
BOX_H_MM    = 36.0   # scaled up

LINE_MM     = 0.20   # keep line widths unchanged
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
mean_size = 1.0
MEDIAN_COLOR     = "black"
MEAN_COLOR       = "#9f241a"

def make_fig_ax(box_w_mm=BOX_W_MM, box_h_mm=BOX_H_MM):
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

# ---------- plotting for ONE condition (no loop) ----------
def plot_time_boxplot_for_condition(
    condition,
    times_sorted,
    data,
    means,
    y_max,
    output_svg,
    *,
    x_max=120,
    xtick_step=10,
    box_width_data=2.0,
    title=None,
):
    """
    Make a single boxplot figure for one condition, styled like your other figures.
    """
    fig, ax, lw_pt = make_fig_ax(BOX_W_MM, BOX_H_MM)

    bp = ax.boxplot(
        data,
        positions=times_sorted,
        widths=box_width_data,     # wider boxes (data units)
        patch_artist=True,
        manage_ticks=False,
        flierprops=dict(
            marker='o',
            markersize=1.0,
            color='black',
            markerfacecolor='black',
            markeredgecolor='black',
            linestyle='none',
        ),
    )

    for b in bp['boxes']:     b.set(facecolor='lightblue', linewidth=lw_pt)
    for w in bp['whiskers']:  w.set(linewidth=lw_pt)
    for c in bp['caps']:      c.set(linewidth=lw_pt)
    for m in bp['medians']:   m.set(color='black', linewidth=lw_pt)


    # identical mean marker size everywhere

    #ax.scatter(times_sorted, means, color=MEAN_COLOR, marker='s', s=mean_size, zorder=3, label='Mean')
    '''
    ax.plot(
        times_sorted,
        means,
        linestyle='none',
        marker='s',                 # square
        markersize=mean_size,  # size scaled from area
        markerfacecolor=MEAN_COLOR,
        markeredgecolor=MEAN_COLOR,
        zorder=4
    )
    '''
    # labels, ticks, limits
    if title:
        ax.set_title(title, pad=4)
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Particles per Image")

    ax.set_xlim(-1, x_max + 1)
    ax.set_xticks(np.arange(0, x_max + 1, xtick_step))
    ax.set_ylim(0, y_max)

    # Legend in lower-right, including Outliers
    median_line = Line2D([], [], color='green', linewidth=lw_pt, label='Median')
    mean_proxy  = Line2D([], [], color=MEAN_COLOR, marker='s', linestyle='none',
                         markersize=math.sqrt(mean_size), label='Mean')
    '''
    ax.legend([median_line, mean_proxy],
              ["Median", "Mean"],
              frameon=False, loc='lower right')
    '''
    # Save
    out_path = Path(output_svg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    plt.close(fig)

# ---------------------- HOW TO CALL (two explicit plots) ----------------------
if __name__ == "__main__":
    DATA_FOLDER = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1B_hamming_time_square_counting\results"
    OUT_DIR     = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_4_timedata\resources"

    # 1) Square
    cond = "H24"  # <- set the condition string that matches your filenames (e.g., "H24")
    times, data, means, y_max = load_condition_counts(DATA_FOLDER, cond)
    plot_time_boxplot_for_condition(
        cond, times, data, means, y_max,
        output_svg=Path(OUT_DIR) / f"boxplot_{cond}.svg",
        x_max=110,
        xtick_step=10,
        box_width_data=2.5,
        title=f"Yield vs Time at Loss = 7.3",
    )

    # 2) Bird (example; change condition token accordingly)
    cond = "H29"  # another condition ID
    times, data, means, y_max = load_condition_counts(DATA_FOLDER, cond)
    plot_time_boxplot_for_condition(
        cond, times, data, means, y_max,
        output_svg=Path(OUT_DIR) / f"boxplot_{cond}.svg",
        x_max=110,
        xtick_step=10,
        box_width_data=2.5,
        title=f"Yield vs Time at Loss = 2.6 ",
    )
