import pandas as pd
import numpy as np
from pathlib import Path
import toml
import matplotlib.pyplot as plt

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from matplotlib.lines import Line2D

BASE_DIR = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\parameter_sweep\hexagon")

# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------
all_rows = []

for condition_dir in BASE_DIR.iterdir():
    if not condition_dir.is_dir():
        continue

    config_path = condition_dir / "evolution_config.toml"
    hist_path = condition_dir / "match_histograms.csv"
    metrics_path = condition_dir / "metrics.csv"

    if not (config_path.exists() and hist_path.exists() and metrics_path.exists()):
        continue

    # load config
    config = toml.load(config_path)

    prob = config["mutation_type_probabilities"][-1]
    population = config["evolution_population"]
    mutation_rate = config["mutation_rate"]
    generational_survivors = config["generational_survivors"]
    generations = config["evolution_generations"]

    # load histogram (NaN -> 0)
    hist = pd.read_csv(hist_path).fillna(0).to_numpy(dtype=float)

    # load metrics: Best Effective Parasitic Valency
    metrics = (
        pd.read_csv(metrics_path)["Best Effective Parasitic Valency"]
        .fillna(0)
        .to_numpy(dtype=float)
    )

    all_rows.append({
        "folder": condition_dir.name,
        "prob": prob,
        "population": population,
        "mutation_rate": mutation_rate,
        "generational_survivors": generational_survivors,
        "generations": generations,
        "hist": hist,        # numpy array (gens x 6)
        "metrics": metrics,  # numpy array (gens,)
    })

df = pd.DataFrame(all_rows)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def extract_last_histogram_entries(df):
    """
    From df with 'hist' and 'metrics' arrays, return a DataFrame with:
      - prob, population, mutation_rate, generational_survivors
      - last_histogram (length 6)
      - last_valency (final metrics value)
    """
    rows = []

    for _, row in df.iterrows():
        hist = np.nan_to_num(row["hist"], nan=0)
        last_hist = hist[hist.shape[0] - 1]   # shape (6,)

        metrics = np.nan_to_num(row["metrics"], nan=0)
        last_valency = metrics[metrics.shape[0] - 1]

        rows.append({
            "prob": row["prob"],
            "population": row["population"],
            "mutation_rate": row["mutation_rate"],
            "generational_survivors": row["generational_survivors"],
            "last_histogram": last_hist,
            "last_valency": last_valency,
        })

    return pd.DataFrame(rows)


def expand_hist_columns(df_last):
    """
    Expand last_histogram (len 6) into columns match0..match5.
    """
    out = df_last.copy()
    hist_cols = ["match0", "match1", "match2", "match3", "match4", "match5"]
    hist_data = np.vstack(out["last_histogram"].to_numpy())
    for i, col in enumerate(hist_cols):
        out[col] = hist_data[:, i]
    return out


def get_best_parameters(last_df):
    """Row with minimum last_valency."""
    idx = last_df["last_valency"].idxmin()
    return last_df.loc[idx]


def get_best_parameter_sets(last_df, top_n=5):
    """Top N rows with lowest last_valency."""
    return last_df.sort_values("last_valency").head(top_n)

# ---------------------------------------------------------------------
# Reduce to last generation, clean, expand histogram
# ---------------------------------------------------------------------
df_last = extract_last_histogram_entries(df)

# remove runs where survivors >= population (no real evolution)
df_clean = df_last[df_last["generational_survivors"] < df_last["population"]].copy()

df_expanded = expand_hist_columns(df_clean)

# ---------------------------------------------------------------------
# 1) Heatmap: for each prob x survivors, population vs mutation_rate (match3)
# ---------------------------------------------------------------------
prob_values = sorted(df_expanded["prob"].unique())
survivor_values = sorted(df_expanded["generational_survivors"].unique())

fig, axes = plt.subplots(
    len(prob_values),
    len(survivor_values),
    figsize=(4 * len(survivor_values), 4 * len(prob_values)),
    squeeze=False,
)

for row_i, prob_val in enumerate(prob_values):
    df_prob = df_expanded[df_expanded["prob"] == prob_val]

    for col_i, surv in enumerate(survivor_values):
        ax = axes[row_i, col_i]
        subset = df_prob[df_prob["generational_survivors"] == surv]

        if subset.empty:
            ax.axis("off")
            continue

        table = subset.pivot_table(
            index="population",
            columns="mutation_rate",
            values="match3",
            aggfunc="mean",
        )

        im = ax.imshow(table.values, origin="lower", aspect="auto")

        ax.set_xticks(np.arange(len(table.columns)))
        ax.set_xticklabels(table.columns)
        ax.set_yticks(np.arange(len(table.index)))
        ax.set_yticklabels(table.index)

        ax.set_xlabel("mutation_rate")
        ax.set_ylabel("population")
        ax.set_title(f"prob = {prob_val} | survivors = {surv}")

        # write values into cells
        mean_val = np.nanmean(table.values)
        for i in range(table.shape[0]):
            for j in range(table.shape[1]):
                v = table.values[i, j]
                ax.text(
                    j, i, f"{v:.0f}",
                    ha="center", va="center",
                    color="white" if v > mean_val else "black",
                    fontsize=8,
                )

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("match3")

plt.tight_layout()
plt.show()


df_fit = df_expanded[df_expanded["prob"] == 1].copy()

df_fit["pop"] = df_fit["population"]
df_fit["sur"] = df_fit["generational_survivors"]
df_fit["mut"] = df_fit["mutation_rate"]

X = df_fit[["pop", "sur", "mut"]].to_numpy(dtype=float)
y = df_fit["match3"].to_numpy(dtype=float)

poly = PolynomialFeatures(degree=2, include_bias=True)
X_poly = poly.fit_transform(X)

reg = LinearRegression()
reg.fit(X_poly, y)

pred = reg.predict(X_poly)

rmse = np.sqrt(mean_squared_error(y, pred))
r2 = r2_score(y, pred)

print("RMSE:", rmse)
print("R²:", r2)

feature_names = poly.get_feature_names_out(["pop", "sur", "mut"])
for name, coef in zip(feature_names, reg.coef_):
    print(f"{name:15s} {coef}")
print("intercept:", reg.intercept_)

# ---------------------------------------------------------------------
# 3) Scatter: population/survivors vs match3 (prob == 1), per mutation_rate
#    color = survivors, marker = population
# ---------------------------------------------------------------------
from matplotlib.lines import Line2D

df_prob1 = df_expanded[df_expanded["prob"] == 1].copy()
df_prob1["pop_over_surv"] = (
    df_prob1["population"] **3/ df_prob1["generational_survivors"]
)

# unique parameter values
mut_values = sorted(df_prob1["mutation_rate"].unique())
survivor_values = sorted(df_prob1["generational_survivors"].unique())
pop_values = sorted(df_prob1["population"].unique())

# color map for survivors
cmap = plt.get_cmap("tab10")
surv_colors = {s: cmap(i % cmap.N) for i, s in enumerate(survivor_values)}

# marker shapes for populations
markers = ["o", "s", "^", "D", "P", "X", "v", "<", ">", "h", "*"]
pop_markers = {pop: markers[i % len(markers)] for i, pop in enumerate(pop_values)}

# global y-limits
y_min = df_prob1["match3"].min()
y_max = df_prob1["match3"].max()
margin = 0.05 * (y_max - y_min)
y_min -= margin
y_max += margin

# create one subplot per mutation rate
fig, axes = plt.subplots(
    1,
    len(mut_values),
    figsize=(4 * len(mut_values), 4),
    sharey=True,
    squeeze=False,
)
axes = axes[0]

# global legend handles
surv_handles = [
    Line2D([0], [0], marker="o", linestyle="", color=surv_colors[s],
           label=f"{s}")
    for s in survivor_values
]
pop_handles = [
    Line2D([0], [0], marker=pop_markers[p], linestyle="", color="k",
           label=f"{p}")
    for p in pop_values
]

for ax, mut in zip(axes, mut_values):
    sub_mut = df_prob1[df_prob1["mutation_rate"] == mut]

    for surv in survivor_values:
        sub_s = sub_mut[sub_mut["generational_survivors"] == surv]
        if sub_s.empty:
            continue

        for pop in pop_values:
            sub_p = sub_s[sub_s["population"] == pop]
            if sub_p.empty:
                continue

            ax.scatter(
                sub_p["pop_over_surv"],
                sub_p["match3"],
                color=surv_colors[surv],
                marker=pop_markers[pop],
                alpha=0.9
            )

    ax.set_xscale("log")
    ax.set_xlabel("population / survivors")
    ax.set_title(f"mutation_rate = {mut}")
    ax.set_ylim(y_min, y_max)
    ax.grid(False)

    # legends outside each subplot
    legend1 = ax.legend(
        handles=surv_handles,
        title="survivors",
        fontsize=8,
        loc="center left",
        bbox_to_anchor=(1.02, 0.65),
    )
    ax.add_artist(legend1)

    ax.legend(
        handles=pop_handles,
        title="population",
        fontsize=8,
        loc="center left",
        bbox_to_anchor=(1.02, 0.25),
    )

axes[0].set_ylabel("match3")

plt.tight_layout(rect=[0, 0, 0.8, 1])
plt.show()




# ---------------------------------------------------------------------
# 5) Scatter per survivor value:
#    x = mutation_rate * population / survivors  (prob == 1)
#    color = mutation_rate, marker = population
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# 5) Scatter per survivor value:
#    x = mutation_rate * population / survivors  (prob == 1)
#    color = mutation_rate, marker = population
#    legends placed outside the plot, no grid
# ---------------------------------------------------------------------
from matplotlib.lines import Line2D

df_prob1 = df_expanded[df_expanded["prob"] == 1].copy()

survivor_values = sorted(df_prob1["generational_survivors"].unique())
mut_values = sorted(df_prob1["mutation_rate"].unique())
pop_values = sorted(df_prob1["population"].unique())

# color map for mutation_rate
cmap = plt.get_cmap("tab10")
mut_colors = {mut: cmap(i % cmap.N) for i, mut in enumerate(mut_values)}

# marker styles for population
markers = ["o", "s", "^", "D", "P", "X", "v", "<", ">", "h", "*"]
pop_markers = {pop: markers[i % len(markers)] for i, pop in enumerate(pop_values)}

# global legend handles
color_handles = [
    Line2D([0], [0], marker="o", linestyle="", color=mut_colors[mut],
           label=f"{mut}")
    for mut in mut_values
]
marker_handles = [
    Line2D([0], [0], marker=pop_markers[pop], linestyle="", color="k",
           label=f"{pop}")
    for pop in pop_values
]

n_cols = len(survivor_values)

fig, axes = plt.subplots(
    2,
    n_cols,
    figsize=(4 * n_cols, 6),
    sharey=True,
    squeeze=False,
)

for col, surv in enumerate(survivor_values):
    ax_mut = axes[0, col]  # top row: x = mutation_rate
    ax_pop = axes[1, col]  # bottom row: x = population

    df_s = df_prob1[df_prob1["generational_survivors"] == surv].copy()
    if df_s.empty:
        ax_mut.axis("off")
        ax_pop.axis("off")
        continue

    # -----------------------------
    # Top row: x = mutation_rate
    # connect same population
    # -----------------------------
    for pop in pop_values:
        sub = df_s[df_s["population"] == pop].copy()
        if sub.empty:
            continue

        sub = sub.sort_values("mutation_rate")

        # scatter
        for _, r in sub.iterrows():
            ax_mut.scatter(
                r["mutation_rate"],
                r["match3"],
                color=mut_colors[r["mutation_rate"]],
                marker=pop_markers[pop],
                alpha=0.9,
            )

        # connect by population
        ax_mut.plot(
            sub["mutation_rate"],
            sub["match3"],
            color="black",
            linewidth=0.8,
            alpha=0.7,
        )

    ax_mut.set_title(f"survivors = {surv}")
    ax_mut.grid(False)
    if col == 0:
        ax_mut.set_ylabel("match3")
    ax_mut.set_xlabel("mutation_rate")

    # -----------------------------
    # Bottom row: x = population
    # connect same mutation_rate
    # -----------------------------
    for mut in mut_values:
        sub = df_s[df_s["mutation_rate"] == mut].copy()
        if sub.empty:
            continue

        sub = sub.sort_values("population")

        # scatter
        for _, r in sub.iterrows():
            ax_pop.scatter(
                r["population"],
                r["match3"],
                color=mut_colors[mut],
                marker=pop_markers[r["population"]],
                alpha=0.9,
            )

        # connect by mutation_rate
        ax_pop.plot(
            sub["population"],
            sub["match3"],
            color="black",
            linewidth=0.8,
            alpha=0.7,
        )

    ax_pop.grid(False)
    if col == 0:
        ax_pop.set_ylabel("match3")
    ax_pop.set_xlabel("population")

# -----------------------------
# Global legends outside
# -----------------------------
fig.legend(
    handles=color_handles,
    title="mutation_rate",
    fontsize=8,
    loc="center left",
    bbox_to_anchor=(1.02, 0.65),
)

fig.legend(
    handles=marker_handles,
    title="population",
    fontsize=8,
    loc="center left",
    bbox_to_anchor=(1.02, 0.25),
)

plt.tight_layout(rect=[0, 0, 0.8, 1])  # leave space for legends on the right

# Save combined figure
plt.savefig("scatter_prob1_survivors_grid.pdf")
plt.savefig("scatter_prob1_survivors_grid.png", dpi=600)

plt.show()


