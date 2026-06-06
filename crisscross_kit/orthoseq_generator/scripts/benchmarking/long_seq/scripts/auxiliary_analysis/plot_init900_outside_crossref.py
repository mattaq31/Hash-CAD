#!/usr/bin/env python3
"""Plot the canonical init900 auxiliary-analysis figures for both batch_x runs."""

from __future__ import annotations
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.optimize import curve_fit

PACKAGE_DIR = Path(__file__).resolve().parents[6]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

plt.rcParams["svg.fonttype"] = "none"


def build_shared_bins(
    value_arrays: list[np.ndarray],
    bin_count: int = 25,
    xmax: float | None = None,
) -> tuple[np.ndarray, float]:
    if xmax is None:
        values = np.concatenate(value_arrays)
        vmax = min(float(values.max()) + 0.05, 1.0)
    else:
        vmax = float(xmax)
    bins = np.linspace(0.0, vmax, bin_count + 1)
    return bins, vmax


def mean_conflict_probability(values: np.ndarray) -> float:
    if len(values) == 0:
        return float("nan")
    return float(np.mean(np.asarray(values, dtype=float)))


def std_conflict_probability(values: np.ndarray) -> float:
    if len(values) == 0:
        return float("nan")
    return float(np.std(np.asarray(values, dtype=float)))


def format_decimal_math(value: float) -> str:
    if not np.isfinite(value):
        return r"\mathrm{N/A}"
    return f"{value:.3f}"


def infer_output_suffix(data_dir: Path) -> str:
    length_label = data_dir.parent.name
    condition_label = data_dir.name.removeprefix("5p_")
    return f"{condition_label}_{length_label}"


def prepare_xy(x: np.ndarray, y: np.ndarray, *, positive_x_only: bool = False) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid_mask = np.isfinite(x) & np.isfinite(y)
    if positive_x_only:
        valid_mask &= x > 0.0
    else:
        valid_mask &= x >= 0.0
    return x[valid_mask], y[valid_mask]


def log_progress_fit(x: np.ndarray, A: float, B: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    clipped_x = np.clip(x, 0.0, None)
    bounded_B = float(np.clip(B, 1e-12, None))
    return A * np.log1p(clipped_x / bounded_B)


def fit_log_progress(x: np.ndarray, y: np.ndarray) -> tuple[float, float] | None:
    x, y = prepare_xy(x, y)
    if len(x) == 0:
        return None
    positive_x = x[x > 0.0]
    positive_y = y[y > 0.0]
    if len(positive_x) == 0 or len(positive_y) == 0:
        return None
    B0 = float(np.median(positive_x))
    log_scale = np.log1p(float(np.max(positive_x)) / max(B0, 1e-12))
    A0 = float(np.max(positive_y)) / max(log_scale, 1e-6)
    parameters, _ = curve_fit(
        log_progress_fit,
        x,
        y,
        p0=(A0, B0),
        bounds=([1e-8, 1e-8], [np.inf, np.inf]),
        maxfev=20000,
    )
    return float(parameters[0]), float(parameters[1])


def draw_distribution(
    ax,
    values: np.ndarray,
    bins: np.ndarray,
    xmax: float,
    *,
    color: str,
    title: str,
    xlabel: str,
) -> None:
    mean_value = mean_conflict_probability(values)
    std_value = std_conflict_probability(values)
    mean_color = "#6A1B9A"
    if np.isfinite(mean_value) and np.isfinite(std_value) and std_value > 0.0:
        ax.axvspan(
            max(0.0, mean_value - std_value),
            min(xmax, mean_value + std_value),
            color=mean_color,
            alpha=0.12,
            linewidth=0.0,
            zorder=1,
        )
    ax.hist(
        values,
        bins=bins,
        density=True,
        color=color,
        edgecolor="black",
        linewidth=0.5,
        zorder=3,
    )
    ax.axvline(
        mean_value,
        color=mean_color,
        linewidth=1.0,
        linestyle="--",
        zorder=4,
    )
    ax.set_xlabel(xlabel, fontsize=6)
    ax.set_ylabel("Density", fontsize=6)
    ax.set_title(title, fontsize=8, pad=6)
    ax.set_xlim(0.0, xmax)
    ax.tick_params(axis="both", labelsize=6, width=0.5, length=2)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    handles = [
        Line2D(
            [0],
            [0],
            color=mean_color,
            linewidth=1.0,
            linestyle="--",
            label=rf"Mean = {format_decimal_math(mean_value)}",
        ),
        Patch(
            facecolor=mean_color,
            edgecolor="none",
            alpha=0.12,
            label=rf"$\pm 1$ SD = $\pm {format_decimal_math(std_value)}$",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=6,
        handlelength=1.4,
        borderaxespad=0.2,
    )


def draw_progress_overlay(
    ax,
    naive_passed_homodimer: np.ndarray,
    naive_retained_pairs: np.ndarray,
    hybrid_seed_x_values: np.ndarray,
    hybrid_seed_pairs_after_vc: np.ndarray,
    hybrid_collection_x_values: np.ndarray,
    hybrid_collection_pairs_after_vc: np.ndarray,
    *,
    progress_xmax: float,
    fit_eval_points: int,
    fit_linewidth: float,
    fit_zorder: int,
    point_zorder: int,
    point_markersize: float,
    point_edgewidth: float,
    point_edge_color: str,
) -> None:
    naive_T, naive_n = prepare_xy(naive_passed_homodimer, naive_retained_pairs)
    hybrid_x = np.concatenate((hybrid_seed_x_values, hybrid_collection_x_values))
    hybrid_y = np.concatenate((hybrid_seed_pairs_after_vc, hybrid_collection_pairs_after_vc))
    hybrid_x, hybrid_y = prepare_xy(hybrid_x, hybrid_y, positive_x_only=True)

    point_style = {
        "s": point_markersize**2,
        "edgecolors": point_edge_color,
        "linewidths": point_edgewidth,
        "zorder": point_zorder,
    }

    naive_parameters = fit_log_progress(naive_T, naive_n)
    if naive_parameters is not None:
        fit_A, fit_B = naive_parameters
        print(f"naive fit: y = A ln(1 + x / B) with A = {fit_A:.6g}, B = {fit_B:.6g}", flush=True)
        x_fit = np.linspace(0.0, progress_xmax, fit_eval_points)
        ax.plot(
            x_fit,
            log_progress_fit(x_fit, fit_A, fit_B),
            color="#264653",
            linewidth=fit_linewidth,
            label="Naive fit",
            zorder=fit_zorder,
        )
    else:
        print("naive fit: unavailable", flush=True)

    hybrid_parameters = fit_log_progress(hybrid_x, hybrid_y)
    if hybrid_parameters is not None:
        fit_A, fit_B = hybrid_parameters
        print(f"graph fit: y = A ln(1 + x / B) with A = {fit_A:.6g}, B = {fit_B:.6g}", flush=True)
        x_fit = np.linspace(0.0, progress_xmax, fit_eval_points)
        ax.plot(
            x_fit,
            log_progress_fit(x_fit, fit_A, fit_B),
            color="#E76F51",
            linewidth=fit_linewidth,
            label="Graph fit",
            zorder=fit_zorder,
        )
    else:
        print("graph fit: unavailable", flush=True)

    ax.scatter(
        naive_T,
        naive_n,
        color="#9A9A9A",
        marker="o",
        label="Naive",
        **point_style,
    )
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
    ax.set_xlabel("Candidates", fontsize=6)
    ax.set_ylabel("Orthogonal pairs", fontsize=6)
    ax.set_title("Progress comparison", fontsize=8, pad=6)
    ax.set_xlim(0.0, progress_xmax)
    ymax = max(
        float(np.max(naive_retained_pairs)) if len(naive_retained_pairs) else 0.0,
        float(np.max(hybrid_seed_pairs_after_vc)) if len(hybrid_seed_pairs_after_vc) else 0.0,
        float(np.max(hybrid_collection_pairs_after_vc)) if len(hybrid_collection_pairs_after_vc) else 0.0,
    )
    ax.set_ylim(0.0, ymax + 10.0 if ymax > 0.0 else 10.0)
    ax.tick_params(axis="both", labelsize=6, width=0.5, length=2)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=6,
        handlelength=1.4,
        borderaxespad=0.2,
    )


def save_stack_plot(
    output_path: Path,
    bins: np.ndarray,
    xmax: float,
    random_values: np.ndarray,
    naive_values: np.ndarray,
    graph_values: np.ndarray,
    show_plots: bool,
    naive_progress_passed_homodimer: np.ndarray | None = None,
    naive_progress_retained_pairs: np.ndarray | None = None,
    hybrid_seed_x_values: np.ndarray | None = None,
    hybrid_seed_pairs_after_vc: np.ndarray | None = None,
    hybrid_collection_x_values: np.ndarray | None = None,
    hybrid_collection_pairs_after_vc: np.ndarray | None = None,
    *,
    progress_xmax: float,
    fit_eval_points: int,
    fit_linewidth: float,
    fit_zorder: int,
    point_zorder: int,
    point_markersize: float,
    point_edgewidth: float,
    point_edge_color: str,
) -> None:
    upscale = 1.25
    figure_width_mm = 177.8 * 0.32 * upscale
    panel_height_mm = 38.0 * upscale
    panel_count = 4 if naive_progress_passed_homodimer is not None else 3
    if panel_count == 4:
        height_ratios = [1.0, 1.0, 1.0, 1.4]
    else:
        height_ratios = [1.0, 1.0, 1.0]
    figure_height_mm = panel_height_mm * float(sum(height_ratios))
    figure_size_inches = (figure_width_mm / 25.4, figure_height_mm / 25.4)
    fig, axes = plt.subplots(
        panel_count,
        1,
        figsize=figure_size_inches,
        sharex=False,
        gridspec_kw={"height_ratios": height_ratios},
    )

    draw_distribution(
        axes[0],
        random_values,
        bins,
        xmax,
        color="#C76D5E",
        title="Randomly selected",
        xlabel="Conflict probability",
    )
    draw_distribution(
        axes[1],
        naive_values,
        bins,
        xmax,
        color="#808080",
        title="Naive selected",
        xlabel="Conflict probability",
    )
    draw_distribution(
        axes[2],
        graph_values,
        bins,
        xmax,
        color="#2A9D8F",
        title="Graph selected",
        xlabel="Conflict probability",
    )
    if naive_progress_passed_homodimer is not None:
        draw_progress_overlay(
            axes[3],
            naive_progress_passed_homodimer,
            naive_progress_retained_pairs,
            hybrid_seed_x_values,
            hybrid_seed_pairs_after_vc,
            hybrid_collection_x_values,
            hybrid_collection_pairs_after_vc,
            progress_xmax=progress_xmax,
            fit_eval_points=fit_eval_points,
            fit_linewidth=fit_linewidth,
            fit_zorder=fit_zorder,
            point_zorder=point_zorder,
            point_markersize=point_markersize,
            point_edgewidth=point_edgewidth,
            point_edge_color=point_edge_color,
        )
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.06, top=0.97, hspace=0.40)
    fig.savefig(output_path, format="svg")
    if show_plots:
        plt.show()
    plt.close(fig)


def plot_one_target(
    *,
    module_dir: Path,
    output_dir: Path,
    batch_name: str,
    length_label: str,
    condition_label: str,
    conflict_probability_xmax: float,
    show_plots: bool,
    progress_xmax: float,
    fit_eval_points: int,
    fit_linewidth: float,
    fit_zorder: int,
    point_zorder: int,
    point_markersize: float,
    point_edgewidth: float,
    point_edge_color: str,
) -> None:
    batch_dir = module_dir / "data" / batch_name
    analysis_workbook = (
        batch_dir
        / "auxiliary_analysis"
        / "init900_outside_crossref"
        / f"{length_label}_{condition_label}"
        / "compatibility_analysis.xlsx"
    )
    data_dir = batch_dir / length_label / condition_label
    report_stem = f"{length_label}_{condition_label}_limitm8p16_budget10000000"
    hybrid_report = data_dir / f"hybrid_{report_stem}_init900_seed41.xlsx"
    hybrid_init250_report = data_dir / f"hybrid_{report_stem}_init250_seed41.xlsx"
    hybrid_init450_report = data_dir / f"hybrid_{report_stem}_init450_seed41.xlsx"
    naive_report = data_dir / f"naive_{report_stem}_seed41.xlsx"

    print(f"loading prepared analysis data for {batch_name} / {length_label} / {condition_label}...", flush=True)
    seed_df = pd.read_excel(analysis_workbook, sheet_name="seed_conflict_probability")
    outside_df = pd.read_excel(analysis_workbook, sheet_name="outside_to_inside")
    inside_against_outside_df = pd.read_excel(analysis_workbook, sheet_name="inside_to_outside")
    hybrid_progress_df = pd.read_excel(hybrid_report, sheet_name="search_progress")
    hybrid_init250_progress_df = pd.read_excel(hybrid_init250_report, sheet_name="search_progress")
    hybrid_init450_progress_df = pd.read_excel(hybrid_init450_report, sheet_name="search_progress")
    naive_progress_df = pd.read_excel(naive_report, sheet_name="search_progress")
    print(
        f"loaded seed_rows={len(seed_df)} outside_rows={len(outside_df)} "
        f"inside_rows={len(inside_against_outside_df)}",
        flush=True,
    )

    inside_to_outside_bins, inside_to_outside_xmax = build_shared_bins(
        [
            seed_df["conflict_probability"].to_numpy(dtype=float),
            inside_against_outside_df.loc[
                inside_against_outside_df["set_name"] == "naive_first_m",
                "outside_conflict_probability",
            ].to_numpy(dtype=float),
            inside_against_outside_df.loc[
                inside_against_outside_df["set_name"] == "hybrid_seed_independent",
                "outside_conflict_probability",
            ].to_numpy(dtype=float),
        ],
        bin_count=21,
        xmax=conflict_probability_xmax,
    )

    output_suffix = infer_output_suffix(data_dir)
    inside_to_outside_plot_svg_path = output_dir / f"conf_prob_analysis_{output_suffix}.svg"
    naive_inside_values = inside_against_outside_df.loc[
        inside_against_outside_df["set_name"] == "naive_first_m",
        "outside_conflict_probability",
    ].to_numpy(dtype=float)
    graph_inside_values = inside_against_outside_df.loc[
        inside_against_outside_df["set_name"] == "hybrid_seed_independent",
        "outside_conflict_probability",
    ].to_numpy(dtype=float)
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
        seed_row = progress_df.loc[progress_df["pass"] == "seed", ["pairs_collected", "pairs_after_vc"]].copy()
        seed_row["pairs_collected"] = pd.to_numeric(seed_row["pairs_collected"], errors="coerce")
        seed_row["pairs_after_vc"] = pd.to_numeric(seed_row["pairs_after_vc"], errors="coerce")
        seed_row = seed_row.dropna()
        row = seed_row.iloc[-1]
        hybrid_seed_points.append((float(row["pairs_collected"]), float(row["pairs_after_vc"])))
    hybrid_seed_points = sorted(hybrid_seed_points, key=lambda pair: pair[0])
    hybrid_seed_x_values = np.array([point[0] for point in hybrid_seed_points], dtype=float)
    hybrid_seed_pairs_after_vc = np.array([point[1] for point in hybrid_seed_points], dtype=float)

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
    hybrid_collection_x_values = np.array([point[0] for point in hybrid_collection_points], dtype=float)
    hybrid_collection_pairs_after_vc = np.array([point[1] for point in hybrid_collection_points], dtype=float)

    print(f"writing plot to {inside_to_outside_plot_svg_path}...", flush=True)
    save_stack_plot(
        inside_to_outside_plot_svg_path,
        inside_to_outside_bins,
        inside_to_outside_xmax,
        seed_df["conflict_probability"].to_numpy(dtype=float),
        naive_inside_values,
        graph_inside_values,
        show_plots,
        naive_progress_rows["passed_homodimer"].to_numpy(dtype=float),
        naive_progress_rows["accepted_into_pool"].to_numpy(dtype=float),
        hybrid_seed_x_values,
        hybrid_seed_pairs_after_vc,
        hybrid_collection_x_values,
        hybrid_collection_pairs_after_vc,
        progress_xmax=progress_xmax,
        fit_eval_points=fit_eval_points,
        fit_linewidth=fit_linewidth,
        fit_zorder=fit_zorder,
        point_zorder=point_zorder,
        point_markersize=point_markersize,
        point_edgewidth=point_edgewidth,
        point_edge_color=point_edge_color,
    )
    print(f"wrote_inside_to_outside_plot_svg={inside_to_outside_plot_svg_path}", flush=True)


if __name__ == "__main__":
    conflict_probability_xmax = 0.36
    progress_xmax = 2000.0
    fit_eval_points = 4000
    fit_linewidth = 1.2
    fit_zorder = 4
    point_zorder = 6
    point_markersize = 3.0
    point_edgewidth = 0.35
    point_edge_color = "black"

    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    show_plots = False
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "Arial"
    for batch_name, length_label, condition_label in (
        ("batch_x_TTTT_sigma1p0_seed41", "len12", "5p_TTTT"),
        ("batch_x______sigma1p0_seed41", "len12", "5p_none"),
    ):
        plot_one_target(
            module_dir=module_dir,
            output_dir=output_dir,
            batch_name=batch_name,
            length_label=length_label,
            condition_label=condition_label,
            conflict_probability_xmax=conflict_probability_xmax,
            show_plots=show_plots,
            progress_xmax=progress_xmax,
            fit_eval_points=fit_eval_points,
            fit_linewidth=fit_linewidth,
            fit_zorder=fit_zorder,
            point_zorder=point_zorder,
            point_markersize=point_markersize,
            point_edgewidth=point_edgewidth,
            point_edge_color=point_edge_color,
        )
