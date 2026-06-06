"""
Purpose:
    Explore comparison noflank_results by plotting all sigmas for a given
    sequence length into a single line-graph figure.
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt


def _apply_publication_style():
    plt.rcParams.update(
        {
            "svg.fonttype": "none",
            "font.family": "Arial",
            "axes.linewidth": 1.0,
            "lines.linewidth": 1.6,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "legend.fontsize": 9,
        }
    )


def _load_results(results_path):
    if results_path.endswith(".pkl"):
        try:
            return pd.read_pickle(results_path)
        except Exception as exc:
            raise RuntimeError(
                f"Could not read pickle '{results_path}'. "
                "Use the CSV compare file instead."
            ) from exc
    if results_path.endswith(".csv"):
        return pd.read_csv(results_path)
    raise ValueError(f"Unsupported results file type: {results_path}")


def _compute_limits(df):
    x_limits = None
    y_limits = None
    if "offtarget_limit" in df:
        x_vals = df["offtarget_limit"].dropna()
        if not x_vals.empty:
            min_val = float(x_vals.min())
            max_val = float(x_vals.max())
            span = max_val - min_val
            pad = 0.1 if span == 0 else span * 0.05
            x_limits = (min_val - pad, max_val + pad)
    if "independent_set_size" in df:
        y_vals = df["independent_set_size"].dropna()
        if not y_vals.empty:
            min_val = float(y_vals.min())
            max_val = float(y_vals.max())
            span = max_val - min_val
            pad = 1.0 if span == 0 else span * 0.05
            y_limits = (min_val - pad, max_val + pad)
    return x_limits, y_limits


def _plot_sequence_length(length, df, out_dir):
    _apply_publication_style()

    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    sigmas = sorted(df["range_sigma"].dropna().unique()) if "range_sigma" in df else []
    run_types = sorted(df["run_type"].dropna().unique()) if "run_type" in df else []

    if not sigmas or not run_types:
        print(f"Skipping sequence length {length}: missing sigma/run_type data.")
        return

    naive_sigmas = [s for s in sigmas if not df[(df["range_sigma"] == s) & (df["run_type"] == "naive")].empty]
    vertex_sigmas = [s for s in sigmas if not df[(df["range_sigma"] == s) & (df["run_type"] == "vertex_cover")].empty]

    naive_colors = {
        sigma: plt.cm.Greens(0.35 + 0.6 * (idx / max(1, len(naive_sigmas) - 1)))
        for idx, sigma in enumerate(naive_sigmas)
    }
    vertex_colors = {
        sigma: plt.cm.Reds(0.35 + 0.6 * (idx / max(1, len(vertex_sigmas) - 1)))
        for idx, sigma in enumerate(vertex_sigmas)
    }

    naive_handles = []
    naive_labels = []
    vc_handles = []
    vc_labels = []

    for sigma in sigmas:
        for run_type in run_types:
            subset = df[(df["range_sigma"] == sigma) & (df["run_type"] == run_type)]
            if subset.empty:
                continue
            stats = (
                subset.groupby("offtarget_limit")["independent_set_size"]
                .mean()
                .reset_index()
                .sort_values("offtarget_limit")
            )
            num_vertices = subset["num_vertices"].iloc[0] if "num_vertices" in subset else None
            if num_vertices is not None:
                label_run = "Naive" if run_type == "naive" else "Graph" if run_type == "vertex_cover" else run_type
                label = f"N = {int(num_vertices)}, {label_run}"
            else:
                label = "Naive" if run_type == "naive" else "Graph" if run_type == "vertex_cover" else run_type
            if run_type == "naive":
                color = naive_colors.get(sigma, "#2ca02c")
            elif run_type == "vertex_cover":
                color = vertex_colors.get(sigma, "#d62728")
            else:
                color = "#333333"
            line = ax.plot(
                stats["offtarget_limit"],
                stats["independent_set_size"],
                color=color,
                linestyle="-",
                marker="o",
                markersize=3.8,
                label=label,
            )[0]
            if run_type == "naive":
                naive_handles.append(line)
                naive_labels.append(label)
            elif run_type == "vertex_cover":
                vc_handles.append(line)
                vc_labels.append(label)

    ax.set_xlabel("Off-Target Binding Limit (kcal/mol)")
    ax.set_ylabel("Independent Set Size")
    ax.set_title(f"Sequence Length = {int(length)}")

    x_limits, y_limits = _compute_limits(df)
    if x_limits is not None:
        ax.set_xlim(*x_limits)
    if y_limits is not None:
        ax.set_ylim(*y_limits)

    # Secondary axis: conflict probability (mean across runs for each sigma).
    ax2 = None
    conflict_handles = []
    conflict_labels = []
    conflict_colors = {
        sigma: plt.cm.Greys(0.35 + 0.6 * (idx / max(1, len(sigmas) - 1)))
        for idx, sigma in enumerate(sigmas)
    }
    if "conflict_probability" in df:
        ax2 = ax.twinx()
        for sigma in sigmas:
            subset = df[df["range_sigma"] == sigma]
            if subset.empty:
                continue
            conflict = (
                subset.groupby("offtarget_limit")["conflict_probability"]
                .mean()
                .reset_index()
                .sort_values("offtarget_limit")
            )
            ax2.plot(
                conflict["offtarget_limit"],
                conflict["conflict_probability"],
                color=conflict_colors.get(sigma, "#666666"),
                linestyle="-",
                linewidth=0.9,
                alpha=0.7,
            )
            num_vertices = subset["num_vertices"].iloc[0] if "num_vertices" in subset else None
            if num_vertices is not None:
                label = f"Conflict Probability, N = {int(num_vertices)}"
            else:
                label = "Conflict Probability"
            conflict_handles.append(
                plt.Line2D([0], [0], color=conflict_colors.get(sigma, "#666666"), linewidth=0.9)
            )
            conflict_labels.append(label)
        ax2.set_ylabel("Conflict Probability")
        ax2.set_ylim(0.0, 1.0)

    handles = naive_handles + vc_handles + conflict_handles
    labels = naive_labels + vc_labels + conflict_labels
    ax.legend(handles, labels, frameon=False, ncol=3)

    fig.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    out_svg = os.path.join(out_dir, f"sequence_{int(length)}_sigmas_lineplot.svg")
    fig.savefig(out_svg, format="svg")
    plt.show()


def plot_all_sequences(results_paths, out_dir=None):
    records = []
    for path in results_paths:
        df = _load_results(path)
        if df.empty or "sequence_length" not in df:
            continue
        df = df.copy()
        df["source_path"] = path
        records.append(df)

    if not records:
        print("No noflank_results to plot.")
        return

    all_df = pd.concat(records, ignore_index=True)
    out_dir = out_dir or os.path.join(os.path.dirname(results_paths[0]), "plots_explore")

    for length in sorted(all_df["sequence_length"].dropna().unique()):
        subset = all_df[all_df["sequence_length"] == length]
        _plot_sequence_length(length, subset, out_dir)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(__file__)
    RESULTS_DIR = os.path.join(SCRIPT_DIR, "data", "noflank_results")
    RESULTS_PATHS = sorted(glob.glob(os.path.join(RESULTS_DIR, "*_compare_results.csv")))
    # RESULTS_PATHS = [os.path.join(RESULTS_DIR, "short_seq_5mer_sigma1p0_subset_compare_results.csv")]
    if not RESULTS_PATHS:
        raise FileNotFoundError(f"No result files found in {RESULTS_DIR}")
    plot_all_sequences(RESULTS_PATHS)
