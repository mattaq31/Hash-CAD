import math
import matplotlib.pyplot as plt

from orthoseq_generator import numeric_functions as nf

# Set these values and run the script.
pc = 0.082
n_min = 1
n_max = 100000
num_points = 200

n_values = [
    int(
        round(
            10
            ** (
                i * (1.0 / (num_points - 1)) * (math.log10(n_max) - math.log10(n_min))
                + math.log10(n_min)
            )
        )
    )
    for i in range(num_points)
]
n_values = sorted(set(max(1, n) for n in n_values))
if n_values[-1] != n_max:
    n_values.append(n_max)

y_values = [nf.numeric_independet_set_estimator(n, pc) for n in n_values]

plt.plot(n_values, y_values, linewidth=2)
plt.xscale("log")
plt.xlim(1, n_max)
plt.xlabel("n (log scale)")
plt.ylabel("numeric_independet_set_estimator(n, pc)")
plt.title(f"numeric_independet_set_estimator vs n (pc={pc})")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.show()
