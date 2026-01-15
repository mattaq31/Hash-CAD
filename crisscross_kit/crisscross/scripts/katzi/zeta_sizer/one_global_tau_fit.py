import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

# ============================================================
# Model: normalized (g2 - 1) network-only power-law
# One shared t0, per-curve q_i
# y = (1 + t/t0)^(-2*q_i)
# ============================================================

def g2m1_norm_network(t, t0, q):
    return (1.0 + t / t0) ** (-2.0 * q)


# ============================================================
# Loader: exact Malvern format (same as your routine)
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
    Returns:
      curves: list of dicts with keys:
        - key: tuple identifying curve (sample_base, temperature_C)
        - t: delay times (sorted)
        - y: normalized correlation (sorted, normalized)
    """
    curves = []

    for key, g in df.groupby(list(group_cols)):
        g = g.sort_values("delay_us")  # critical: ensures y[0] is earliest delay
        t = g["delay_us"].values.astype(float)
        y = g["correlation"].values.astype(float)

        # basic masking
        m = np.isfinite(t) & np.isfinite(y) & (t > 0) & (t <= t_max_fit)
        t = t[m]
        y = y[m]

        if len(t) < 10:
            continue

        # normalize by earliest point
        y0 = y[0]
        if not np.isfinite(y0) or y0 <= 0:
            # can't normalize meaningfully
            continue

        y = y / y0

        # optional noise-floor cutoff after normalization
        if y_min is not None:
            m2 = (y >= y_min)
            t = t[m2]
            y = y[m2]

        if len(t) < 10:
            continue

        curves.append({"key": key, "t": t, "y": y})

    return curves


# ============================================================
# Global fit: shared t0, per-curve q_i
# ============================================================

def global_fit_shared_t0_percurve_q(curves, t0_init=None, q_init=0.5, q_bounds=(0.0, 5.0), robust_loss="soft_l1"):
    """
    Parameters:
      curves: list from build_curves()
      t0_init: initial guess for shared t0 (in us). If None, use median of all times.
      q_init: initial guess for each curve's q
      q_bounds: bounds for q
      robust_loss: least_squares loss ('linear', 'soft_l1', 'huber', 'cauchy', 'arctan')

    Returns:
      result dict with:
        - t0
        - q_map: dict curve_key -> q
        - curve_keys: list of curve keys in fit order
        - opt: raw scipy result
    """
    if len(curves) == 0:
        raise RuntimeError("No curves available for fitting.")

    # initial guess for t0
    if t0_init is None:
        all_t = np.concatenate([c["t"] for c in curves])
        t0_init = float(np.median(all_t))

    # Parameterization:
    # p[0] = log_t0  (enforces positive t0)
    # p[1+i] = q_i   for each curve
    n = len(curves)

    p0 = np.zeros(1 + n, dtype=float)
    p0[0] = np.log(max(t0_init, 1e-12))
    p0[1:] = float(q_init)

    # bounds
    # log_t0 in (-inf, +inf) but we clamp to reasonable range
    # You can widen if needed.
    log_t0_lower = np.log(1e-12)
    log_t0_upper = np.log(1e30)

    lb = np.empty_like(p0)
    ub = np.empty_like(p0)

    lb[0] = log_t0_lower
    ub[0] = log_t0_upper
    lb[1:] = q_bounds[0]
    ub[1:] = q_bounds[1]

    def residuals(p):
        log_t0 = p[0]
        t0 = np.exp(log_t0)
        qs = p[1:]

        res_list = []
        for i, c in enumerate(curves):
            t = c["t"]
            y = c["y"]
            yfit = g2m1_norm_network(t, t0, qs[i])
            res_list.append(yfit - y)

        return np.concatenate(res_list)

    opt = least_squares(
        residuals,
        p0,
        bounds=(lb, ub),
        loss=robust_loss,
        max_nfev=200000
    )

    t0_fit = float(np.exp(opt.x[0]))
    qs_fit = opt.x[1:].astype(float)

    curve_keys = [c["key"] for c in curves]
    q_map = {k: float(q) for k, q in zip(curve_keys, qs_fit)}

    return {"t0": t0_fit, "q_map": q_map, "curve_keys": curve_keys, "opt": opt}


# ============================================================
# MAIN
# ============================================================

PATH = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_h29_better_exp.txt"

T_MAX_FIT = np.inf   # in us; you can set e.g. 1e7 if you want
Y_MIN = None         # e.g. 1e-4 to cut off noise floor after normalization

df = load_melt_file_malvern(PATH)
df = df[~((df["sample_base"] == "H24") & (df["temperature_C"] < 25.0))]

# Build curves grouped by (sample_base, temperature)
curves = build_curves(
    df,
    group_cols=("sample_base", "temperature_C"),
    t_max_fit=T_MAX_FIT,
    y_min=Y_MIN
)

if len(curves) == 0:
    raise RuntimeError("No valid curves after filtering/normalization.")

# Global fit: one shared t0, separate q per curve
fit = global_fit_shared_t0_percurve_q(
    curves,
    t0_init=None,
    q_init=0.5,
    q_bounds=(0.0, 5.0),
    robust_loss="soft_l1"
)

t0_global = fit["t0"]
q_map = fit["q_map"]

print("==================================================")
print("Global fit results:")
print(f"  Shared t0 (us): {t0_global:.6g}")
print(f"  Number of curves fit: {len(curves)}")
print("  Converged:", fit["opt"].success, "-", fit["opt"].message)
print("==================================================\n")

# Build a table of q(T) per sample_base
rows = []
for c in curves:
    sample_base, T = c["key"]
    rows.append({
        "sample_base": sample_base,
        "temperature_C": float(T),
        "q": q_map[c["key"]]
    })

q_df = pd.DataFrame(rows).sort_values(["sample_base", "temperature_C"])
print(q_df.to_string(index=False))

# ============================================================
# Overlay plots
# ============================================================

for sample_base in sorted(q_df["sample_base"].unique()):
    plt.figure()
    these = [c for c in curves if c["key"][0] == sample_base]

    for c in sorted(these, key=lambda x: x["key"][1]):
        (_, T) = c["key"]
        t = c["t"]
        y = c["y"]
        q = q_map[c["key"]]
        yfit = g2m1_norm_network(t, t0_global, q)

        line, = plt.semilogx(t, y, ".", alpha=0.25, label=f"{T:.0f} °C")
        plt.semilogx(t, yfit, "-", lw=2, color=line.get_color())

    plt.xlabel("Delay time (µs)")
    plt.ylabel(r"$(g_2(\tau)-1)/(g_2(0)-1)$")
    plt.title(f"{sample_base}  (shared t0 = {t0_global:.3g} µs)")
    plt.legend(title="Temperature")
    plt.tight_layout()
    plt.show()

# ============================================================
# Summary plot: q(T)
# ============================================================

plt.figure()
for sample_base in sorted(q_df["sample_base"].unique()):
    g = q_df[q_df["sample_base"] == sample_base]
    plt.plot(g["temperature_C"], g["q"], "o-", label=sample_base)
plt.xlabel("Temperature (°C)")
plt.ylabel("q  (tail exponent parameter)")
plt.legend()
plt.tight_layout()
plt.show()
