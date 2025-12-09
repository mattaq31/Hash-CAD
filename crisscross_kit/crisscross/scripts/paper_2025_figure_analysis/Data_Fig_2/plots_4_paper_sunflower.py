import pandas as pd
import numpy as np
from pathlib import Path
import toml
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle



BASE_DIR = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\parameter_sweep\Sunflower")

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

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 6,
    "axes.titlesize": 6,
    "axes.labelsize": 6,
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
})

prob_values = sorted(df_expanded["prob"].unique())
survivor_values = sorted(df_expanded["generational_survivors"].unique())

# Global grids so every subplot has identical axes
pop_values = sorted(df_expanded["population"].unique())
mut_values = sorted(df_expanded["mutation_rate"].unique())

# Shared colormap range across all plots
global_max = df_expanded["match3"].max()
# Global minimum of match3 (after cleaning/expansion)
global_min = df_expanded["match3"].min()
min_rows = df_expanded[df_expanded["match3"] == global_min].copy()

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    new_colors = cmap(np.linspace(minval, maxval, n))
    return mpl.colors.LinearSegmentedColormap.from_list(
        f"trunc({cmap.name},{minval:.2f},{maxval:.2f})",
        new_colors)

base_cmap = plt.get_cmap("YlGnBu")
cmap = truncate_colormap(base_cmap, minval=0.15, maxval=0.85)  # remove lowest 20%
cmap.set_bad("#d0d0d0")

# ---------------------- LAYOUT HANDLES ----------------------
FIG_WIDTH_MM = 180.0
fig_width_in = FIG_WIDTH_MM / 25.4

nrows = len(prob_values)
ncols = len(survivor_values)

ny = len(pop_values)  # number of y cells
nx = len(mut_values)  # number of x cells

# Height matched to data aspect so aspect="auto" doesn't stretch y
HEIGHT_SCALE = 1.0
fig_height_in = fig_width_in * (nrows / ncols) * (ny / nx) * HEIGHT_SCALE

# Margins around subplot block
MARGINS = dict(left=0.1, right=0.89, bottom=0.0525, top=0.9125)

# Inter-panel spacing (small, but not negative)
SPACING = dict(wspace=0.04, hspace=0.04)

# Colorbar axis placement [left, bottom, width, height] in figure fraction.
CBAR_AX = [0.88, 0.15, 0.02, 0.70]

# ---------------------------------------------------------
# Set axis border (spine) line width to 0.3 mm
# ---------------------------------------------------------
lw_mm = 0.3
lw_pt = lw_mm * 72 / 25.4    # mm → points
# ------------------------------------------------------------

fig, axes = plt.subplots(
    nrows, ncols,
    figsize=(fig_width_in, fig_height_in),
    squeeze=False,
)

fig.subplots_adjust(**MARGINS, **SPACING)

norm = plt.Normalize(vmin=0, vmax=global_max)
last_im = None

for row_i, prob_val in enumerate(prob_values):
    df_prob = df_expanded[df_expanded["prob"] == prob_val]

    for col_i, surv in enumerate(survivor_values):
        ax = axes[row_i, col_i]

        for spine in ax.spines.values():
            spine.set_linewidth(lw_pt)
        subset = df_prob[df_prob["generational_survivors"] == surv]

        table = subset.pivot_table(
            index="population",
            columns="mutation_rate",
            values="match3",
        ).reindex(index=pop_values, columns=mut_values)

        last_im = ax.imshow(
            table.values,
            origin="lower",
            aspect="auto",   # fills slot, no forced shrink
            cmap=cmap,
            norm=norm,
        )

        # major ticks for labels
        ax.set_xticks(np.arange(len(mut_values)))
        ax.set_yticks(np.arange(len(pop_values)))
        ax.tick_params(axis="x", which="both", bottom=False, top=False, pad=0.12)
        ax.tick_params(axis="y", which="both", left=False, right=False, pad=0.12)

        # show y labels only in first column
        if col_i == 0:
            ax.set_yticklabels(pop_values)
            ax.set_ylabel("Population", fontsize=7)
            ax.yaxis.set_label_coords(-0.165, 0.5)  # <- reliable position
        else:
            ax.set_yticklabels([])
            ax.set_ylabel("")

        # show x labels only in bottom row
        if row_i == nrows - 1:
            ax.set_xticklabels(mut_values)
            ax.set_xlabel("Mutation Rate", fontsize=7)
            ax.xaxis.set_label_coords(0.5, -0.12)  # <- reliable position
        else:
            ax.set_xticklabels([])
            ax.set_xlabel("")

        # black grid between cells (Kacheln)
        ny_loc, nx_loc = table.shape
        ax.set_xticks(np.arange(-0.5, nx_loc, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, ny_loc, 1), minor=True)
        ax.grid(which="minor", color="black", linewidth=lw_pt/2)
        ax.tick_params(which="minor", bottom=False, left=False)

        # write values into cells: ALWAYS BLACK TEXT
        for i in range(ny_loc):
            for j in range(nx_loc):
                v = table.values[i, j]
                if np.isnan(v):
                    continue
                ax.text(
                    j, i, f"{v:.0f}",
                    ha="center", va="center",
                    color="black",
                    fontsize=5,
                )


# ---------------------------------------------------------
# Mark global minimum cell(s) with a red square border
# ---------------------------------------------------------
for _, r in min_rows.iterrows():
    prob_val = r["prob"]
    surv_val = r["generational_survivors"]
    pop_val  = r["population"]
    mut_val  = r["mutation_rate"]

    # find subplot indices
    try:
        row_i = prob_values.index(prob_val)
        col_i = survivor_values.index(surv_val)
    except ValueError:
        continue

    ax = axes[row_i, col_i]

    # find cell indices inside the heatmap grid
    try:
        i = pop_values.index(pop_val)   # y index
        j = mut_values.index(mut_val)   # x index
    except ValueError:
        continue

    # Draw a red square around cell (j, i)
    rect = Rectangle(
        (j - 0.45, i - 0.45),  # bottom-left corner of cell
        0.9, 0.9,  # width and height
        fill=False,
        edgecolor="#C00000",
        linewidth=lw_pt*2,
        zorder=1  # <<< bring to top layer
    )
    ax.add_patch(rect)



# Column labels (survivors) on top
for col_i, surv in enumerate(survivor_values):
    ax_top = axes[0, col_i]
    x_center = (ax_top.get_position().x0 + ax_top.get_position().x1) / 2
    fig.text(
        x_center, MARGINS["top"] + 0.02,
        f"Survivors = {surv}",
        ha="center", va="bottom", fontsize=7
    )

# Row labels (prob) on left
for row_i, prob_val in enumerate(prob_values):
    ax_left = axes[row_i, 0]
    y_center = (ax_left.get_position().y0 + ax_left.get_position().y1) / 2
    fig.text(
        MARGINS["left"] - 0.09, y_center,
        f"Directed Mutations\n         = {100-int(prob_val*100)}%",
        ha="left", va="center", fontsize=7, rotation=90
    )

min_handle = Line2D(
    [0],[0],
    marker="s",
    markersize=6,
    markerfacecolor="none",
    markeredgecolor="#C00000",
    markeredgewidth=lw_pt*2,
    linestyle="none"
)

fig.legend(
    handles=[min_handle],
    labels=["Minimum"],
    loc="upper right",
    bbox_to_anchor=(1, MARGINS["top"] + -0.010),
    frameon=False,
    fontsize=7,
    handletextpad=0.0      # <<< adjust marker–text spacing here
)


# Manual colorbar axis on right
CBAR_AX = [0.94, 0.15, 0.02, 0.70]
cax = fig.add_axes(CBAR_AX)
cbar = fig.colorbar(last_im, cax=cax)
cbar.set_label("Parasitic Interactions with Valency 3", fontsize=7)
cbar.ax.tick_params(labelsize=5, length=2, width=0.6, pad=1)
cbar.ax.yaxis.labelpad = -35

name = "Sunflower"

# Save SVG
out_dir = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\Figures\Evo_algorithm")
out_dir.mkdir(parents=True, exist_ok=True)

out_path = out_dir / f"heatmap_match3_parameter_{name}.svg"

# Top-left overall label
fig.text(
    MARGINS["left"]+0.35,              # x in figure fraction
    MARGINS["top"] + 0.05,       # y a bit above your column headers
    name,
    ha="left", va="bottom",
    fontsize=12, fontfamily="Arial"
)


fig.savefig(out_path, format="svg")

plt.show()
print(f"Saved SVG to: {out_path}")


out_path = out_dir / f"heatmap_match3_parameter_{name}.pdf"
fig.savefig(out_path, format="pdf")

plt.show()
print(f"Saved pdf to: {out_path}")


