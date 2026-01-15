import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ============================================================
# User-defined constants
# ============================================================

TAU_FAST_FIXED = 120.0   # µs, fast diffusive mode (fixed globally)

# ============================================================
# Two-timescale model
# ============================================================

def g2_two_pop_fixed_tau(t, beta, a, t0, q):
    """
    g1(t) = a * exp(-t/tau_fast)
          + (1-a) * (1 + t/t0)^(-q)

    g2(t) - 1 = beta * g1(t)^2
    """
    g1 = (
        a * np.exp(-t / TAU_FAST_FIXED) +
        (1.0 - a) * (1.0 + t / t0) ** (-q)
    )
    return beta * g1**2


# ============================================================
# Data loader (same format you used before)
# ============================================================

def load_melt_file(path):
    rows = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue

            toks = [t.strip() for t in line.split("\t") if t.strip()]
            if len(toks) < 5:
                continue

            sample = toks[0]

            try:
                temperature = float(toks[1])
            except ValueError:
                continue

            try:
                sep_idx = toks.index(sample, 2)
            except ValueError:
                sep_idx = toks.index(sample.split()[0], 2)

            delays = np.array(toks[2:sep_idx], dtype=float)
            corrs  = np.array(toks[sep_idx + 1:], dtype=float)

            for d, c in zip(delays, corrs):
                rows.append({
                    "sample": sample,
                    "temperature_C": temperature,
                    "delay_us": d,
                    "correlation": c
                })

    return pd.DataFrame(rows)


# ============================================================
# Fit all temperatures with the SAME model
# ============================================================

def fit_all_temperatures(df):
    rows = []

    for T, g in df.groupby("temperature_C"):
        t = g["delay_us"].values
        y = g["correlation"].values

        m = y > 0
        t = t[m]
        y = y[m]

        p0 = [
            np.max(y),     # beta
            0.1,           # a_free
            np.median(t),  # t0
            0.5            # q
        ]

        popt, _ = curve_fit(
            g2_two_pop_fixed_tau,
            t, y,
            p0=p0,
            bounds=(
                [0.0, 0.0, 0.0, 0.0],
                [2.0, 1.0, np.inf, 5.0]
            ),
            maxfev=200000
        )

        rows.append({
            "temperature_C": T,
            "beta":   popt[0],
            "a_free": popt[1],
            "t0":     popt[2],
            "q":      popt[3],
        })

    return pd.DataFrame(rows).sort_values("temperature_C")


# ============================================================
# Plotting helpers
# ============================================================

def plot_overlays(df, fit_df):
    plt.figure()

    for T, g in df.groupby("temperature_C"):
        t = g["delay_us"].values
        y = g["correlation"].values
        row = fit_df[fit_df["temperature_C"] == T].iloc[0]

        yfit = g2_two_pop_fixed_tau(
            t,
            row.beta,
            row.a_free,
            row.t0,
            row.q
        )

        line, = plt.semilogx(t, y, ".", alpha=0.3)
        plt.semilogx(t, yfit, "-", lw=2, color=line.get_color())

    plt.xlabel("Delay time (µs)")
    plt.ylabel("g₂ − 1")
    plt.tight_layout()
    plt.show()


def plot_loglog(df, fit_df):
    plt.figure()

    for T, g in df.groupby("temperature_C"):
        t = g["delay_us"].values
        y = g["correlation"].values
        row = fit_df[fit_df["temperature_C"] == T].iloc[0]

        yfit = g2_two_pop_fixed_tau(
            t,
            row.beta,
            row.a_free,
            row.t0,
            row.q
        )

        m = y > 0
        plt.loglog(t[m], y[m], ".", alpha=0.3)
        plt.loglog(t[m], yfit[m], "-", lw=2)

    plt.xlabel("Delay time (µs)")
    plt.ylabel("g₂ − 1")
    plt.tight_layout()
    plt.show()


def plot_summary(fit_df):
    plt.figure()
    plt.plot(fit_df["temperature_C"], fit_df["a_free"], "o-")
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Free fraction a")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.semilogy(fit_df["temperature_C"], fit_df["t0"], "o-")
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Network timescale t₀ (µs)")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.plot(fit_df["temperature_C"], fit_df["q"], "o-")
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Network exponent q")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.plot(
        fit_df["temperature_C"],
        np.log(fit_df["q"] / fit_df["t0"]),
        "o-"
    )
    plt.xlabel("Temperature (°C)")
    plt.ylabel("ln(q / t₀)")
    plt.tight_layout()
    plt.show()


# ============================================================
# Main execution
# ============================================================

if __name__ == "__main__":

    path = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_better_exp.txt"

    df = load_melt_file(path)
    fit_df = fit_all_temperatures(df)

    print(fit_df)

    plot_overlays(df, fit_df)
    plot_loglog(df, fit_df)
    plot_summary(fit_df)
