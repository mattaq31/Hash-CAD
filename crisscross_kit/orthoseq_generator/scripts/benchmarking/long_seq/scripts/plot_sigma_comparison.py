"""Compare sigma 1.0 and 0.5 in a supplementary PDF with side-by-side extension conditions.

Read saved benchmark reports and preserve the plotting-window aspect ratio of
the canonical sigma 1.0 long-sequence plot used in main-text Figure 3B.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from plot_single_limit_batch import (
    FIGURE_HEIGHT_MM, FIGURE_WIDTH_MM, build_series_specs, collect_runs, compute_shared_y_max,
)


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[1]
    output_dir = module_dir / "plots" / "sigma_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    lengths = [8, 12, 16, 20]
    sigmas = [("1p0", "σ = 1.0", None), ("0p5", "σ = 0.5", "///")]
    targets = [
        ("batch_x_TTTT", "TTTT", "5′ TTTT extension"),
        ("batch_x_____", "none", "No extension"),
    ]
    pair_width = 0.16
    bar_width = pair_width * 0.43
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["hatch.linewidth"] = 0.4
    # Match the axes dimensions after the canonical main-text plot's subplot margins.
    panel_aspect = (FIGURE_HEIGHT_MM * (0.88 - 0.20)) / (FIGURE_WIDTH_MM * (0.98 - 0.18))
    figure_width_mm = 165.1
    left_space_mm = 12.0
    right_space_mm = 1.5
    column_gap_mm = 13.0
    heading_space_mm = 6.5
    bottom_space_mm = 9.0
    panel_width_mm = (figure_width_mm - left_space_mm - right_space_mm - column_gap_mm) / 2
    panel_height_mm = panel_width_mm * panel_aspect
    figure_height_mm = panel_height_mm + heading_space_mm + bottom_space_mm

    runs_by_condition = {}
    for batch_name, condition, title in targets:
        for sigma, label, hatch in sigmas:
            data_root = module_dir / "data" / f"{batch_name}_sigma{sigma}_seed41"
            runs_by_condition[(condition, sigma)] = [
                run for run in collect_runs(data_root) if run["length"] in lengths
            ]
    shared_y_max = compute_shared_y_max([
        run for runs in runs_by_condition.values() for run in runs
    ])

    fig, axes = plt.subplots(1, 2, figsize=(figure_width_mm / 25.4, figure_height_mm / 25.4), sharey=True)
    for column, (batch_name, condition, title) in enumerate(targets):
        series_specs = build_series_specs(runs_by_condition[(condition, "0p5")])
        run_lookup = {
            (sigma, run["length"], run["algorithm"], run["init_count"]): run
            for sigma, label, hatch in sigmas for run in runs_by_condition[(condition, sigma)]
        }
        ax = axes[column]
        ax.set_box_aspect(panel_aspect)
        for cluster_index, length in enumerate(lengths):
            for series_index, spec in enumerate(series_specs):
                position = cluster_index + (series_index - (len(series_specs) - 1) / 2) * pair_width
                for sigma_index, (sigma, label, hatch) in enumerate(sigmas):
                    run = run_lookup[(sigma, length, spec["algorithm"], spec["init_count"])]
                    ax.bar(
                        position + (sigma_index - 0.5) * bar_width, run["found_pair_count"],
                        width=bar_width, facecolor=spec["color"], edgecolor="black",
                        linewidth=0.5, hatch=hatch, zorder=3,
                    )

        legend_handles = [
            Patch(facecolor=spec["color"], edgecolor="black", linewidth=0.5, label=spec["label"])
            for spec in series_specs
        ] + [
            Patch(facecolor="white", edgecolor="black", linewidth=0.5, hatch=hatch, label=label)
            for sigma, label, hatch in sigmas
        ]
        ax.legend(handles=legend_handles, loc="upper right", fontsize=6, frameon=True,
                  facecolor="white", edgecolor="none", framealpha=1, handlelength=1.5,
                  labelspacing=0.15, borderpad=0.25, borderaxespad=0.3)
        ax.set_title(title, fontsize=8, pad=4)
        ax.set_xlabel("Sequence length", fontsize=8, labelpad=2)
        ax.set_ylabel("Number of pairs found", fontsize=8, labelpad=2)
        ax.set_xticks(range(len(lengths)), lengths)
        ax.set_xlim(-0.5, len(lengths) - 0.5)
        ax.set_ylim(0, shared_y_max)
        ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, pad=2, labelleft=True)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="0.85", linewidth=0.4)
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
        ax.text(-0.15, 1.02, "AB"[column], transform=ax.transAxes,
                fontsize=10, ha="left", va="bottom")

    fig.subplots_adjust(left=left_space_mm / figure_width_mm, right=1 - right_space_mm / figure_width_mm,
                        bottom=bottom_space_mm / figure_height_mm, top=1 - heading_space_mm / figure_height_mm,
                        wspace=column_gap_mm / panel_width_mm)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    divider_x = (axes[0].get_tightbbox(renderer).x1 + axes[1].get_tightbbox(renderer).x0) / (2 * fig.bbox.width)
    fig.add_artist(Line2D([divider_x, divider_x], [axes[0].get_position().y0, axes[0].get_position().y1],
                         transform=fig.transFigure, color="black", linewidth=0.6))
    output_path = output_dir / "sigma_comparison.pdf"
    fig.savefig(output_path, format="pdf")
    print(f"Saved: {output_path}")
    print(f"Figure size: {figure_width_mm:.1f} × {figure_height_mm:.2f} mm; "
          f"panel height/width: {panel_aspect:.6f}")
    plt.close(fig)
