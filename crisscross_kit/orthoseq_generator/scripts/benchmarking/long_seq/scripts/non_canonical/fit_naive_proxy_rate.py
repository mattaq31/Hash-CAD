#!/usr/bin/env python3
"""
Fit an old naive-search trajectory after proxy-rescaling its x-axis.

The old naive workbook stores only raw `attempt` counts in `search_progress`.
This script borrows the upstream homodimer-pass throughput from a newer hybrid
run, rescales the naive attempt axis as

    t = rho_homodimer * attempts

and then fits

    s(t) = (1 / k) * ln(1 + k * t)

to the cumulative accepted-pair trajectory. The local slope at a target set
size is reported as a provisional acceptance-rate estimate.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MODULE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_NAIVE_REPORT = MODULE_DIR / "data" / "non_canonical" / "naive_len16_5p_none_limitm8p16_seed41.xlsx"
DEFAULT_HYBRID_REPORT = MODULE_DIR / "data" / "non_canonical" / "ortho_16mers8p16_new_sheettest7.xlsx"
DEFAULT_OUTPUT_DIR = MODULE_DIR / "data" / "non_canonical"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit the old naive trajectory using a hybrid-derived throughput proxy."
    )
    parser.add_argument(
        "--naive-report",
        type=Path,
        default=DEFAULT_NAIVE_REPORT,
        help="Old naive workbook with raw-attempt trajectory.",
    )
    parser.add_argument(
        "--hybrid-report",
        type=Path,
        default=DEFAULT_HYBRID_REPORT,
        help="New hybrid workbook used to estimate homodimer-pass throughput.",
    )
    parser.add_argument(
        "--target-size",
        type=float,
        default=44.0,
        help="Set size at which to evaluate the fitted local rate.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the saved plot.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the plot window.",
    )
    return parser.parse_args()


def load_search_progress(report_path: Path) -> pd.DataFrame:
    """Load the `search_progress` sheet from one benchmark workbook."""
    return pd.read_excel(report_path, sheet_name="search_progress")


def extract_hybrid_throughputs(progress_df: pd.DataFrame) -> dict[str, float]:
    """Estimate homodimer-pass throughput for each hybrid search phase."""
    required = {"pass", "attempts", "passed_homodimer", "accepted_into_pool"}
    if not required.issubset(progress_df.columns):
        missing = required - set(progress_df.columns)
        raise ValueError(f"Hybrid search_progress is missing required columns: {sorted(missing)}")

    rows = progress_df.copy()
    rows["attempts"] = pd.to_numeric(rows["attempts"], errors="coerce")
    rows["passed_homodimer"] = pd.to_numeric(rows["passed_homodimer"], errors="coerce")
    rows = rows.dropna(subset=["pass", "attempts", "passed_homodimer"])
    rows = rows.loc[rows["attempts"] > 0].copy()
    if rows.empty:
        raise ValueError("Hybrid search_progress does not contain valid throughput rows.")

    throughput_by_pass = {}
    for pass_name in ("seed", "collection"):
        subset = rows.loc[rows["pass"] == pass_name]
        if subset.empty:
            continue
        row = subset.iloc[-1]
        throughput_by_pass[pass_name] = float(row["passed_homodimer"] / row["attempts"])

    total_attempts = float(rows["attempts"].sum())
    total_passed_homodimer = float(rows["passed_homodimer"].sum())
    throughput_by_pass["pooled"] = float(total_passed_homodimer / total_attempts)
    return throughput_by_pass


def extract_naive_trajectory(progress_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize old and new naive progress formats into one accepted-pair trajectory."""
    if {"step", "attempt", "pairs_found"}.issubset(progress_df.columns):
        rows = progress_df.loc[progress_df["step"] == "accepted_pair", ["attempt", "pairs_found"]].copy()
        rows["attempt"] = pd.to_numeric(rows["attempt"], errors="coerce")
        rows["pairs_found"] = pd.to_numeric(rows["pairs_found"], errors="coerce")
        rows = rows.dropna(subset=["attempt", "pairs_found"]).sort_values("attempt").reset_index(drop=True)
        rows = rows.rename(columns={"attempt": "raw_attempts", "pairs_found": "pairs_found"})
    elif {"attempts", "accepted_into_pool", "pass"}.issubset(progress_df.columns):
        rows = progress_df.loc[progress_df["pass"] == "naive", ["attempts", "accepted_into_pool"]].copy()
        rows["attempts"] = pd.to_numeric(rows["attempts"], errors="coerce")
        rows["accepted_into_pool"] = pd.to_numeric(rows["accepted_into_pool"], errors="coerce")
        rows = rows.dropna(subset=["attempts", "accepted_into_pool"]).sort_values("attempts").reset_index(drop=True)
        rows = rows.rename(columns={"attempts": "raw_attempts", "accepted_into_pool": "pairs_found"})
    else:
        raise ValueError("Naive search_progress has an unsupported format.")

    if rows.empty:
        raise ValueError("Naive search_progress does not contain accepted-pair trajectory rows.")

    origin = pd.DataFrame({"raw_attempts": [0.0], "pairs_found": [0.0]})
    rows = pd.concat([origin, rows], ignore_index=True)
    rows["raw_attempts"] = rows["raw_attempts"].astype(float)
    rows["pairs_found"] = rows["pairs_found"].astype(float)
    return rows


def fit_log_model(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """
    Fit the one-parameter homogeneous-product model.

    The fitted curve is

        s(t) = (1 / k) * ln(1 + k * t)

    where `k > 0` is chosen by grid search with iterative refinement.
    """
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("Need at least three trajectory points to fit the log model.")
    if np.any(x < 0.0) or np.any(y < 0.0):
        raise ValueError("Trajectory values must be non-negative.")

    xmax = float(np.max(x))
    ymax = float(np.max(y))
    if xmax <= 0.0 or ymax <= 0.0:
        raise ValueError("Trajectory must extend beyond the origin to fit the log model.")

    log_b_low = math.log(max(xmax * 1e-6, 1e-12))
    log_b_high = math.log(max(xmax * 1e3, 1e-9))

    best_k = float("nan")
    best_sse = float("inf")

    for _ in range(8):
        k_grid = np.exp(np.linspace(log_b_low, log_b_high, 120))
        sse_values = np.empty(len(k_grid), dtype=float)
        for idx, k_value in enumerate(k_grid):
            y_hat = np.log1p(k_value * x) / k_value
            residual = y - y_hat
            sse_values[idx] = float(np.dot(residual, residual))

        best_idx = int(np.argmin(sse_values))
        best_k = float(k_grid[best_idx])
        best_sse = float(sse_values[best_idx])

        b_step = (log_b_high - log_b_low) / max(len(k_grid) - 1, 1)
        best_log_b = math.log(best_k)
        log_b_low = best_log_b - 3.0 * b_step
        log_b_high = best_log_b + 3.0 * b_step

    return best_k, best_sse


def evaluate_log_model(k_value: float, x: np.ndarray) -> np.ndarray:
    """Evaluate the homogeneous-product trajectory model at the given x values."""
    return np.log1p(k_value * x) / k_value


def slope_at_target_size(k_value: float, target_size: float) -> float:
    """Return the local acceptance rate implied by the model at set size `target_size`."""
    return float(math.exp(-k_value * target_size))


def effective_conflict_probability(k_value: float) -> float:
    """Convert the fitted burden parameter into an implied pair-conflict probability."""
    return float(1.0 - math.exp(-k_value))


def x_at_target_size(k_value: float, target_size: float) -> float:
    """Invert the fitted model to obtain proxy x at the requested set size."""
    return float(math.expm1(k_value * target_size) / k_value)


def extract_hybrid_empirical_rate(progress_df: pd.DataFrame) -> float | None:
    """Read the collection-pass empirical acceptance rate from a hybrid workbook."""
    required = {"pass", "passed_homodimer", "accepted_into_pool"}
    if not required.issubset(progress_df.columns):
        return None

    rows = progress_df.loc[progress_df["pass"] == "collection"].copy()
    if rows.empty:
        return None

    row = rows.iloc[-1]
    passed_homodimer = pd.to_numeric(row.get("passed_homodimer"), errors="coerce")
    accepted_into_pool = pd.to_numeric(row.get("accepted_into_pool"), errors="coerce")
    if pd.isna(passed_homodimer) or pd.isna(accepted_into_pool) or passed_homodimer <= 0:
        return None
    return float(accepted_into_pool / passed_homodimer)


def plot_proxy_fit(
    trajectory_df: pd.DataFrame,
    fit_results: dict[str, dict[str, float]],
    target_size: float,
    empirical_rate: float | None,
    output_path: Path,
    *,
    show: bool,
) -> None:
    """Plot the proxy-scaled naive trajectory and the pooled homogeneous fit."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.8, 5.0))

    pooled = fit_results["pooled"]
    x_values = trajectory_df["proxy_passed_homodimer"].to_numpy(dtype=float)
    y_values = trajectory_df["pairs_found"].to_numpy(dtype=float)
    ax.scatter(
        x_values,
        y_values,
        s=26,
        color="#264653",
        alpha=0.85,
        label="Naive trajectory (proxy x-axis)",
    )

    x_grid_max = max(float(np.max(x_values)), pooled["x_at_target_size"]) * 1.05
    x_grid = np.linspace(0.0, x_grid_max, 600)
    y_grid = evaluate_log_model(pooled["k"], x_grid)
    ax.plot(x_grid, y_grid, color="#E76F51", linewidth=2.0, label="Pooled-rho fit")

    ax.axhline(target_size, color="#6C757D", linewidth=1.2, linestyle="--")
    ax.axvline(pooled["x_at_target_size"], color="#6C757D", linewidth=1.2, linestyle="--")
    ax.scatter(
        [pooled["x_at_target_size"]],
        [target_size],
        color="#E76F51",
        s=34,
        zorder=3,
    )

    summary_lines = [
        f"target size = {target_size:.0f}",
        f"pooled rho = {pooled['rho']:.4f}",
        f"fit: s(t) = (1/{pooled['k']:.3e}) ln(1 + {pooled['k']:.3e} t)",
        f"rate at {target_size:.0f} = {pooled['rate_at_target_size']:.3e}",
    ]
    if empirical_rate is not None:
        summary_lines.append(f"hybrid empirical = {empirical_rate:.3e}")
    summary_lines.append(
        f"rho range = [{fit_results['seed']['rho']:.4f}, {fit_results['collection']['rho']:.4f}]"
    )
    ax.text(
        0.98,
        0.02,
        "\n".join(summary_lines),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#CCCCCC", "boxstyle": "round,pad=0.3"},
    )

    ax.set_title("Naive trajectory with hybrid-derived proxy x-axis")
    ax.set_xlabel("Estimated homodimer-passed candidates")
    ax.set_ylabel("Accepted pairs")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def build_fit_result(
    rho: float,
    raw_attempts: np.ndarray,
    pairs_found: np.ndarray,
    target_size: float,
) -> dict[str, float]:
    """Fit one proxy-scaled trajectory and package the derived summary values."""
    proxy_x = rho * raw_attempts
    k_value, sse = fit_log_model(proxy_x, pairs_found)
    return {
        "rho": rho,
        "k": k_value,
        "sse": sse,
        "x_at_target_size": x_at_target_size(k_value, target_size),
        "rate_at_target_size": slope_at_target_size(k_value, target_size),
    }


def print_fit_summary(
    fit_results: dict[str, dict[str, float]],
    naive_trajectory_df: pd.DataFrame,
    target_size: float,
    hybrid_empirical_rate: float | None,
    output_dir: Path,
) -> None:
    """Emit the compact text summary consumed by the exploratory workflow."""
    pooled = fit_results["pooled"]
    print(f"target_size={target_size:.0f}")
    print(f"naive_accepted_pair_count={int(naive_trajectory_df['pairs_found'].max())}")
    print(f"hybrid_seed_throughput={fit_results['seed']['rho']:.6f}")
    print(f"hybrid_collection_throughput={fit_results['collection']['rho']:.6f}")
    print(f"hybrid_pooled_throughput={pooled['rho']:.6f}")
    print(f"pooled_fit_k={pooled['k']:.6f}")
    print(f"pooled_estimated_x_at_target_size={pooled['x_at_target_size']:.6f}")
    print(f"pooled_rate_at_target_size={pooled['rate_at_target_size']:.6e}")
    print(
        "pooled_effective_conflict_probability="
        f"{effective_conflict_probability(pooled['k']):.6e}"
    )
    print(
        "rate_at_target_size_range="
        f"[{fit_results['seed']['rate_at_target_size']:.6e}, "
        f"{fit_results['collection']['rate_at_target_size']:.6e}]"
    )
    if hybrid_empirical_rate is not None:
        print(f"hybrid_empirical_acceptance_rate={hybrid_empirical_rate:.6e}")
    print("plots_ready=1")
    print(f"plots_saved_in={output_dir}")


def main() -> None:
    args = parse_args()
    naive_progress_df = load_search_progress(args.naive_report)
    hybrid_progress_df = load_search_progress(args.hybrid_report)

    throughputs = extract_hybrid_throughputs(hybrid_progress_df)
    naive_trajectory_df = extract_naive_trajectory(naive_progress_df)
    hybrid_empirical_rate = extract_hybrid_empirical_rate(hybrid_progress_df)

    raw_attempts = naive_trajectory_df["raw_attempts"].to_numpy(dtype=float)
    pairs_found = naive_trajectory_df["pairs_found"].to_numpy(dtype=float)
    fit_results = {
        label: build_fit_result(throughputs[label], raw_attempts, pairs_found, args.target_size)
        for label in ("seed", "collection", "pooled")
    }

    naive_trajectory_df = naive_trajectory_df.copy()
    naive_trajectory_df["proxy_passed_homodimer"] = (
        fit_results["pooled"]["rho"] * naive_trajectory_df["raw_attempts"].to_numpy(dtype=float)
    )

    output_path = args.output_dir / f"{args.naive_report.stem}_proxy_fit.png"
    plot_proxy_fit(
        naive_trajectory_df,
        fit_results,
        args.target_size,
        hybrid_empirical_rate,
        output_path,
        show=not args.no_show,
    )

    print_fit_summary(
        fit_results,
        naive_trajectory_df,
        args.target_size,
        hybrid_empirical_rate,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
