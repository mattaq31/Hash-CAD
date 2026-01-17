import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ============================================================
# Models
# ============================================================

def g2_single_exp(t, beta, tau_fast):
    """Single exponential in g2-1 space"""
    return beta * np.exp(-2.0 * t / tau_fast)


def g2_from_g1_two_mode(t, beta, a, tau_slow, alpha, tau_fast_fixed):
    """
    Physically correct two-component model:
      g1 = a * exp(-t/tau_fast) + (1-a) * exp(-(t/tau_slow)^alpha)
      g2 - 1 = beta * g1^2
    """
    g1 = (
        a * np.exp(-t / tau_fast_fixed) +
        (1.0 - a) * np.exp(-(t / tau_slow) ** alpha)
    )
    return beta * g1**2

# ============================================================
# Data loader
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
# Load data
# ============================================================

path = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_better_exp.txt"
df = load_melt_file(path)

# ============================================================
# Determine tau_fast from highest temperature (plain fit)
# ============================================================

T_ref = df["temperature_C"].max()
g_ref = df[df["temperature_C"] == T_ref]

t_ref = g_ref["delay_us"].values
y_ref = g_ref["correlation"].values

beta0 = np.max(y_ref)
tau0  = t_ref[len(t_ref)//10]

(beta_fast, tau_fast_fixed), _ = curve_fit(
    g2_single_exp,
    t_ref,
    y_ref,
    p0=[beta0, tau0],
    bounds=([0.0, 0.0], [2.0, np.inf]),
    maxfev=20000
)

print(f"Reference T = {T_ref:.0f} °C")
print(f"tau_fast = {tau_fast_fixed:.2f} µs")

# sanity plot
plt.figure()
plt.semilogx(t_ref, y_ref, ".", alpha=0.3, label="data")
plt.semilogx(t_ref, g2_single_exp(t_ref, beta_fast, tau_fast_fixed),
             "-", linewidth=2, label="single exp fit")
plt.xlabel("Delay time (µs)")
plt.ylabel("g₂ − 1")
plt.legend()
plt.tight_layout()
plt.show()

# ============================================================
# Fit all temperatures with Siegert-consistent model
# ============================================================

fit_rows = []

for T, g in df.groupby("temperature_C"):
    t = g["delay_us"].values
    y = g["correlation"].values

    m = y > 0
    t = t[m]
    y = y[m]

    beta0 = np.max(y)
    a0 = 0.5
    tau_slow0 = np.median(t)
    alpha0 = 0.7

    popt, _ = curve_fit(
        lambda t, beta, a, tau_slow, alpha:
            g2_from_g1_two_mode(t, beta, a, tau_slow, alpha, tau_fast_fixed),
        t,
        y,
        p0=[beta0, a0, tau_slow0, alpha0],
        bounds=(
            [0.0, 0.0, 0.0, 0.1],
            [2.0, 1.0, np.inf, 1.5]
        ),
        maxfev=50000
    )

    beta, a, tau_slow, alpha = popt

    fit_rows.append({
        "temperature_C": T,
        "beta": beta,
        "a_fast": a,
        "tau_slow": tau_slow,
        "alpha": alpha
    })

fit_df = pd.DataFrame(fit_rows).sort_values("temperature_C")

# ============================================================
# Plot data + fits (same color)
# ============================================================

plt.figure()

for T, g in df.groupby("temperature_C"):
    t = g["delay_us"].values
    y = g["correlation"].values
    row = fit_df[fit_df["temperature_C"] == T].iloc[0]

    y_fit = g2_from_g1_two_mode(
        t,
        row.beta,
        row.a_fast,
        row.tau_slow,
        row.alpha,
        tau_fast_fixed
    )

    line, = plt.semilogx(t, y, ".", alpha=0.3, label=f"{T:.0f} °C")
    plt.semilogx(t, y_fit, "-", color=line.get_color(), linewidth=2)

plt.xlabel("Delay time (µs)")
plt.ylabel("g₂ − 1")
plt.legend(title="Temperature")
plt.tight_layout()
plt.show()

# ============================================================
# Summary plots
# ============================================================

plt.figure()
plt.semilogy(fit_df["temperature_C"], fit_df["tau_slow"], "o-")
plt.xlabel("Temperature (°C)")
plt.ylabel("Slow relaxation time τ_slow (µs)")
plt.tight_layout()
plt.show()

plt.figure()
plt.plot(fit_df["temperature_C"], fit_df["alpha"], "o-")
plt.xlabel("Temperature (°C)")
plt.ylabel("Stretching exponent α")
plt.tight_layout()
plt.show()

plt.figure()
plt.plot(fit_df["temperature_C"], fit_df["a_fast"], "o-")
plt.xlabel("Temperature (°C)")
plt.ylabel("Fast-mode weight a")
plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt

plt.figure()

for T, g in df.groupby("temperature_C"):
    t = g["delay_us"].values
    y = g["correlation"].values

    m = y > 0
    plt.loglog(t[m], y[m], ".", alpha=0.6, label=f"{T:.0f} °C")

plt.xlabel("Delay time (µs)")
plt.ylabel("g₂ − 1")
plt.legend(title="Temperature")
plt.tight_layout()
plt.show()
