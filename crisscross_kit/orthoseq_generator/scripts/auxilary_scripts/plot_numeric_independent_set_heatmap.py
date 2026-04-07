import numpy as np
import matplotlib.pyplot as plt

from orthoseq_generator import numeric_functions as nf

# Simple heatmap over n (log-spaced) and p (linear).

n_values = np.logspace(np.log10(10), np.log10(1000), num=30)
n_values = np.unique(np.round(n_values).astype(int))

p_values = np.arange(0.1, 1.0, 0.1)

z = np.zeros((len(p_values), len(n_values)), dtype=float)

for i, p in enumerate(p_values):
    for j, n in enumerate(n_values):
        z[i, j] = nf.numeric_independet_set_estimator(int(n), float(p))

plt.figure(figsize=(8, 4.5))
plt.imshow(
    z,
    aspect="auto",
    origin="lower",
    interpolation="nearest",
    extent=[n_values[0], n_values[-1], p_values[0], p_values[-1]],
)
plt.xscale("log")
plt.xlabel("n (log scale)")
plt.ylabel("p")
plt.title("numeric_independet_set_estimator heatmap")
plt.colorbar(label="estimated m")
plt.tight_layout()
plt.show()

# Line plot: fixed p, variable n.
fixed_p = 0.05
line_n = np.logspace(np.log10(10), np.log10(100000), num=120)
line_n = np.unique(np.round(line_n).astype(int))
line_m_for_n = [nf.numeric_independet_set_estimator(int(n), float(fixed_p)) for n in line_n]

plt.figure(figsize=(7, 4))
plt.plot(line_n, line_m_for_n, linewidth=2)
plt.xscale("log")
plt.xlabel("n (log scale)")
plt.ylabel("estimated m")
plt.title(f"numeric_independet_set_estimator vs n (p={fixed_p})")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()

# Line plot: fixed n, variable p.
fixed_n = 100
line_p = np.arange(0.1, 1.0, 0.05)
line_m_for_p = [nf.numeric_independet_set_estimator(int(fixed_n), float(p)) for p in line_p]

plt.figure(figsize=(7, 4))
plt.plot(line_p, line_m_for_p, linewidth=2)
plt.xlabel("p")
plt.ylabel("estimated m")
plt.title(f"numeric_independet_set_estimator vs p (n={fixed_n})")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
