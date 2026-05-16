#!/usr/bin/env python3
"""
Display the distribution of per-pair conflict probabilities for one workbook.

This script:
1. loads one workbook matrix bundle
2. reads `search.offtarget_limit`
3. reuses `compute_vertex_conflict_probabilities(...)`
4. plots the distribution of p_i values
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[6]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.vertex_cover_algorithms import (
    build_edges,
    compute_pair_conflict_probability,
)
from fit_naive_proxy_rate import (
    effective_conflict_probability,
    extract_hybrid_throughputs,
    extract_naive_trajectory,
    fit_log_model,
    load_search_progress as load_fit_search_progress,
    slope_at_target_size,
)


MODULE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = (
    MODULE_DIR / "data" / "exploratory" / "ortho_16mers8p16_new_sheettest7.xlsx"
)
DEFAULT_NAIVE_REPORT_PATH = (
    MODULE_DIR / "data" / "exploratory" / "naive_len16_5p_none_limitm8p16_seed41.xlsx"
)
DEFAULT_OUTPUT_DIR = MODULE_DIR / "data" / "exploratory"
MATRIX_FAMILY_CONFIG = {
    "selected": {
        "pair_sheet": "found_pairs",
        "hh_sheet": "selected_hh",
        "hah_sheet": "selected_hah",
        "ahah_sheet": "selected_ahah",
    },
    "seed": {
        "pair_sheet": "seed_pass_pairs",
        "hh_sheet": "seed_hh",
        "hah_sheet": "seed_hah",
        "ahah_sheet": "seed_ahah",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Display the per-pair conflict probability distribution."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Path to the XLSX report.",
    )
    parser.add_argument(
        "--matrix-family",
        choices=["auto", "seed", "selected"],
        default="auto",
        help="Which matrix bundle to use. `auto` prefers `seed` when present.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for saved outputs.",
    )
    parser.add_argument(
        "--write-csv",
        action="store_true",
        help="Write the p_i table to CSV.",
    )
    parser.add_argument(
        "--naive-report",
        type=Path,
        default=DEFAULT_NAIVE_REPORT_PATH,
        help="Naive workbook used for the proxy-fit comparison bar.",
    )
    parser.add_argument(
        "--naive-target-size",
        type=float,
        default=44.0,
        help="Target set size at which to evaluate the naive proxy-fit local rate.",
    )
    parser.add_argument(
        "--no-naive-proxy-rate",
        action="store_true",
        help="Skip the naive proxy-fit local rate bar in the acceptance comparison.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the plot window.",
    )
    return parser.parse_args()


def read_metadata_value(metadata_df: pd.DataFrame, key: str):
    rows = metadata_df.loc[metadata_df["key"] == key, "value"]
    if rows.empty:
        return None
    value = rows.iloc[0]
    if pd.isna(value) or value == "N.A.":
        return None
    return value


def choose_matrix_family(xls: pd.ExcelFile, requested_family: str) -> str:
    if requested_family != "auto":
        return requested_family
    return "seed" if "seed_hh" in xls.sheet_names else "selected"


def read_matrix_sheet(xls: pd.ExcelFile, sheet_name: str):
    return pd.read_excel(xls, sheet_name=sheet_name, index_col=0).to_numpy()


def load_report_bundle(report_path: Path, requested_family: str):
    """Load the matrix bundle and supporting sheets for one workbook."""
    xls = pd.ExcelFile(report_path)
    matrix_family = choose_matrix_family(xls, requested_family)
    config = MATRIX_FAMILY_CONFIG[matrix_family]

    metadata_df = pd.read_excel(xls, sheet_name="run_metadata")
    pair_df = pd.read_excel(xls, sheet_name=config["pair_sheet"])
    final_pair_df = pd.read_excel(xls, sheet_name="found_pairs") if "found_pairs" in xls.sheet_names else None
    search_progress_df = pd.read_excel(xls, sheet_name="search_progress") if "search_progress" in xls.sheet_names else None
    offtarget_dict = {
        "handle_handle_energies": read_matrix_sheet(xls, config["hh_sheet"]),
        "antihandle_handle_energies": read_matrix_sheet(xls, config["hah_sheet"]),
        "antihandle_antihandle_energies": read_matrix_sheet(xls, config["ahah_sheet"]),
    }
    return metadata_df, pair_df, final_pair_df, search_progress_df, offtarget_dict, matrix_family


def build_probability_df(pair_df: pd.DataFrame, rows: list[dict]) -> pd.DataFrame:
    """Attach per-vertex conflict statistics to the pair table."""
    probability_df = pd.DataFrame(rows).rename(columns={"vertex": "global_pair_id"})
    return pair_df.merge(probability_df, on="global_pair_id", how="left").sort_values(
        ["conflict_probability", "global_pair_id"],
        ascending=[False, True],
    )


def reconstruct_seed_survivor_df(
    probability_df: pd.DataFrame,
    final_pair_df: pd.DataFrame | None,
) -> pd.DataFrame | None:
    """Recover seed survivors by intersecting seed-pass and final found-pair ids."""
    if final_pair_df is None:
        return None
    final_pair_ids = set(final_pair_df["global_pair_id"].astype(int).tolist())
    survivor_df = probability_df.loc[
        probability_df["global_pair_id"].astype(int).isin(final_pair_ids)
    ].copy()
    return survivor_df.sort_values(
        ["conflict_probability", "global_pair_id"],
        ascending=[False, True],
    )


def compute_vertex_conflict_probabilities(
    offtarget_dict: dict,
    indices: list[int],
    energy_cutoff: float,
) -> list[dict]:
    """Compute degree-based conflict probabilities for every vertex in one matrix bundle."""
    edges = build_edges(offtarget_dict, indices, energy_cutoff)
    adjacency = {vertex: set() for vertex in indices}

    for u, v in edges:
        if u == v:
            continue
        adjacency[u].add(v)
        adjacency[v].add(u)

    if len(indices) <= 1:
        return [
            {
                "vertex": vertex,
                "conflict_count": 0,
                "conflict_probability": 0.0,
            }
            for vertex in indices
        ]

    denominator = len(indices) - 1
    return [
        {
            "vertex": vertex,
            "conflict_count": len(adjacency[vertex]),
            "conflict_probability": float(len(adjacency[vertex]) / denominator),
        }
        for vertex in indices
    ]


def compute_theoretical_acceptance_probability(probability_df: pd.DataFrame) -> float:
    """Compute the one-body independent-null acceptance prediction."""
    pi_values = probability_df["conflict_probability"].to_numpy(dtype=float)
    if len(pi_values) == 0:
        return float("nan")
    if np.any(pi_values >= 1.0):
        return 0.0
    return float(np.exp(np.log1p(-pi_values).sum()))


def compute_outside_conditioned_probability_df(
    probability_df: pd.DataFrame,
    survivor_df: pd.DataFrame,
    offtarget_dict: dict,
    energy_cutoff: float,
) -> pd.DataFrame:
    """
    Recompute survivor conflict probabilities against outside seed vertices only.

    This is an intentionally biased diagnostic: it excludes the survivor set from
    the reference universe and asks how often each survivor hits the remaining
    outside seed vertices.
    """
    survivor_ids = survivor_df["global_pair_id"].astype(int).tolist()
    survivor_id_set = set(survivor_ids)
    all_ids = probability_df["global_pair_id"].astype(int).tolist()
    outside_ids = [vertex_id for vertex_id in all_ids if vertex_id not in survivor_id_set]

    if not outside_ids:
        result = survivor_df.copy()
        result["outside_conflict_count"] = 0
        result["outside_conflict_probability"] = 0.0
        return result

    edges = build_edges(offtarget_dict, all_ids, energy_cutoff)
    outside_set = set(outside_ids)
    outside_counts = {vertex_id: 0 for vertex_id in survivor_ids}
    for u, v in edges:
        if u in outside_counts and v in outside_set:
            outside_counts[u] += 1
        if v in outside_counts and u in outside_set:
            outside_counts[v] += 1

    result = survivor_df.copy()
    denominator = len(outside_ids)
    result["outside_conflict_count"] = (
        result["global_pair_id"].astype(int).map(outside_counts).fillna(0).astype(int)
    )
    result["outside_conflict_probability"] = result["outside_conflict_count"] / denominator
    return result


def compute_random_reference_baseline(mean_conflict_probability: float, reference_size: int) -> float:
    """Compute the weak random-set baseline `(1 - mean_pi)^m`."""
    if reference_size <= 0:
        return float("nan")
    if mean_conflict_probability >= 1.0:
        return 0.0
    return float((1.0 - mean_conflict_probability) ** reference_size)


def apparent_conflict_probability_from_acceptance(
    acceptance_probability: float,
    reference_size: int,
) -> float:
    """Convert an acceptance probability into the homogeneous apparent conflict rate."""
    if reference_size <= 0:
        return float("nan")
    if acceptance_probability <= 0.0:
        return 1.0
    if acceptance_probability >= 1.0:
        return 0.0
    return float(1.0 - math.exp(math.log(acceptance_probability) / reference_size))


def extract_collection_acceptance_stats(search_progress_df: pd.DataFrame | None) -> dict | None:
    """Read the hybrid collection-pass empirical acceptance counters."""
    if search_progress_df is None or "pass" not in search_progress_df.columns:
        return None
    collection_rows = search_progress_df.loc[search_progress_df["pass"] == "collection"].copy()
    if collection_rows.empty:
        return None

    row = collection_rows.iloc[-1]
    passed_homodimer = pd.to_numeric(row.get("passed_homodimer"), errors="coerce")
    accepted_into_pool = pd.to_numeric(row.get("accepted_into_pool"), errors="coerce")
    if pd.isna(passed_homodimer) or pd.isna(accepted_into_pool) or passed_homodimer <= 0:
        return None

    return {
        "passed_homodimer": int(passed_homodimer),
        "accepted_into_pool": int(accepted_into_pool),
        "empirical_acceptance_probability": float(accepted_into_pool / passed_homodimer),
    }


def compute_naive_proxy_rate(
    hybrid_progress_df: pd.DataFrame | None,
    naive_report_path: Path,
    target_size: float,
) -> float | None:
    """Evaluate the naive proxy-fit local rate at the requested target size."""
    if hybrid_progress_df is None:
        return None

    throughputs = extract_hybrid_throughputs(hybrid_progress_df)
    pooled_rho = throughputs.get("pooled")
    if pooled_rho is None:
        return None

    naive_progress_df = load_fit_search_progress(naive_report_path)
    naive_trajectory_df = extract_naive_trajectory(naive_progress_df)
    proxy_x = pooled_rho * naive_trajectory_df["raw_attempts"].to_numpy(dtype=float)
    y_values = naive_trajectory_df["pairs_found"].to_numpy(dtype=float)
    k_value, _ = fit_log_model(proxy_x, y_values)
    return slope_at_target_size(k_value, target_size)


def compute_naive_proxy_conflict_probability(
    hybrid_progress_df: pd.DataFrame | None,
    naive_report_path: Path,
) -> float | None:
    """Read the naive proxy fit back into an implied per-pair conflict probability."""
    if hybrid_progress_df is None:
        return None

    throughputs = extract_hybrid_throughputs(hybrid_progress_df)
    pooled_rho = throughputs.get("pooled")
    if pooled_rho is None:
        return None

    naive_progress_df = load_fit_search_progress(naive_report_path)
    naive_trajectory_df = extract_naive_trajectory(naive_progress_df)
    proxy_x = pooled_rho * naive_trajectory_df["raw_attempts"].to_numpy(dtype=float)
    y_values = naive_trajectory_df["pairs_found"].to_numpy(dtype=float)
    k_value, _ = fit_log_model(proxy_x, y_values)
    return effective_conflict_probability(k_value)


def build_empirical_mass_df(probability_df: pd.DataFrame) -> pd.DataFrame:
    """Tabulate the empirical probability mass function of the per-vertex `p_i` values."""
    return (
        probability_df["conflict_probability"]
        .value_counts(normalize=True)
        .sort_index()
        .rename_axis("pi")
        .reset_index(name="empirical_probability_mass")
    )


def build_er_mass_df(vertex_count: int, edge_probability: float) -> pd.DataFrame:
    """Construct the Erdős-Rényi reference mass function and CDF."""
    if vertex_count <= 1:
        return pd.DataFrame(
            [{"pi": 0.0, "er_probability_mass": 1.0, "er_cdf": 1.0}]
        )

    degree_count = vertex_count - 1
    rows = []
    cumulative = 0.0
    for k in range(degree_count + 1):
        pmf = (
            math.comb(degree_count, k)
            * (edge_probability ** k)
            * ((1.0 - edge_probability) ** (degree_count - k))
        )
        cumulative += pmf
        rows.append(
            {
                "pi": k / degree_count,
                "er_probability_mass": pmf,
                "er_cdf": cumulative,
            }
        )
    return pd.DataFrame(rows)


def build_empirical_cdf_df(probability_df: pd.DataFrame) -> pd.DataFrame:
    """Build the empirical CDF of the per-vertex conflict probabilities."""
    empirical_cdf_df = build_empirical_mass_df(probability_df)
    empirical_cdf_df["empirical_cdf"] = empirical_cdf_df["empirical_probability_mass"].cumsum()
    return empirical_cdf_df


def plot_probability_distribution(
    probability_df: pd.DataFrame,
    report_path: Path,
    matrix_family: str,
    output_dir: Path,
    er_mass_df: pd.DataFrame,
    *,
    show: bool,
) -> Path:
    """Plot the empirical `p_i` distribution against the ER reference."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    values = probability_df["conflict_probability"].to_numpy()
    empirical_cdf_df = build_empirical_cdf_df(probability_df)
    bin_count = min(20, max(5, len(values)))
    hist_density, bin_edges, _ = axes[0].hist(
        values,
        bins=bin_count,
        density=True,
        color="#2A9D8F",
        edgecolor="black",
        linewidth=0.6,
        alpha=0.7,
        label="Observed",
    )
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_widths = np.diff(bin_edges)
    er_density = []
    for left, right, width in zip(bin_edges[:-1], bin_edges[1:], bin_widths):
        if right == bin_edges[-1]:
            mask = (er_mass_df["pi"] >= left) & (er_mass_df["pi"] <= right)
        else:
            mask = (er_mass_df["pi"] >= left) & (er_mass_df["pi"] < right)
        bin_probability = float(er_mass_df.loc[mask, "er_probability_mass"].sum())
        er_density.append(bin_probability / width if width > 0 else 0.0)

    axes[0].plot(
        bin_centers,
        er_density,
        color="#E76F51",
        linewidth=1.8,
        label="ER analytical",
    )
    axes[0].set_title("Histogram of p_i")
    axes[0].set_xlabel("p_i")
    axes[0].set_ylabel("Density")
    axes[0].legend(frameon=False)

    axes[1].step(
        empirical_cdf_df["pi"],
        empirical_cdf_df["empirical_cdf"],
        where="post",
        color="#264653",
        linewidth=1.5,
        label="Observed",
    )
    axes[1].plot(
        er_mass_df["pi"],
        er_mass_df["er_cdf"],
        color="#E76F51",
        linewidth=1.2,
        label="ER analytical",
    )
    axes[1].set_title("CDF of p_i")
    axes[1].set_xlabel("p_i")
    axes[1].set_ylabel("Cumulative probability")
    axes[1].legend(frameon=False)

    fig.suptitle(f"{report_path.stem} [{matrix_family}]", fontsize=11)
    fig.tight_layout()

    output_path = output_dir / f"{report_path.stem}_{matrix_family}_pi_distribution.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return output_path


def write_probability_csv(
    report_path: Path,
    matrix_family: str,
    probability_df: pd.DataFrame,
    output_dir: Path,
) -> Path:
    """Write the per-vertex conflict table to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{report_path.stem}_{matrix_family}_pi_values.csv"
    probability_df.to_csv(output_path, index=False)
    return output_path


def plot_acceptance_comparison(
    report_path: Path,
    output_dir: Path,
    random_baseline_probability: float,
    theoretical_probability: float,
    outside_conditioned_probability: float,
    empirical_probability: float,
    naive_proxy_rate: float | None,
    naive_target_size: float,
    *,
    show: bool,
) -> Path:
    """Compare acceptance probabilities from the retained graph diagnostics."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    labels = [
        "Random baseline\n(1-mean(pi))^m",
        "Theory\nprod(1-p_i)",
        "Outside-conditioned\nprod(1-p_i^out)",
        "Empirical\naccepted/passed_homodimer",
    ]
    values = [
        random_baseline_probability,
        theoretical_probability,
        outside_conditioned_probability,
        empirical_probability,
    ]
    colors = ["#6C757D", "#264653", "#8E6C8A", "#E76F51"]
    if naive_proxy_rate is not None:
        labels.append(f"Rate estimate\nlocal rate @ {naive_target_size:.0f}")
        values.append(naive_proxy_rate)
        colors.append("#2A9D8F")
    ax.bar(labels, values, color=colors, width=0.65)
    ax.set_ylabel("Acceptance probability")
    ax.set_ylim(0.0, max(values) * 1.15 if max(values) > 0 else 1.0)
    ax.set_title("Stage-2 acceptance comparison")
    for idx, value in enumerate(values):
        ax.text(idx, value, f"{value:.3e}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()

    output_path = output_dir / f"{report_path.stem}_seed_acceptance_comparison.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return output_path


def plot_conflict_probability_comparison(
    report_path: Path,
    output_dir: Path,
    probability_by_label: list[tuple[str, float]],
    *,
    show: bool,
) -> Path:
    """Compare apparent per-pair conflict probabilities on one common scale."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    labels = [label for label, _ in probability_by_label]
    values = [value for _, value in probability_by_label]
    palette = ["#6C757D", "#264653", "#E76F51", "#2A9D8F", "#577590"]
    colors = palette[: len(values)]

    ax.bar(labels, values, color=colors, width=0.65)
    ax.set_ylabel("Apparent conflict probability")
    ax.set_ylim(0.0, max(values) * 1.15 if max(values) > 0 else 1.0)
    ax.set_title("Conflict-probability comparison")
    for idx, value in enumerate(values):
        ax.text(idx, value, f"{value:.3e}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()

    output_path = output_dir / f"{report_path.stem}_seed_conflict_probability_comparison.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return output_path


def plot_seed_survivor_distribution(
    seed_probability_df: pd.DataFrame,
    survivor_df: pd.DataFrame,
    report_path: Path,
    output_dir: Path,
    *,
    show: bool,
) -> Path:
    """Compare the seed-pool and survivor `p_i` distributions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    full_values = seed_probability_df["conflict_probability"].to_numpy()
    survivor_values = survivor_df["conflict_probability"].to_numpy()
    bin_count = min(20, max(5, len(full_values)))

    axes[0].hist(
        full_values,
        bins=bin_count,
        density=True,
        color="#2A9D8F",
        edgecolor="black",
        linewidth=0.6,
        alpha=0.55,
        label="Initial seed pool",
    )
    axes[0].hist(
        survivor_values,
        bins=bin_count,
        density=True,
        histtype="step",
        color="#E76F51",
        linewidth=1.8,
        label="Seed survivors",
    )
    axes[0].set_title("Seed survivors within initial pool")
    axes[0].set_xlabel("p_i")
    axes[0].set_ylabel("Density")
    axes[0].legend(frameon=False)

    full_sorted = np.sort(full_values)
    survivor_sorted = np.sort(survivor_values)
    full_cdf = np.arange(1, len(full_sorted) + 1) / len(full_sorted)
    survivor_cdf = np.arange(1, len(survivor_sorted) + 1) / len(survivor_sorted)

    axes[1].step(full_sorted, full_cdf, where="post", color="#264653", linewidth=1.4, label="Initial seed pool")
    axes[1].step(
        survivor_sorted,
        survivor_cdf,
        where="post",
        color="#E76F51",
        linewidth=1.6,
        label="Seed survivors",
    )
    axes[1].set_title("CDF: seed pool vs survivors")
    axes[1].set_xlabel("p_i")
    axes[1].set_ylabel("Cumulative probability")
    axes[1].legend(frameon=False)

    fig.suptitle(f"{report_path.stem} [seed survivors]", fontsize=11)
    fig.tight_layout()

    output_path = output_dir / f"{report_path.stem}_seed_survivor_pi_distribution.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return output_path


def summarize_outside_conditioned_diagnostic(
    probability_df: pd.DataFrame,
    survivor_df: pd.DataFrame,
    offtarget_dict: dict,
    offtarget_limit: float,
    survivor_count: int,
) -> dict[str, float]:
    """Compute the outside-only survivor diagnostic and its apparent-`p` summary."""
    outside_conditioned_probability_df = compute_outside_conditioned_probability_df(
        probability_df,
        survivor_df,
        offtarget_dict,
        offtarget_limit,
    )
    outside_conditioned_theory_df = outside_conditioned_probability_df[
        ["global_pair_id", "outside_conflict_probability"]
    ].rename(columns={"outside_conflict_probability": "conflict_probability"})
    acceptance_probability = compute_theoretical_acceptance_probability(outside_conditioned_theory_df)
    return {
        "mean_conflict_probability": float(
            outside_conditioned_probability_df["outside_conflict_probability"].mean()
        ),
        "acceptance_probability": acceptance_probability,
        "apparent_conflict_probability": apparent_conflict_probability_from_acceptance(
            acceptance_probability,
            survivor_count,
        ),
    }


def build_conflict_probability_comparison_items(
    global_probability: float,
    theoretical_apparent_conflict_probability: float,
    outside_conditioned_apparent_conflict_probability: float,
    empirical_apparent_conflict_probability: float,
    naive_proxy_conflict_probability: float | None,
) -> list[tuple[str, float]]:
    """Assemble the apparent-`p` comparison bars in one place."""
    items = [
        ("Seed graph\np", global_probability),
        ("Theory implied\np", theoretical_apparent_conflict_probability),
        ("Outside-conditioned\nimplied p", outside_conditioned_apparent_conflict_probability),
        ("Hybrid empirical\np", empirical_apparent_conflict_probability),
    ]
    if naive_proxy_conflict_probability is not None:
        items.append(("Rate estimate\nimplied p", naive_proxy_conflict_probability))
    return items


def main() -> None:
    args = parse_args()
    metadata_df, pair_df, final_pair_df, search_progress_df, offtarget_dict, matrix_family = load_report_bundle(
        args.report,
        args.matrix_family,
    )

    offtarget_limit_value = read_metadata_value(metadata_df, "search.offtarget_limit")
    if offtarget_limit_value is None:
        raise ValueError("Workbook is missing `search.offtarget_limit` in `run_metadata`.")
    offtarget_limit = float(offtarget_limit_value)

    indices = pair_df["global_pair_id"].astype(int).tolist()
    probability_rows = compute_vertex_conflict_probabilities(
        offtarget_dict,
        indices,
        offtarget_limit,
    )
    probability_df = build_probability_df(pair_df, probability_rows)

    global_probability = compute_pair_conflict_probability(offtarget_dict, offtarget_limit)
    mean_pi = float(probability_df["conflict_probability"].mean())
    er_mass_df = build_er_mass_df(len(indices), mean_pi)
    saved_plot_paths = []

    print(f"matrix_family={matrix_family}")
    print(f"graph_cutoff_offtarget_limit={offtarget_limit}")
    print(f"global_conflict_probability={global_probability:.6f}")
    print(f"mean_pi={mean_pi:.6f}")
    print("")
    print("top_pi_pairs")
    print(
        probability_df.loc[
            :,
            ["global_pair_id", "pair_idx", "conflict_count", "conflict_probability"],
        ].head(15).to_string(index=False)
    )

    plot_path = plot_probability_distribution(
        probability_df,
        args.report,
        matrix_family,
        args.output_dir,
        er_mass_df,
        show=not args.no_show,
    )
    saved_plot_paths.append(plot_path)

    if matrix_family == "seed":
        survivor_df = reconstruct_seed_survivor_df(probability_df, final_pair_df)
        if survivor_df is not None and not survivor_df.empty:
            survivor_plot_path = plot_seed_survivor_distribution(
                probability_df,
                survivor_df,
                args.report,
                args.output_dir,
                show=not args.no_show,
            )
            print(f"reconstructed_seed_survivor_count={len(survivor_df)}")
            saved_plot_paths.append(survivor_plot_path)

            unconditioned_theoretical_acceptance_probability = compute_theoretical_acceptance_probability(survivor_df)
            random_baseline_acceptance_probability = compute_random_reference_baseline(
                mean_pi,
                len(survivor_df),
            )
            random_baseline_apparent_conflict_probability = apparent_conflict_probability_from_acceptance(
                random_baseline_acceptance_probability,
                len(survivor_df),
            )
            theoretical_apparent_conflict_probability = apparent_conflict_probability_from_acceptance(
                unconditioned_theoretical_acceptance_probability,
                len(survivor_df),
            )
            collection_stats = extract_collection_acceptance_stats(search_progress_df)
            naive_proxy_rate = None
            naive_proxy_conflict_probability = None
            if not args.no_naive_proxy_rate:
                naive_proxy_rate = compute_naive_proxy_rate(
                    search_progress_df,
                    args.naive_report,
                    args.naive_target_size,
                )
                naive_proxy_conflict_probability = compute_naive_proxy_conflict_probability(
                    search_progress_df,
                    args.naive_report,
                )
            outside_conditioned_summary = summarize_outside_conditioned_diagnostic(
                probability_df,
                survivor_df,
                offtarget_dict,
                offtarget_limit,
                len(survivor_df),
            )
            print(f"random_baseline_acceptance_probability={random_baseline_acceptance_probability:.6e}")
            print(f"theoretical_acceptance_probability={unconditioned_theoretical_acceptance_probability:.6e}")
            print(
                "outside_conditioned_mean_conflict_probability="
                f"{outside_conditioned_summary['mean_conflict_probability']:.6e}"
            )
            print(
                "outside_conditioned_theoretical_acceptance_probability="
                f"{outside_conditioned_summary['acceptance_probability']:.6e}"
            )
            print(
                "random_baseline_apparent_conflict_probability="
                f"{random_baseline_apparent_conflict_probability:.6e}"
            )
            print(
                "theoretical_apparent_conflict_probability="
                f"{theoretical_apparent_conflict_probability:.6e}"
            )
            print(
                "outside_conditioned_apparent_conflict_probability="
                f"{outside_conditioned_summary['apparent_conflict_probability']:.6e}"
            )
            if naive_proxy_rate is not None:
                print(f"naive_proxy_fit_rate_at_target_size={naive_proxy_rate:.6e}")
            if naive_proxy_conflict_probability is not None:
                print(
                    "naive_proxy_effective_conflict_probability="
                    f"{naive_proxy_conflict_probability:.6e}"
                )
                print(
                    "naive_vs_hybrid_seed_graph_conflict_probability_delta="
                    f"{(naive_proxy_conflict_probability - global_probability):.6e}"
                )

            if collection_stats is not None:
                empirical_acceptance_probability = collection_stats["empirical_acceptance_probability"]
                empirical_apparent_conflict_probability = apparent_conflict_probability_from_acceptance(
                    empirical_acceptance_probability,
                    len(survivor_df),
                )
                comparison_plot_path = plot_acceptance_comparison(
                    args.report,
                    args.output_dir,
                    random_baseline_acceptance_probability,
                    unconditioned_theoretical_acceptance_probability,
                    outside_conditioned_summary["acceptance_probability"],
                    empirical_acceptance_probability,
                    naive_proxy_rate,
                    args.naive_target_size,
                    show=not args.no_show,
                )
                probability_comparison_items = build_conflict_probability_comparison_items(
                    global_probability,
                    theoretical_apparent_conflict_probability,
                    outside_conditioned_summary["apparent_conflict_probability"],
                    empirical_apparent_conflict_probability,
                    naive_proxy_conflict_probability,
                )
                probability_comparison_path = plot_conflict_probability_comparison(
                    args.report,
                    args.output_dir,
                    probability_comparison_items,
                    show=not args.no_show,
                )
                print(f"collection_passed_homodimer={collection_stats['passed_homodimer']}")
                print(f"collection_accepted_into_pool={collection_stats['accepted_into_pool']}")
                print(f"empirical_acceptance_probability={empirical_acceptance_probability:.6e}")
                print(
                    "empirical_apparent_conflict_probability="
                    f"{empirical_apparent_conflict_probability:.6e}"
                )
                saved_plot_paths.append(comparison_plot_path)
                saved_plot_paths.append(probability_comparison_path)

    if args.write_csv:
        csv_path = write_probability_csv(
            args.report,
            matrix_family,
            probability_df,
            args.output_dir,
        )
        print(f"wrote_csv={csv_path}")

    print("")
    print(f"plots_ready={len(saved_plot_paths)}")
    print(f"plots_saved_in={args.output_dir}")

if __name__ == "__main__":
    main()
