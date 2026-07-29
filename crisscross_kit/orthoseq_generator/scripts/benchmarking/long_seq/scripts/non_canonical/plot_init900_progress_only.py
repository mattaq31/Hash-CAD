#!/usr/bin/env python3
"""Plot only the progress-comparison panel for the init900 auxiliary analysis."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HELPER_DIR = Path(__file__).resolve().parents[1] / "auxiliary_analysis"
if str(HELPER_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_DIR))

from plot_init900_outside_crossref import (
    fit_log_progress,
    log_progress_fit,
    prepare_xy,
)


plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["figure.dpi"] = 180

DISPLAY_FIGSIZE = (8.2, 5.2)
DISPLAY_DPI = 180


def load_progress_arrays(
    *,
    module_dir: Path,
    batch_name: str,
    length_label: str,
    condition_label: str,
) -> tuple[Path, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    batch_dir = module_dir / "data" / batch_name
    data_dir = batch_dir / length_label / condition_label
    report_stem = f"{length_label}_{condition_label}_limitm8p16_budget10000000"
    hybrid_report = data_dir / f"hybrid_{report_stem}_init900_seed41.xlsx"
    hybrid_init250_report = data_dir / f"hybrid_{report_stem}_init250_seed41.xlsx"
    hybrid_init450_report = data_dir / f"hybrid_{report_stem}_init450_seed41.xlsx"
    naive_report = data_dir / f"naive_{report_stem}_seed41.xlsx"

    hybrid_progress_df = pd.read_excel(hybrid_report, sheet_name="search_progress")
    hybrid_init250_progress_df = pd.read_excel(hybrid_init250_report, sheet_name="search_progress")
    hybrid_init450_progress_df = pd.read_excel(hybrid_init450_report, sheet_name="search_progress")
    naive_progress_df = pd.read_excel(naive_report, sheet_name="search_progress")

    naive_progress_rows = naive_progress_df.loc[
        naive_progress_df["pass"] == "naive",
        ["passed_homodimer", "accepted_into_pool"],
    ].copy()
    naive_progress_rows["passed_homodimer"] = pd.to_numeric(
        naive_progress_rows["passed_homodimer"], errors="coerce"
    )
    naive_progress_rows["accepted_into_pool"] = pd.to_numeric(
        naive_progress_rows["accepted_into_pool"], errors="coerce"
    )
    naive_progress_rows = naive_progress_rows.dropna().sort_values("passed_homodimer")

    hybrid_seed_points = []
    for progress_df in (hybrid_init250_progress_df, hybrid_init450_progress_df, hybrid_progress_df):
        seed_row = progress_df.loc[
            progress_df["pass"] == "seed",
            ["pairs_collected", "pairs_after_vc"],
        ].copy()
        seed_row["pairs_collected"] = pd.to_numeric(seed_row["pairs_collected"], errors="coerce")
        seed_row["pairs_after_vc"] = pd.to_numeric(seed_row["pairs_after_vc"], errors="coerce")
        seed_row = seed_row.dropna()
        row = seed_row.iloc[-1]
        hybrid_seed_points.append((float(row["pairs_collected"]), float(row["pairs_after_vc"])))
    hybrid_seed_points = sorted(hybrid_seed_points, key=lambda pair: pair[0])

    hybrid_collection_points = []
    for progress_df in (hybrid_init250_progress_df, hybrid_init450_progress_df, hybrid_progress_df):
        collection_row = progress_df.loc[
            progress_df["pass"] == "collection",
            ["pairs_collected", "pairs_after_vc"],
        ].copy()
        collection_row["pairs_collected"] = pd.to_numeric(
            collection_row["pairs_collected"], errors="coerce"
        )
        collection_row["pairs_after_vc"] = pd.to_numeric(
            collection_row["pairs_after_vc"], errors="coerce"
        )
        collection_row = collection_row.dropna()
        row = collection_row.iloc[-1]
        hybrid_collection_points.append((float(row["pairs_collected"]), float(row["pairs_after_vc"])))
    hybrid_collection_points = sorted(hybrid_collection_points, key=lambda pair: pair[0])

    return (
        data_dir,
        naive_progress_rows["passed_homodimer"].to_numpy(dtype=float),
        naive_progress_rows["accepted_into_pool"].to_numpy(dtype=float),
        np.array([point[0] for point in hybrid_seed_points], dtype=float),
        np.array([point[1] for point in hybrid_seed_points], dtype=float),
        np.array([point[0] for point in hybrid_collection_points], dtype=float),
        np.array([point[1] for point in hybrid_collection_points], dtype=float),
    )


def plot_progress_only(
    *,
    title: str,
    naive_passed_homodimer: np.ndarray,
    naive_retained_pairs: np.ndarray,
    hybrid_seed_x_values: np.ndarray,
    hybrid_seed_pairs_after_vc: np.ndarray,
    hybrid_collection_x_values: np.ndarray,
    hybrid_collection_pairs_after_vc: np.ndarray,
    progress_xmax: float,
    fit_eval_points: int,
    fit_linewidth: float,
    fit_zorder: int,
    point_zorder: int,
    point_markersize: float,
    point_edgewidth: float,
    point_edge_color: str,
    show_plot: bool,
) -> None:
    naive_x, naive_y = prepare_xy(naive_passed_homodimer, naive_retained_pairs)
    hybrid_x = np.concatenate((hybrid_seed_x_values, hybrid_collection_x_values))
    hybrid_y = np.concatenate((hybrid_seed_pairs_after_vc, hybrid_collection_pairs_after_vc))
    hybrid_x, hybrid_y = prepare_xy(hybrid_x, hybrid_y, positive_x_only=True)

    plt.rcParams["font.family"] = "Arial"
    fig, ax = plt.subplots(1, 1, figsize=DISPLAY_FIGSIZE, dpi=DISPLAY_DPI)

    fit_ymax_candidates = []

    naive_parameters = fit_log_progress(naive_x, naive_y)
    if naive_parameters is not None:
        fit_A, fit_B = naive_parameters
        print(f"{title} naive fit: y = A ln(1 + x / B) with A = {fit_A:.6g}, B = {fit_B:.6g}", flush=True)
        x_fit = np.linspace(0.0, progress_xmax, fit_eval_points)
        y_fit = log_progress_fit(x_fit, fit_A, fit_B)
        fit_ymax_candidates.append(float(np.max(y_fit)))
        ax.plot(
            x_fit,
            y_fit,
            color="#264653",
            linewidth=fit_linewidth,
            label="Naive fit",
            zorder=fit_zorder,
        )

    hybrid_parameters = fit_log_progress(hybrid_x, hybrid_y)
    if hybrid_parameters is not None:
        fit_A, fit_B = hybrid_parameters
        print(f"{title} graph fit: y = A ln(1 + x / B) with A = {fit_A:.6g}, B = {fit_B:.6g}", flush=True)
        x_fit = np.linspace(0.0, progress_xmax, fit_eval_points)
        y_fit = log_progress_fit(x_fit, fit_A, fit_B)
        fit_ymax_candidates.append(float(np.max(y_fit)))
        ax.plot(
            x_fit,
            y_fit,
            color="#E76F51",
            linewidth=fit_linewidth,
            label="Graph fit",
            zorder=fit_zorder,
        )

    point_style = {
        "s": point_markersize**2,
        "edgecolors": point_edge_color,
        "linewidths": point_edgewidth,
        "zorder": point_zorder,
    }
    ax.scatter(naive_x, naive_y, color="#9A9A9A", marker="o", label="Naive", **point_style)
    ax.scatter(
        hybrid_seed_x_values,
        hybrid_seed_pairs_after_vc,
        color="#2A9D8F",
        marker="o",
        label="Graph initial",
        **point_style,
    )
    ax.scatter(
        hybrid_collection_x_values,
        hybrid_collection_pairs_after_vc,
        color="#2A9D8F",
        marker="s",
        label="Graph collected",
        **point_style,
    )

    ax.set_xlabel("Candidates", fontsize=10)
    ax.set_ylabel("Orthogonal pairs", fontsize=10)
    ax.set_title(title, fontsize=12, pad=8)
    ax.set_xlim(0.0, progress_xmax)
    ymax = max(
        float(np.max(naive_retained_pairs)) if len(naive_retained_pairs) else 0.0,
        float(np.max(hybrid_seed_pairs_after_vc)) if len(hybrid_seed_pairs_after_vc) else 0.0,
        float(np.max(hybrid_collection_pairs_after_vc)) if len(hybrid_collection_pairs_after_vc) else 0.0,
        max(fit_ymax_candidates) if fit_ymax_candidates else 0.0,
    )
    ax.set_ylim(0.0, ymax + 10.0 if ymax > 0.0 else 10.0)
    ax.tick_params(axis="both", labelsize=9, width=0.7, length=3)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=9,
        handlelength=1.4,
        borderaxespad=0.2,
    )

    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.14, top=0.90)
    if show_plot:
        plt.show()
    else:
        plt.close(fig)


def plot_budget_reparameterized_fits(
    *,
    title: str,
    naive_passed_homodimer: np.ndarray,
    naive_retained_pairs: np.ndarray,
    hybrid_seed_x_values: np.ndarray,
    hybrid_seed_pairs_after_vc: np.ndarray,
    hybrid_collection_x_values: np.ndarray,
    hybrid_collection_pairs_after_vc: np.ndarray,
    progress_xmax: float,
    fit_eval_points: int,
    fit_linewidth: float,
    show_plot: bool,
) -> None:
    naive_x, naive_y = prepare_xy(naive_passed_homodimer, naive_retained_pairs)
    hybrid_x = np.concatenate((hybrid_seed_x_values, hybrid_collection_x_values))
    hybrid_y = np.concatenate((hybrid_seed_pairs_after_vc, hybrid_collection_pairs_after_vc))
    hybrid_x, hybrid_y = prepare_xy(hybrid_x, hybrid_y, positive_x_only=True)

    naive_parameters = fit_log_progress(naive_x, naive_y)
    hybrid_parameters = fit_log_progress(hybrid_x, hybrid_y)

    plt.rcParams["font.family"] = "Arial"
    fig, ax = plt.subplots(1, 1, figsize=DISPLAY_FIGSIZE, dpi=DISPLAY_DPI)

    budget_xmax = progress_xmax**2
    budget_xmin = 1.0
    budget_grid = np.geomspace(budget_xmin, budget_xmax, fit_eval_points)
    fit_ymax_candidates = []

    if naive_parameters is not None:
        fit_A, fit_B = naive_parameters
        # Diagnostic reparameterization: naive candidate count scales linearly with budget.
        naive_budget_y = log_progress_fit(budget_grid, fit_A, fit_B)
        fit_ymax_candidates.append(float(np.max(naive_budget_y)))
        ax.plot(
            budget_grid,
            naive_budget_y,
            color="#264653",
            linewidth=fit_linewidth,
            label="Naive fit",
            zorder=3,
        )
        print(
            f"{title} naive budget-fit: y = A ln(1 + budget / B) with A = {fit_A:.6g}, B = {fit_B:.6g}",
            flush=True,
        )

    if hybrid_parameters is not None:
        fit_A, fit_B = hybrid_parameters
        # Diagnostic reparameterization: graph candidate count scales like sqrt(budget).
        graph_budget_y = log_progress_fit(np.sqrt(budget_grid), fit_A, fit_B)
        fit_ymax_candidates.append(float(np.max(graph_budget_y)))
        ax.plot(
            budget_grid,
            graph_budget_y,
            color="#E76F51",
            linewidth=fit_linewidth,
            label="Graph fit",
            zorder=3,
        )
        print(
            f"{title} graph budget-fit: y = A ln(1 + sqrt(budget) / B) with A = {fit_A:.6g}, B = {fit_B:.6g}",
            flush=True,
        )

    ax.set_xlabel("Computational budget (arb. units)", fontsize=10)
    ax.set_ylabel("Orthogonal pairs", fontsize=10)
    ax.set_title(f"{title}: budget-axis fit check", fontsize=12, pad=8)
    ax.set_xscale("log")
    ax.set_xlim(budget_xmin, budget_xmax)
    ymax = max(fit_ymax_candidates) if fit_ymax_candidates else 0.0
    ax.set_ylim(0.0, ymax + 10.0 if ymax > 0.0 else 10.0)
    ax.tick_params(axis="both", labelsize=9, width=0.7, length=3)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=9,
        handlelength=1.4,
        borderaxespad=0.2,
    )

    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.14, top=0.90)
    if show_plot:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    progress_xmax = 100000.0
    fit_eval_points = 4000
    fit_linewidth = 1.2

    module_dir = Path(__file__).resolve().parents[2]

    for batch_name, length_label, condition_label, title in (
        ("batch_x_TTTT_sigma1p0_seed41", "len12", "5p_TTTT", "Progress comparison: TTTT"),
        ("batch_x______sigma1p0_seed41", "len12", "5p_none", "Progress comparison: no TTTT"),
    ):
        (
            data_dir,
            naive_passed_homodimer,
            naive_retained_pairs,
            hybrid_seed_x_values,
            hybrid_seed_pairs_after_vc,
            hybrid_collection_x_values,
            hybrid_collection_pairs_after_vc,
        ) = load_progress_arrays(
            module_dir=module_dir,
            batch_name=batch_name,
            length_label=length_label,
            condition_label=condition_label,
        )
        print(f"displaying budget-axis fit check for {condition_label}...", flush=True)
        plot_budget_reparameterized_fits(
            title=title,
            naive_passed_homodimer=naive_passed_homodimer,
            naive_retained_pairs=naive_retained_pairs,
            hybrid_seed_x_values=hybrid_seed_x_values,
            hybrid_seed_pairs_after_vc=hybrid_seed_pairs_after_vc,
            hybrid_collection_x_values=hybrid_collection_x_values,
            hybrid_collection_pairs_after_vc=hybrid_collection_pairs_after_vc,
            progress_xmax=progress_xmax,
            fit_eval_points=fit_eval_points,
            fit_linewidth=fit_linewidth,
            show_plot=True,
        )
