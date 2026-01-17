import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import (
    oneshot_hamming_compute,
    extract_handle_dicts
)
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import (
    read_handle_log as rhl,
    intuitive_score as in_sc
)

# ============================================================
# Model: network-only g1 power-law
# ============================================================

def g1_network_only(t, t0, q):
    return (1.0 + t / t0) ** (-2*q)


def fit_network_only(t, y, t_max_fit):
    m = (t <= t_max_fit)
    t = t[m]
    y = y[m]

    if len(t) < 10:
        raise RuntimeError("Too few points after cutoff to fit reliably.")

    # normalize so curve starts at 1
    y = y / y[0]

    # fit sqrt(data)
    #y_sqrt = np.sqrt(y)

    p0 = [float(np.median(t)), 0.5]  # t0, q

    popt, _ = curve_fit(
        g1_network_only,
        t,
        y,
        p0=p0,
        bounds=([1e-9, 0.0], [np.inf, 5.0]),
        maxfev=200000
    )

    return popt  # t0, q


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
# Run analysis
# ============================================================

PATH = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_h29_better_exp.txt"
T_MAX_FIT = 5000000000000000000.0  # µs

df = load_melt_file_malvern(PATH)


fit_rows = []
failed = []

for (sample_base, T), g in df.groupby(["sample_base", "temperature_C"]):
    t = g["delay_us"].values
    y = g["correlation"].values

    try:
        t0, q = fit_network_only(t, y, T_MAX_FIT)
    except Exception as e:
        failed.append((sample_base, T, str(e)))
        continue

    fit_rows.append({
        "sample_base": sample_base,
        "temperature_C": T,
        "t0": t0,
        "q": q
    })

if failed:
    msg = "Some fits failed:\n" + "\n".join(
        [f"  {s} @ {T}°C: {err}" for (s, T, err) in failed]
    )
    raise RuntimeError(msg)

fit_df = (
    pd.DataFrame(fit_rows)
    .set_index(["sample_base", "temperature_C"])
    .sort_index()
)


# ============================================================
# Overlay plots (sqrt-normalized data)
# ============================================================

for sample_base in ["H24", "H29"]:

    plt.figure()
    df_s = df[df["sample_base"] == sample_base]

    for T, g in df_s.groupby("temperature_C"):
        t = g["delay_us"].values
        y = g["correlation"].values

        m = (y > 0) & (t <= T_MAX_FIT)
        t = t[m]
        y = y[m]

        y = y / y[0]
        #y_sqrt = np.sqrt(y)

        t0, q = fit_df.loc[(sample_base, T), ["t0", "q"]].values
        yfit = g1_network_only(t, t0, q)

        line, = plt.semilogx(
            t, y, ".", alpha=0.25, label=f"{T:.0f} °C"
        )
        plt.semilogx(
            t, yfit, "-", lw=2, color=line.get_color()
        )

    plt.xlabel("Delay time (µs)")
    plt.ylabel(r"$g_2(\tau)-1$ (normalized)")
    plt.title(sample_base)
    plt.legend(title="Temperature")
    plt.tight_layout()
    plt.show()


# ============================================================
# Summary plots
# ============================================================

# q(T)
plt.figure()
for sample_base in fit_df.index.get_level_values(0).unique():
    g = fit_df.loc[sample_base].reset_index()
    plt.plot(g["temperature_C"], g["q"], "o-", label=sample_base)
plt.xlabel("Temperature (°C)")
plt.ylabel("q")
plt.legend()
plt.tight_layout()
plt.show()

# t0(T)
plt.figure()
for sample_base in fit_df.index.get_level_values(0).unique():
    g = fit_df.loc[sample_base].reset_index()
    plt.semilogy(g["temperature_C"], g["t0"], "o-", label=sample_base)
plt.xlabel("Temperature (°C)")
plt.ylabel("t₀ (µs)")
plt.legend()
plt.tight_layout()
plt.show()

# ln(q / t0)
plt.figure()
for sample_base in fit_df.index.get_level_values(0).unique():
    g = fit_df.loc[sample_base].reset_index()
    plt.plot(
        g["temperature_C"],
        np.log(g["q"] / g["t0"]),
        "o-",
        label=sample_base
    )
plt.xlabel("Temperature (°C)")
plt.ylabel("ln(q / t₀)")
plt.legend()
plt.tight_layout()
plt.show()
