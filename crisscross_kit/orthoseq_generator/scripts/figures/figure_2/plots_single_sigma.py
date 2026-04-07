"""
Purpose:
    Explore comparison noflank_results by plotting only sigma 1.0
    for each sequence length into a single line-graph figure.
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator


STYLE = {}


def _apply_publication_style():
    # Match the histogram plot styling from sequence_computations.py
    global STYLE
    STYLE = {
        "LINEWIDTH_AXIS": 2.5,
        "TICK_WIDTH": 2.5,
        "TICK_LENGTH": 6,
        "FONTSIZE_TICKS": 16,
        "FONTSIZE_LABELS": 19,
        "FONTSIZE_TITLE": 19,
        "FONTSIZE_LEGEND": 16,
    }
    plt.rcParams.update(
        {
            "svg.fonttype": "none",
            "font.family": "Arial",
            "axes.linewidth": STYLE["LINEWIDTH_AXIS"],
            "lines.linewidth": 2.4,
            "xtick.labelsize": STYLE["FONTSIZE_TICKS"],
            "ytick.labelsize": STYLE["FONTSIZE_TICKS"],
            "axes.labelsize": STYLE["FONTSIZE_LABELS"],
            "axes.titlesize": STYLE["FONTSIZE_TITLE"],
            "legend.fontsize": STYLE["FONTSIZE_LEGEND"],
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


def _filter_by_conflict_probability(df, conflict_prob_range):
    if conflict_prob_range is None or "conflict_probability" not in df:
        return df

    min_prob, max_prob = conflict_prob_range
    mask = pd.Series(True, index=df.index)
    if min_prob is not None:
        mask &= df["conflict_probability"] >= min_prob
    if max_prob is not None:
        mask &= df["conflict_probability"] <= max_prob
    return df[mask]


def _compute_error(stats, error_bar):
    if error_bar == "std":
        return stats["std"].fillna(0.0).to_numpy()
    if error_bar == "sem":
        return (stats["std"] / stats["count"].pow(0.5)).fillna(0.0).to_numpy()
    return None


def _format_run_type_label(run_type):
    return {"naive": "Naive", "vertex_cover": "Graph"}.get(run_type, run_type)


def _format_sigma_tag(sigmas_to_plot):
    sigma_str = "_".join(str(s).replace(".", "p") for s in sigmas_to_plot)
    return f"sigma_{sigma_str}" if sigma_str else "sigma_all"


def _plot_sequence_length(
    length,
    df,
    out_dir,
    sigmas_to_plot,
    aspect_ratio=9 / 16,
    error_bar="std",
    conflict_prob_range=None,
):
    _apply_publication_style()

    fig_height = 5.5
    fig_width = fig_height / aspect_ratio
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    filtered_df = _filter_by_conflict_probability(df, conflict_prob_range)
    if filtered_df.empty:
        print(f"Skipping sequence length {length}: no data in selected conflict probability range.")
        return

    sigmas = sorted(filtered_df["range_sigma"].dropna().unique()) if "range_sigma" in filtered_df else []
    run_types = (
        sorted(filtered_df["run_type"].dropna().unique())
        if "run_type" in filtered_df
        else []
    )

    sigmas = [s for s in sigmas if float(s) in sigmas_to_plot]

    if not sigmas or not run_types:
        print(f"Skipping sequence length {length}: missing sigma/run_type data.")
        return

    naive_color = "#0b5d1e"
    vertex_color = "#7a0f16"

    handles = []
    labels = []
    legend_seen = set()

    num_vertices_for_title = None
    for sigma in sigmas:
        for run_type in run_types:
            subset = filtered_df[
                (filtered_df["range_sigma"] == sigma) & (filtered_df["run_type"] == run_type)
            ]
            if subset.empty:
                continue
            stats = (
                subset.groupby("offtarget_limit")["independent_set_size"]
                .agg(["mean", "std", "count"])
                .reset_index()
                .sort_values("offtarget_limit")
            )
            stats = stats.dropna(subset=["mean"])
            if stats.empty:
                continue
            num_vertices = subset["num_vertices"].iloc[0] if "num_vertices" in subset else None
            if num_vertices_for_title is None and num_vertices is not None:
                num_vertices_for_title = num_vertices
            label = _format_run_type_label(run_type)
            if run_type == "naive":
                color = naive_color
            elif run_type == "vertex_cover":
                color = vertex_color
            else:
                color = "#333333"
            yerr = _compute_error(stats, error_bar)
            line = ax.errorbar(
                stats["offtarget_limit"],
                stats["mean"],
                yerr=yerr,
                color=color,
                linestyle="-",
                marker="o",
                markersize=4.6,
                label=label,
                capsize=3.3 if yerr is not None else 0,
            )[0]
            if label not in legend_seen:
                handles.append(line)
                labels.append(label)
                legend_seen.add(label)

    ax.set_xlabel("Off-Target Binding Limit (kcal/mol)", fontsize=STYLE["FONTSIZE_LABELS"])
    ax.set_ylabel("Independent Set Size", fontsize=STYLE["FONTSIZE_LABELS"])
    if num_vertices_for_title is not None:
        ax.set_title(
            f"{int(length)} mer, N = {int(num_vertices_for_title)}",
            fontsize=STYLE["FONTSIZE_TITLE"],
            pad=10,
        )
    else:
        ax.set_title(f"{int(length)} mer", fontsize=STYLE["FONTSIZE_TITLE"], pad=10)

    # Secondary axis: conflict probability (mean across runs for each sigma).
    ax2 = None
    conflict_color = "#1f5fbf"
    if "conflict_probability" in filtered_df:
        ax2 = ax.twinx()
        for sigma in sigmas:
            subset = filtered_df[filtered_df["range_sigma"] == sigma]
            if subset.empty:
                continue
            conflict = (
                subset.groupby("offtarget_limit")["conflict_probability"]
                .mean()
                .reset_index()
                .sort_values("offtarget_limit")
            )
            if conflict.empty:
                continue
            ax2.plot(
                conflict["offtarget_limit"],
                conflict["conflict_probability"],
                color=conflict_color,
                linestyle="-",
                linewidth=2.4,
                alpha=0.7,
            )
        ax2.set_ylabel("Conflict Probability", fontsize=STYLE["FONTSIZE_LABELS"])
        ax2.set_ylim(0.0, 1.0)
        if "Conflict Probability" not in legend_seen:
            handles.append(plt.Line2D([0], [0], color=conflict_color, linewidth=2.4))
            labels.append("Conflict Probability")
            legend_seen.add("Conflict Probability")

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(axis="x", which="minor", length=4, width=1.2)
    ax.tick_params(
        axis="both",
        which="major",
        labelsize=STYLE["FONTSIZE_TICKS"],
        width=STYLE["TICK_WIDTH"],
        length=STYLE["TICK_LENGTH"],
    )
    for spine in ax.spines.values():
        spine.set_linewidth(STYLE["LINEWIDTH_AXIS"])
    if ax2 is not None:
        ax2.tick_params(
            axis="both",
            which="major",
            labelsize=STYLE["FONTSIZE_TICKS"],
            width=STYLE["TICK_WIDTH"],
            length=STYLE["TICK_LENGTH"],
        )
        for spine in ax2.spines.values():
            spine.set_linewidth(STYLE["LINEWIDTH_AXIS"])

    if handles:
        ax.legend(handles, labels, frameon=False, ncol=1, fontsize=STYLE["FONTSIZE_LEGEND"])

    if aspect_ratio is not None:
        if hasattr(ax, "set_box_aspect"):
            ax.set_box_aspect(aspect_ratio)
            if ax2 is not None:
                ax2.set_box_aspect(aspect_ratio)
        else:
            ax.set_aspect(aspect_ratio, adjustable="box")
            if ax2 is not None:
                ax2.set_aspect(aspect_ratio, adjustable="box")

    fig.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    sigma_tag = _format_sigma_tag(sigmas_to_plot)
    out_svg = os.path.join(out_dir, f"sequence_{int(length)}_{sigma_tag}_lineplot.svg")
    fig.savefig(out_svg, format="svg")
    plt.show()


def plot_all_sequences(
    results_paths,
    out_dir=None,
    sigmas_to_plot=(1.0,),
    aspect_ratio=9 / 16,
    error_bar="std",
    conflict_prob_range=None,
):
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
        _plot_sequence_length(
            length,
            subset,
            out_dir,
            sigmas_to_plot,
            aspect_ratio=aspect_ratio,
            error_bar=error_bar,
            conflict_prob_range=conflict_prob_range,
        )


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(__file__)
    RESULTS_DIR = os.path.join(SCRIPT_DIR, "data", "noflank_results")
    RESULTS_PATHS = sorted(glob.glob(os.path.join(RESULTS_DIR, "*_compare_results.csv")))
    # RESULTS_PATHS = [os.path.join(RESULTS_DIR, "short_seq_6mer_sigma1_subset_compare_results.csv")]
    if not RESULTS_PATHS:
        raise FileNotFoundError(f"No result files found in {RESULTS_DIR}")
    ASPECT_RATIO = 9 / 16
    MIN_CONFLICT_PROB = 0.04
    # e.g. 0.1
    MAX_CONFLICT_PROB = 0.4  # e.g. 0.8
    CONFLICT_PROB_RANGE = (MIN_CONFLICT_PROB, MAX_CONFLICT_PROB)
    plot_all_sequences(
        RESULTS_PATHS,
        sigmas_to_plot=(1.0,),
        aspect_ratio=ASPECT_RATIO,
        error_bar="std",
        conflict_prob_range=CONFLICT_PROB_RANGE,
    )
