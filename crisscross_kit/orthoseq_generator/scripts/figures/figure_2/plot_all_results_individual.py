"""
Purpose:
    Plot comparison noflank_results produced by compare_algorithms_from_pkl.py.
    X axis: offtarget limit
    Y axis: independent set size
    One plot per input noflank_results file.
"""

import os
import glob
import re
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


def _format_title(df, base_name):
    # Pull one row of metadata for display.
    num_vertices = df["num_vertices"].iloc[0] if "num_vertices" in df else None
    length = df["sequence_length"].iloc[0] if "sequence_length" in df else None
    sigma = df["sigma"].iloc[0] if "sigma" in df else None
    if sigma is None:
        match = re.search(r"sigma([0-9]+p[0-9]+)", base_name)
        if match:
            sigma = float(match.group(1).replace("p", "."))

    parts = []
    if length is not None:
        parts.append(f"sequence length = {int(length)}")
    if sigma is not None:
        parts.append(f"sigma = {sigma:g}")
    if num_vertices is not None:
        parts.append(f"N = {int(num_vertices)}")
    if not parts:
        parts.append(base_name)

    return ", ".join(parts)


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


def _x_limits_from_conflict(df, min_conflict_prob):
    if min_conflict_prob is None or "conflict_probability" not in df:
        return None
    subset = df[df["conflict_probability"] >= min_conflict_prob]
    if subset.empty or "offtarget_limit" not in subset:
        return None
    min_val = float(subset["offtarget_limit"].min())
    max_val = float(subset["offtarget_limit"].max())
    if min_val == max_val:
        pad = 0.1
    else:
        span = max_val - min_val
        pad = span * 0.05
    return (min_val - pad, max_val + pad)


def _y_limits_from_conflict(df, min_conflict_prob):
    if min_conflict_prob is None or "conflict_probability" not in df:
        return None
    subset = df[df["conflict_probability"] >= min_conflict_prob]
    if subset.empty or "independent_set_size" not in subset:
        return None
    max_val = float(subset["independent_set_size"].max())
    pad = 1.0 if max_val == 0 else max_val * 0.05
    return (0.0, max_val + pad)


def plot_results(
    results_path,
    out_dir=None,
    y_limits=None,
    x_limits=None,
    min_conflict_prob=None,
):
    # Accept either PKL or CSV noflank_results.
    df = _load_results(results_path)
    if df.empty:
        print(f"No data in {results_path}")
        return

    _apply_publication_style()

    base_name = os.path.splitext(os.path.basename(results_path))[0]
    title = _format_title(df, base_name)

    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(results_path), "plots")
    os.makedirs(out_dir, exist_ok=True)

    colors = {
        "naive": "#2ca02c",
        "vertex_cover": "#800020",
    }

    fig, ax = plt.subplots(figsize=(6.2, 4.0))

    # Plot independent set size with error bars.
    for run_type in sorted(df["run_type"].unique()):
        subset = df[df["run_type"] == run_type]
        stats = (
            subset.groupby("offtarget_limit")["independent_set_size"]
            .agg(["mean", "std"])
            .reset_index()
            .sort_values("offtarget_limit")
        )
        ax.errorbar(
            stats["offtarget_limit"],
            stats["mean"],
            yerr=stats["std"],
            color=colors.get(run_type, "#333333"),
            marker="o",
            markersize=4.5,
            linestyle="none",
            capsize=2.5,
            label=run_type,
        )

    ax.set_xlabel("Off-Target Binding limit (kcal/mol)")
    ax.set_ylabel("Independent set size")
    ax.set_title(title)
    if min_conflict_prob is not None:
        conflict_limits = _x_limits_from_conflict(df, min_conflict_prob)
        if conflict_limits is not None:
            x_limits = conflict_limits
        conflict_y_limits = _y_limits_from_conflict(df, min_conflict_prob)
        if conflict_y_limits is not None:
            y_limits = conflict_y_limits
    if x_limits is not None:
        ax.set_xlim(*x_limits)
    if y_limits is not None:
        ax.set_ylim(0.0, y_limits[1])
    # Secondary axis: conflict probability.
    ax2 = None
    if "conflict_probability" in df:
        ax2 = ax.twinx()
        conflict = (
            df.groupby("offtarget_limit")["conflict_probability"]
            .mean()
            .reset_index()
            .sort_values("offtarget_limit")
        )
        ax2.plot(
            conflict["offtarget_limit"],
            conflict["conflict_probability"],
            color="#8ecae6",
            linestyle="-",
            linewidth=1.4,
            label="conflict probability",
        )
        ax2.scatter(
            conflict["offtarget_limit"],
            conflict["conflict_probability"],
            color="#1f77b4",
            s=18,
            zorder=3,
        )
        ax2.set_ylabel("Conflict probability")
        ax2.set_ylim(0.0, 1.0)

    handles, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        handles2, labels2 = ax2.get_legend_handles_labels()
        handles += handles2
        labels += labels2
    ax.legend(handles, labels, frameon=False)

    fig.tight_layout()
    out_svg = os.path.join(out_dir, f"{base_name}_compare.svg")
    fig.savefig(out_svg, format="svg")
    plt.show()


def _collect_sequence_limits(results_paths):
    sequence_lengths = {}
    y_limits = {}
    x_limits = {}
    for path in results_paths:
        df = _load_results(path)
        if df.empty or "sequence_length" not in df:
            continue
        length = int(df["sequence_length"].iloc[0])
        sequence_lengths[path] = length

        y_values = df["independent_set_size"].dropna()
        if not y_values.empty:
            min_val = float(y_values.min())
            max_val = float(y_values.max())
            if length in y_limits:
                current_min, current_max = y_limits[length]
                y_limits[length] = (min(current_min, min_val), max(current_max, max_val))
            else:
                y_limits[length] = (min_val, max_val)

        x_values = df["offtarget_limit"].dropna() if "offtarget_limit" in df else pd.Series([], dtype=float)
        if not x_values.empty:
            min_val = float(x_values.min())
            max_val = float(x_values.max())
            if length in x_limits:
                current_min, current_max = x_limits[length]
                x_limits[length] = (min(current_min, min_val), max(current_max, max_val))
            else:
                x_limits[length] = (min_val, max_val)

    for length, (_, max_val) in y_limits.items():
        pad = 1.0 if max_val == 0 else max_val * 0.05
        y_limits[length] = (0.0, max_val + pad)

    for length, (min_val, max_val) in x_limits.items():
        span = max_val - min_val
        pad = 0.1 if span == 0 else span * 0.05
        x_limits[length] = (min_val - pad, max_val + pad)

    return sequence_lengths, y_limits, x_limits


if __name__ == "__main__":
    # Minimal defaults for manual runs.
    SCRIPT_DIR = os.path.dirname(__file__)
    OUTPUT_DIR = os.path.join(SCRIPT_DIR, "data", "TTTT_results")
    MIN_CONFLICT_PROB = 0.1  # e.g. 0.1 to set x-range by conflict probability
    RESULTS_PATHS = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_compare_results.csv")))
    # RESULTS_PATHS = [os.path.join(OUTPUT_DIR, "short_seq_5mer_sigma1p0_subset_compare_results.csv")]
    if not RESULTS_PATHS:
        raise FileNotFoundError(f"No result files found in {OUTPUT_DIR}")

    sequence_lengths, y_limits, x_limits = _collect_sequence_limits(RESULTS_PATHS)
    for path in RESULTS_PATHS:
        length = sequence_lengths.get(path)
        plot_results(
            path,
            y_limits=y_limits.get(length),
            x_limits=x_limits.get(length),
            min_conflict_prob=MIN_CONFLICT_PROB,
        )
