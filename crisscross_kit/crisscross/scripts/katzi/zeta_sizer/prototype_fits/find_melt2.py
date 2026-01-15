import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ============================================================
# Model: network-only power-law
# ============================================================

def g2_network_only(t, beta, t0, q):
    """
    g1(t) = (1 + t/t0)^(-q)
    g2(t)-1 = beta * g1(t)^2
    """
    g1 = (1.0 + t / t0) ** (-q)
    return beta * g1**2


def fit_network_only(t, y, t_max_fit):
    """
    Network-only fit with enforced upper time cutoff.
    """
    m = (y > 0) & (t <= t_max_fit)
    t = t[m]
    y = y[m]

    beta0 = np.max(y)
    t0_0  = np.median(t)
    q0    = 0.5

    popt, _ = curve_fit(
        g2_network_only,
        t, y,
        p0=[beta0, t0_0, q0],
        bounds=(
            [0.0, 0.0, 0.0],
            [2.0, np.inf, 5.0]
        ),
        maxfev=200000
    )

    return popt  # beta, t0, q


# ============================================================
# Load data (unchanged)
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
# Parameters
# ============================================================

t_max_fit = 2000.0  # µs — enforced everywhere

path = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_better_exp.txt"
df = load_melt_file(path)


# ============================================================
# Fit all temperatures
# ============================================================

fit_rows = []

for T, g in df.groupby("temperature_C"):
    t = g["delay_us"].values
    y = g["correlation"].values

    beta, t0, q = fit_network_only(t, y, t_max_fit)

    fit_rows.append({
        "temperature_C": T,
        "beta": beta,
        "t0": t0,
        "q": q
    })

fit_df = pd.DataFrame(fit_rows).sort_values("temperature_C")


# ============================================================
# Overlay plot (same cutoff used for plotting)
# ============================================================

plt.figure()

for T, g in df.groupby("temperature_C"):
    t = g["delay_us"].values
    y = g["correlation"].values

    m = (y > 0) & (t <= t_max_fit)
    t = t[m]
    y = y[m]

    row = fit_df[fit_df["temperature_C"] == T].iloc[0]
    yfit = g2_network_only(t, row.beta, row.t0, row.q)

    line, = plt.semilogx(t, y, ".", alpha=0.3, label=f"{T:.0f} °C")
    plt.semilogx(t, yfit, "-", lw=2, color=line.get_color())

plt.xlabel("Delay time (µs)")
plt.ylabel("g₂ − 1")
plt.legend(title="Temperature")
plt.tight_layout()
plt.show()


# ============================================================
# Log–log diagnostic plot (cutoff enforced)
# ============================================================

plt.figure()

for T, g in df.groupby("temperature_C"):
    t = g["delay_us"].values
    y = g["correlation"].values

    m = (y > 0) & (t <= t_max_fit)
    t = t[m]
    y = y[m]

    row = fit_df[fit_df["temperature_C"] == T].iloc[0]
    yfit = g2_network_only(t, row.beta, row.t0, row.q)

    plt.loglog(t, y, ".", alpha=0.3)
    plt.loglog(t, yfit, "-", lw=2)

plt.xlabel("Delay time (µs)")
plt.ylabel("g₂ − 1  (log–log)")
plt.tight_layout()
plt.show()


# ============================================================
# Summary plots
# ============================================================

plt.figure()
plt.plot(fit_df["temperature_C"], fit_df["q"], "o-")
plt.xlabel("Temperature (°C)")
plt.ylabel("Network exponent q")
plt.tight_layout()
plt.show()

plt.figure()
plt.semilogy(fit_df["temperature_C"], fit_df["t0"], "o-")
plt.xlabel("Temperature (°C)")
plt.ylabel("Network crossover time t₀ (µs)")
plt.tight_layout()
plt.show()

plt.figure()
plt.plot(fit_df["temperature_C"], fit_df["beta"], "o-")
plt.xlabel("Temperature (°C)")
plt.ylabel("β (coherence factor)")
plt.tight_layout()
plt.show()

plt.figure()
plt.plot(fit_df["q"], np.log(fit_df["q"]/fit_df["t0"]), "o")
plt.xlabel("q")
plt.ylabel("ln(q / t₀)")
plt.tight_layout()
plt.show()