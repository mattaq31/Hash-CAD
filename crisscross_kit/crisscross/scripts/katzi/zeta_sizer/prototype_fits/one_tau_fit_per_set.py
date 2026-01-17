import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

# ============================================================
# Model: normalized (g2 - 1) network-only power-law
# You are fitting normalized g2-1 directly:
# y = (1 + t/t0)^(-2*q)
# (you already baked in the factor that would arise from sqrt conversion)
# ============================================================

def g2m1_norm_network(t, t0, q):
    return (1.0 + t / t0) ** (-2.0 * q)


# ============================================================
# Loader: exact Malvern format
# ============================================================

def load_melt_file_malvern(path):
    rows = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue

            toks = [t.strip() for t in line.split("\t") if t.strip()]
            if len(toks) < 6:
                continue

            sample_id = toks[0]

            try:
                T = float(toks[1])
            except ValueError:
                continue

            try:
                sep = toks.index(sample_id, 2)
            except ValueError as e:
                raise RuntimeError(
                    f"Could not find repeated sample token '{sample_id}'"
                ) from e

            delays = np.array(toks[2:sep], dtype=float)
            corrs  = np.array(toks[sep+1:], dtype=float)

            if len(delays) != len(corrs):
                raise RuntimeError(
                    f"Length mismatch for {sample_id} at {T}°C"
                )

            sample_base = sample_id.split()[0].upper()

            for d, c in zip(delays, corrs):
                rows.append({
                    "sample_base": sample_base,
                    "sample_id": sample_id,
                    "temperature_C": T,
                    "delay_us": d,
                    "correlation": c
                })

    return pd.DataFrame(rows)


# ============================================================
# Prepare curves
# ============================================================

def build_curves(df, group_cols=("sample_base", "temperature_C"), t_max_fit=np.inf, y_min=None):
    """
    Returns a list of curves:
      {"key": (sample_base, temperature_C), "t": ..., "y": ...}
    with t sorted, y normalized by first (smallest-delay) point.
    """
    curves = []

    for key, g in df.groupby(list(group_cols)):
        g = g.sort_values("delay_us")  # critical: ensures y[0] is earliest delay
        t = g["delay_us"].values.astype(float)
        y = g["correlation"].values.astype(float)

        m = np.isfinite(t) & np.isfinite(y) & (t > 0) & (t <= t_max_fit)
        t = t[m]
        y = y[m]

        if len(t) < 10:
            continue

        y0 = y[0]
        if not np.isfinite(y0) or y0 <= 0:
            continue

        y = y / y0

        if y_min is not None:
            m2 = (y >= y_min)
            t = t[m2]
            y = y[m2]

        if len(t) < 10:
            continue

        curves.append({"key": key, "t": t, "y": y})

    return curves


# ============================================================
# Global fit: one t0 per sample_base, per-curve q
# ============================================================

def global_fit_t0_per_samplebase_q_per_curve(
    curves,
    q_init=0.5,
    q_bounds=(0.0, 5.0),
    robust_loss="soft_l1"
):
    """
    Fit parameters:
      - log_t0[sample_base] for each sample_base (enforces positivity)
      - q_i for each curve i

    Returns:
      {
        "t0_map": {sample_base: t0},
        "q_map":  {(sample_base, T): q},
        "curve_keys": [...],
        "sample_bases": [...],
        "opt": scipy result
      }
    """
    if len(curves) == 0:
        raise RuntimeError("No curves available for fitting.")

    # Determine which sample_bases exist
    sample_bases = sorted({c["key"][0] for c in curves})
    nb = len(sample_bases)
    ncurves = len(curves)

    base_to_idx = {b: i for i, b in enumerate(sample_bases)}

    # init t0 per base from medians within that base
    log_t0_init = np.zeros(nb, dtype=float)
    for b in sample_bases:
        ts = np.concatenate([c["t"] for c in curves if c["key"][0] == b])
        t0_guess = float(np.median(ts))
        log_t0_init[base_to_idx[b]] = np.log(max(t0_guess, 1e-12))

    # p = [log_t0_base0, ..., log_t0_base(nb-1), q_curve0, ..., q_curve(ncurves-1)]
    p0 = np.empty(nb + ncurves, dtype=float)
    p0[:nb] = log_t0_init
    p0[nb:] = float(q_init)

    # bounds
    log_t0_lower = np.log(1e-12)
    log_t0_upper = np.log(1e30)

    lb = np.empty_like(p0)
    ub = np.empty_like(p0)

    lb[:nb] = log_t0_lower
    ub[:nb] = log_t0_upper
    lb[nb:] = q_bounds[0]
    ub[nb:] = q_bounds[1]

    # residual builder
    def residuals(p):
        log_t0s = p[:nb]
        qs = p[nb:]

        res_list = []
        for i, c in enumerate(curves):
            base, _T = c["key"]
            t0 = np.exp(log_t0s[base_to_idx[base]])
            q = qs[i]

            t = c["t"]
            y = c["y"]
            yfit = g2m1_norm_network(t, t0, q)
            res_list.append(yfit - y)

        return np.concatenate(res_list)

    opt = least_squares(
        residuals,
        p0,
        bounds=(lb, ub),
        loss=robust_loss,
        max_nfev=200000
    )

    log_t0s_fit = opt.x[:nb]
    qs_fit = opt.x[nb:]

    t0_map = {b: float(np.exp(log_t0s_fit[base_to_idx[b]])) for b in sample_bases}
    curve_keys = [c["key"] for c in curves]
    q_map = {k: float(q) for k, q in zip(curve_keys, qs_fit)}

    return {
        "t0_map": t0_map,
        "q_map": q_map,
        "curve_keys": curve_keys,
        "sample_bases": sample_bases,
        "opt": opt
    }


# ============================================================
# MAIN
# ============================================================

PATH = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_h29_better_exp.txt"

T_MAX_FIT = np.inf
Y_MIN = None  # e.g. 1e-4 to avoid fitting deep noise floor

df = load_melt_file_malvern(PATH)
df = df[~((df["sample_base"] == "H24") & (df["temperature_C"] < 25.0))]

curves = build_curves(
    df,
    group_cols=("sample_base", "temperature_C"),
    t_max_fit=T_MAX_FIT,
    y_min=Y_MIN
)

if len(curves) == 0:
    raise RuntimeError("No valid curves after filtering/normalization.")

fit = global_fit_t0_per_samplebase_q_per_curve(
    curves,
    q_init=0.5,
    q_bounds=(0.0, 5.0),
    robust_loss="soft_l1"
)

t0_map = fit["t0_map"]
q_map = fit["q_map"]

print("==================================================")
print("Global fit results (t0 shared within each sample_base):")
for b in fit["sample_bases"]:
    print(f"  {b}: t0 = {t0_map[b]:.6g} µs")
print("  Converged:", fit["opt"].success, "-", fit["opt"].message)
print("==================================================\n")

# Table of q(T)
rows = []
for c in curves:
    base, T = c["key"]
    rows.append({
        "sample_base": base,
        "temperature_C": float(T),
        "q": q_map[c["key"]],
        "t0_shared_for_base_us": t0_map[base]
    })
q_df = pd.DataFrame(rows).sort_values(["sample_base", "temperature_C"])
print(q_df.to_string(index=False))

# ============================================================
# Overlay plots
# ============================================================

for sample_base in sorted(q_df["sample_base"].unique()):
    plt.figure()
    these = [c for c in curves if c["key"][0] == sample_base]
    t0 = t0_map[sample_base]

    for c in sorted(these, key=lambda x: x["key"][1]):
        (_, T) = c["key"]
        t = c["t"]
        y = c["y"]
        q = q_map[c["key"]]
        yfit = g2m1_norm_network(t, t0, q)

        line, = plt.semilogx(t, y, ".", alpha=0.25, label=f"{T:.0f} °C")
        plt.semilogx(t, yfit, "-", lw=2, color=line.get_color())

    plt.xlabel("Delay time (µs)")
    plt.ylabel(r"$(g_2(\tau)-1)/(g_2(0)-1)$")
    plt.title(f"{sample_base}  (shared t0 = {t0:.3g} µs)")
    plt.legend(title="Temperature")
    plt.tight_layout()
    plt.show()

# ============================================================
# Summary: q(T)
# ============================================================

plt.figure()
for sample_base in sorted(q_df["sample_base"].unique()):
    g = q_df[q_df["sample_base"] == sample_base]
    plt.plot(g["temperature_C"], g["q"], "o-", label=sample_base)

plt.xlabel("Temperature (°C)")
plt.ylabel("q  (tailiness parameter)")
plt.legend()
plt.tight_layout()
plt.show()
