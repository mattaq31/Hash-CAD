#!/usr/bin/env python3
# -- clean, single-model (y = A*(tau - x)^beta), full-range eval, fast-fail --

from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext
from scipy.optimize import curve_fit

# ====== style ======
MM_PER_INCH = 25.4
def mm_to_in(mm): return mm / MM_PER_INCH
def mm_to_pt(mm): return (mm / MM_PER_INCH) * 72.0

BOX_W_MM     = 38.0
BOX_H_MM     = 22.0
LINE_MM_DATA = 0.33
LINE_MM      = 0.20
TICK_LEN_MM  = 0.40
FS_TICKS     = 5
FS_LABELS    = 6
FS_TITLE     = 6
FS_LEGEND    = 5
FONT_FAMILY  = "Arial"

MARGIN_L_MM = 5.0
MARGIN_R_MM = 6.0
MARGIN_B_MM = 5.0
MARGIN_T_MM = 6.0
PAD_INCHES  = 0.02

PALETTE = ["#004455", "#0088AA", "#00AAD4", "#55DDFF", "#AAEEFF",
           "#600700", "#9f241a", "#dc482e", "#f1968f", "#f4cac8",
           "#7f3c8d", "#11a579", "#3969ac", "#f2b701", "#e73f74"]

def make_fig_ax():
    lw_pt       = mm_to_pt(LINE_MM)
    tick_len_pt = mm_to_pt(TICK_LEN_MM)
    plt.rcParams.update({
        "svg.fonttype": "none",
        "font.family":  FONT_FAMILY,
        "axes.linewidth": lw_pt,
        "lines.linewidth": lw_pt,
        "xtick.labelsize": FS_TICKS,
        "ytick.labelsize": FS_TICKS,
        "legend.title_fontsize": FS_LEGEND,
        "axes.labelsize":  FS_LABELS,
        "axes.titlesize":  FS_TITLE,
        "legend.fontsize": FS_LEGEND,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
    })
    fig_w_mm = BOX_W_MM + MARGIN_L_MM + MARGIN_R_MM
    fig_h_mm = BOX_H_MM + MARGIN_B_MM + MARGIN_T_MM
    fig = plt.figure(figsize=(mm_to_in(fig_w_mm), mm_to_in(fig_h_mm)))
    left   = MARGIN_L_MM / fig_w_mm
    bottom = MARGIN_B_MM / fig_h_mm
    ax_w   = BOX_W_MM / fig_w_mm
    ax_h   = BOX_H_MM / fig_h_mm
    ax = fig.add_axes([left, bottom, ax_w, ax_h])
    for s in ax.spines.values():
        s.set_linewidth(lw_pt)
    ax.tick_params(which="both", direction="out", length=tick_len_pt, width=lw_pt)
    ax.xaxis.labelpad = -0.4; ax.yaxis.labelpad = 0.3
    ax.tick_params(axis="x", pad=1.9); ax.tick_params(axis="y", pad=1.2)
    return fig, ax

# ====== IO ======
def load_match_histogram(path):
    with Path(path).open(newline="") as f:
        r = csv.reader(f)
        header = next(r)
        rows = [[float(x) if x else 0.0 for x in row] for row in r]
    data = np.asarray(rows, dtype=float)
    return data, header

def parse_k_header(header):
    # expects "0 Matches", "1 Matches", ...
    ks, idxs = [], []
    for i, h in enumerate(header):
        parts = h.strip().split()
        assert parts[-1] == "Matches", f"bad header token: {h}"
        ks.append(int(parts[0])); idxs.append(i)
    order = np.argsort(ks)
    ks = [ks[i] for i in order]; idxs = [idxs[i] for i in order]
    return ks, idxs

# ====== math ======
def reverse_cumulative_ge(data, idxs):
    sub = data[:, idxs].astype(float, copy=False)
    sub[sub < 0] = 0.0
    return np.cumsum(sub[:, ::-1], axis=1)[:, ::-1]

# >>> DO NOT RENAME: this is the fitter the rest of the code calls <<<
def fit_series_pos(x, y, model="shifted_power", tau_margin=0.05,
                   n_eval=2000, spacing="log"):
    """
    Fit y = A * (tau - x)^beta on y>0 points only (reverse-cumulative decline).
    Returns: (A, tau, beta), (x_fit_min, x_fit_max)
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y) & (y > 0)
    x = x[m]; y = y[m]
    assert x.size >= 5, "not enough positive points to fit"

    x_min = float(x.min()); x_max = float(x.max())
    span  = max(x_max - x_min, 1.0)

    # model: valid in fit window because we constrain tau > x_max
    def f(xx, A, tau, beta):
        z = tau - xx
        return A * (z ** beta)

    # initials
    A0    = float(y[0])
    tau0  = x_max * (1.0 + 2.0 * float(tau_margin))  # start well to the right
    beta0 = 0.8

    # bounds: A>0; tau right of data; beta positive
    tau_lb = x_max -5
    tau_ub = tau_lb + 100.0 * span
    bounds = ((0.0, tau_lb, 0.01), (np.inf, tau_ub, 30.0))

    popt, _ = curve_fit(f, x, y, p0=(A0, tau0, beta0),
                        bounds=bounds, maxfev=50000)
    A, tau, beta = map(float, popt)
    return (A, tau, beta), (x_min, x_max)

# ====== plotting ======
def plot_perk_raw(data, ks, idxs, out_svg):
    fig, ax = make_fig_ax()
    n = data.shape[0]
    x = np.arange(1, n + 1, dtype=float)
    lw_data = mm_to_pt(LINE_MM_DATA)
    for j, (k, idx) in enumerate(zip(ks, idxs)):
        color = PALETTE[j % len(PALETTE)]
        y = data[:, idx]
        y_plot = np.where(y <= 0, 1e-12, y)
        ax.plot(x, y_plot, label=str(k), color=color, linewidth=lw_data, zorder=2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=7))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.set_xlabel("Generation"); ax.set_ylabel("Counts")
    ax.set_title("Per-k counts", pad=2.7)
    ax.minorticks_off(); ax.set_xlim(0.8, 1.5e5); ax.set_ylim(0.65, 3.0e6)
    ax.legend(title="Valency", frameon=False, loc="upper left",
              bbox_to_anchor=(0.67, 0.49), ncol=2,
              columnspacing=0.7, handlelength=1.4, handletextpad=0.4,
              borderaxespad=0.5, labelspacing=0.35)
    fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)

def plot_rev_cum_with_fits(data, ks, idxs, out_svg,
                           n_eval=3000, spacing="log"):
    """
    Returns:
      params: dict k -> (A, tau, beta)
      dense : dict k -> (x_eval_full, y_eval_full)
    """
    fig, ax = make_fig_ax()
    n = data.shape[0]
    x = np.arange(1, n + 1, dtype=float)
    cum = reverse_cumulative_ge(data, idxs)

    lw_data = mm_to_pt(LINE_MM_DATA)
    lw_fit  = lw_data * 0.7

    params, dense = {}, {}

    # full plotting span for evaluation
    xmin_all, xmax_all = float(x.min()), float(x.max())
    if spacing == "log":
        assert xmin_all > 0, "log spacing requires xmin>0"
        x_eval_full = np.logspace(np.log10(xmin_all), np.log10(xmax_all), int(n_eval))
    else:
        x_eval_full = np.linspace(xmin_all, xmax_all, int(n_eval))

    for j, k in enumerate(ks):
        color = PALETTE[j % len(PALETTE)]
        y = cum[:, j]
        y_plot = np.where(y <= 0, 1e-12, y)
        ax.plot(x, y_plot, label=f"≥ {k}", color=color, linewidth=lw_data, zorder=2)

        # fit on positive part
        mp = (y > 0) & np.isfinite(y)
        xp, yp = x[mp], y[mp]
        (A, tau, beta), (x_fit_min, x_fit_max) = fit_series_pos(xp, yp)
        params[k] = (A, tau, beta)

        # evaluate across the full plotting range (only where defined: tau - x > 0)
        z = tau - x_eval_full
        y_eval_full = np.full_like(x_eval_full, np.nan, dtype=float)
        valid = z > 0
        y_eval_full[valid] = A * (z[valid] ** beta)
        dense[k] = (x_eval_full, y_eval_full)

        # draw solid on fitted span, dashed outside (only where defined)
        mid_mask   = valid & (x_eval_full >= x_fit_min) & (x_eval_full <= x_fit_max)
        left_mask  = valid & (x_eval_full <  x_fit_min)
        right_mask = valid & (x_eval_full >  x_fit_max)
        if np.any(left_mask):
            ax.plot(x_eval_full[left_mask],  y_eval_full[left_mask],  color="black",
                    linewidth=lw_fit, linestyle="--", zorder=3)
        ax.plot(x_eval_full[mid_mask],   y_eval_full[mid_mask],   color="black",
                linewidth=lw_fit, zorder=3)
        if np.any(right_mask):
            ax.plot(x_eval_full[right_mask], y_eval_full[right_mask], color="black",
                    linewidth=lw_fit, linestyle="--", zorder=3)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=7))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.set_xlabel("Generation"); ax.set_ylabel("Reverse cumulative counts")
    ax.set_title("Reverse cumulative (≥k) with shifted-power fits", pad=2.7)
    ax.minorticks_off(); ax.set_xlim(0.8, 1.5e5); ax.set_ylim(0.65, 3.0e6)
    ax.legend(title="≥ Valency", frameon=False, loc="upper left",
              bbox_to_anchor=(0.67, 0.49), ncol=2,
              columnspacing=0.7, handlelength=1.4, handletextpad=0.4,
              borderaxespad=0.5, labelspacing=0.35)

    fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=PAD_INCHES)
    return params, dense

# ====== main ======
if __name__ == "__main__":
    CSV_PATH = r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\figure_4_example_runs\evo_runs\hexagon_long_fast\match_histograms.csv"
    OUT_DIR  = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Figure_DATA\resources")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data, header = load_match_histogram(CSV_PATH)
    ks, idxs = parse_k_header(header)

    # optional cap (remove if you want all)
    cap = min(len(ks), 11)   # up to k=10
    ks, idxs = ks[:cap], idxs[:cap]

    # per-k (no fits)
    plot_perk_raw(data, ks, idxs, OUT_DIR / "perk.svg")

    # reverse cumulative with shifted-power fits (full-range eval)
    params, dense = plot_rev_cum_with_fits(
        data, ks, idxs, OUT_DIR / "rev_cum_fits_fullrange_shifted.svg",
        n_eval=3000, spacing="log"
    )

    # print params (keys match ks)
    for k in ks:
        A, tau, beta = params[k]
        print(f"≥{k}: A={A:.6g}, tau={tau:.6g}, beta={beta:.6g}")

    # example: save evaluated curve for k=1
    # np.savetxt(OUT_DIR / "fit_ge1_fullrange.txt",
    #            np.c_[dense[1][0], dense[1][1]], header="x yhat", fmt="%.8g")
