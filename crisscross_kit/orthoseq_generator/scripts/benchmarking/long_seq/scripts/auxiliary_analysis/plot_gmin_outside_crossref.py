"""Extend the SI conflict-probability figure with GMIN using the saved outside-pool comparisons."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_init900_outside_crossref import build_shared_bins, draw_distribution, draw_progress_overlay


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    conflict_probability_xmax = 0.36
    progress_xmax = 2550.0
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "5′ TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]
    plt.rcParams["font.family"] = "Arial"
    fig, axes = plt.subplots(
        5, 2, figsize=(7, 12), gridspec_kw={"height_ratios": [1, 1, 1, 1, 1.4]},
    )

    for column, (batch_name, condition, condition_title) in enumerate(targets):
        batch_dir = module_dir / "data" / batch_name
        analysis_path = (
            batch_dir / "auxiliary_analysis" / "init900_outside_crossref"
            / f"len12_{condition}" / "compatibility_analysis_gmin.xlsx"
        )
        seed_df = pd.read_excel(analysis_path, sheet_name="seed_conflict_probability")
        inside_df = pd.read_excel(analysis_path, sheet_name="inside_to_outside")
        distributions = [("Randomly selected", seed_df["conflict_probability"].to_numpy(), "#C76D5E")]
        for set_name, title, color in [
            ("naive_first_m", "Naive selected", "#808080"),
            ("hybrid_seed_independent", "GMAX selected", "#2A9D8F"),
            ("gmin_seed_independent", "GMIN selected", "#0072B2"),
        ]:
            values = inside_df.loc[inside_df["set_name"] == set_name, "outside_conflict_probability"].to_numpy()
            distributions.append((title, values, color))
        bins, xmax = build_shared_bins(
            [values for _, values, _ in distributions], bin_count=21, xmax=conflict_probability_xmax,
        )
        for row, (title, values, color) in enumerate(distributions):
            draw_distribution(
                axes[row, column], values, bins, xmax, color=color,
                title=f"{title} (n={len(values)})", xlabel="Conflict probability",
            )
        axes[0, column].set_title(f"{condition_title}\nRandomly selected (n={len(seed_df)})", fontsize=8)

        # The progress panel remains the original GMAX/naive benchmark, not a GMIN search trajectory.
        data_dir = batch_dir / "len12" / condition
        report_stem = f"len12_{condition}_limitm8p16_budget10000000"
        naive_progress_df = pd.read_excel(
            data_dir / f"naive_{report_stem}_seed41.xlsx", sheet_name="search_progress",
        )
        naive_rows = naive_progress_df.loc[
            naive_progress_df["pass"] == "naive", ["passed_homodimer", "accepted_into_pool"],
        ].apply(pd.to_numeric, errors="coerce").dropna().sort_values("passed_homodimer")
        seed_points = []
        collection_points = []
        for init_count in [250, 450, 900, 2500]:
            report_path = data_dir / f"hybrid_{report_stem}_init{init_count}_seed41.xlsx"
            if not report_path.exists():
                continue
            progress_df = pd.read_excel(report_path, sheet_name="search_progress")
            for pass_name, points in [("seed", seed_points), ("collection", collection_points)]:
                rows = progress_df.loc[
                    progress_df["pass"] == pass_name, ["pairs_collected", "pairs_after_vc"],
                ].apply(pd.to_numeric, errors="coerce").dropna()
                if not rows.empty:
                    points.append(tuple(rows.iloc[-1]))
        seed_points = np.array(sorted(seed_points), dtype=float).reshape(-1, 2)
        collection_points = np.array(sorted(collection_points), dtype=float).reshape(-1, 2)
        draw_progress_overlay(
            axes[4, column],
            naive_rows["passed_homodimer"].to_numpy(), naive_rows["accepted_into_pool"].to_numpy(),
            seed_points[:, 0], seed_points[:, 1], collection_points[:, 0], collection_points[:, 1],
            progress_xmax=progress_xmax, fit_eval_points=4000, fit_linewidth=1.2, fit_zorder=4,
            point_zorder=6, point_markersize=3.0, point_edgewidth=0.35, point_edge_color="black",
        )
        axes[4, column].set_title("Original GMAX / naive progress", fontsize=8)

    # Shared scales within each row make the two extension conditions directly comparable.
    for row in range(5):
        ymax = max(ax.get_ylim()[1] for ax in axes[row])
        for ax in axes[row]:
            ax.set_ylim(0, ymax)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.05, top=0.96, hspace=0.65, wspace=0.35)
    output_path = output_dir / "conf_prob_analysis_with_gmin_len12.pdf"
    fig.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close(fig)
