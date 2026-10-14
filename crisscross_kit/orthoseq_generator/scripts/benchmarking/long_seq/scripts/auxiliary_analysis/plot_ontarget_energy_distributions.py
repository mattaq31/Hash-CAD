"""Compare saved initial-pool and final 12-mer on-target energies in the canonical two-column layout."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata, load_seed_pairs


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    length = 12
    init_count = 900
    random_seed = 41
    # Keep the same column width and panel spacing as the canonical GC figure, with one additional row.
    upscale = 1.25
    figure_width_mm = 2 * 177.8 * 0.32 * upscale
    panel_height_mm = 38.0 * upscale
    figure_height_mm = 3 * panel_height_mm + 10.0
    hspace = 0.36
    wspace = 0.25
    # Match ON_COLOR in figures/figure_1/plot_figure_1.py, verified against the paper's f1.pdf.
    histogram_color = "#3B6FB6"
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["pdf.fonttype"] = 42
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "5′ TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(figure_width_mm / 25.4, figure_height_mm / 25.4),
                             sharex="col", sharey=True)
    for column, (batch_name, condition, title) in enumerate(targets):
        data_dir = module_dir / "data" / batch_name / f"len{length}" / condition
        report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
        naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
        metadata = load_metadata(hybrid_report)
        min_ontarget = float(metadata["search.min_ontarget"])
        max_ontarget = float(metadata["search.max_ontarget"])
        groups = {
            "Initial random pool": load_seed_pairs(hybrid_report),
            "Hybrid": load_found_pairs(hybrid_report),
            "Naive": load_found_pairs(naive_report),
        }
        # The same bins within each condition make selection shifts directly comparable.
        bin_edges = np.linspace(min_ontarget, max_ontarget, 21)
        margin = (max_ontarget - min_ontarget) * 0.08
        for row, (group_name, pairs_df) in enumerate(groups.items()):
            energies = pairs_df["on_target_energy_verified"].to_numpy(dtype=float)
            ax = axes[row, column]
            ax.hist(energies, bins=bin_edges, density=True, color=histogram_color,
                    edgecolor="black", linewidth=0.35)
            ax.axvline(min_ontarget, color="#2A9D8F", ls="--", lw=1.1, label="On-target range", zorder=4)
            ax.axvline(max_ontarget, color="#2A9D8F", ls="--", lw=1.1, zorder=4)
            ax.axvline(energies.mean(), color="#4F4F4F", lw=1.1,
                       label=f"Mean: {energies.mean():.2f} kcal/mol", zorder=4)
            panel_title = f"{group_name} (n={len(energies)})"
            if row == 0:
                panel_title = f"{title}\n{panel_title}"
            ax.set_title(panel_title, fontsize=8, pad=4)
            ax.set_xlim(min_ontarget - margin, max_ontarget + margin)
            ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, labelbottom=True, labelleft=True)
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
            ax.legend(fontsize=6, frameon=True, facecolor="white", edgecolor="none", framealpha=1,
                      loc="upper left", handlelength=1.4)
            ax.set_ylabel("Density", fontsize=6)
            ax.set_xlabel(r"$\Delta G_{\mathrm{assoc}}$ (kcal/mol)", fontsize=6, labelpad=2)
            print(f"{title}, {group_name}: {len(energies)} pairs; mean={energies.mean():.5f} kcal/mol; "
                  f"allowed window=[{min_ontarget:.5f}, {max_ontarget:.5f}]")

    # Leave space above the histograms for the mean and range labels.
    axes[0, 0].set_ylim(0, axes[0, 0].get_ylim()[1] * 1.25)
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.10, top=0.93, wspace=wspace, hspace=hspace)
    for row, label in enumerate("ABC"):
        axes[row, 0].text(
            -0.16, 1.02, label, transform=axes[row, 0].transAxes,
            fontsize=10, fontfamily="Arial", fontweight="normal", ha="left", va="bottom",
        )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # Keep the divider clear of the right column's complete axis labels and legends.
    left_edge = max(ax.get_tightbbox(renderer).x1 for ax in axes[:, 0])
    right_edge = min(ax.get_tightbbox(renderer).x0 for ax in axes[:, 1])
    divider_x = 0.5 * (left_edge + right_edge) / fig.bbox.width
    fig.add_artist(Line2D(
        [divider_x, divider_x], [axes[-1, 0].get_position().y0, axes[0, 0].get_position().y1],
        transform=fig.transFigure, color="black", linewidth=0.6,
    ))
    output_path = output_dir / f"ontarget_energy_distributions_len{length}_init{init_count}_seed{random_seed}.pdf"
    fig.savefig(output_path, format="pdf")
    print(f"Saved: {output_path}")
    plt.close(fig)
