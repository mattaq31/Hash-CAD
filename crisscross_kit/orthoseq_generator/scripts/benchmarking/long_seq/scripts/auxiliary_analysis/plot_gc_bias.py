"""Plot canonical positional GC fractions for 12-mer benchmark sets, saving only PDF.

Compare hybrid and naive results against the initial random pool, with TTTT
extension on the left and no extension on the right. Average both strands after
excluding fixed extensions. Read saved reports without computing any energies.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
import numpy as np

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata, load_seed_pairs


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    length = 12
    init_count = 900
    random_seed = 41
    # Match the two-column dimensions of the conflict-probability analysis.
    upscale = 1.25
    figure_width_mm = 2 * 177.8 * 0.32 * upscale
    panel_height_mm = 38.0 * upscale
    figure_height_mm = 2 * panel_height_mm + 10.0
    hspace = 0.36
    wspace = 0.25
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["pdf.fonttype"] = 42
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "5′ TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(figure_width_mm / 25.4, figure_height_mm / 25.4),
                             sharex=True, sharey=True)
    positions = np.arange(1, length + 1)
    for column, (batch_name, condition, title) in enumerate(targets):
        data_dir = module_dir / "data" / batch_name / f"len{length}" / condition
        report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
        naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
        metadata = load_metadata(hybrid_report)
        offset = len(metadata.get("input.fivep_ext") or "")
        groups = {
            "Initial random pool": load_seed_pairs(hybrid_report),
            "Hybrid": load_found_pairs(hybrid_report),
            "Naive": load_found_pairs(naive_report),
        }
        profiles = {}
        for group_name, pairs_df in groups.items():
            # Pool both orientations so canonical strand ordering does not introduce positional bias.
            cores = [seq[offset:offset + length] for strand in ["seq", "rc_seq"] for seq in pairs_df[strand]]
            profiles[group_name] = np.array([[base in "GC" for base in core] for core in cores]).mean(axis=0)

        for row, (group_name, color) in enumerate([
            ("Hybrid", "#3B6FB6"), ("Naive", "#009E73"),
        ]):
            ax = axes[row, column]
            ax.plot(positions, profiles[group_name], "o-", color=color, label=group_name, lw=1.3, ms=2.5)
            ax.plot(positions, profiles["Initial random pool"], "o--", color="0.5",
                    label="Initial random pool", lw=1.1, ms=2.5)
            ax.axhline(0.5, color="0.8", lw=0.7, ls=":", zorder=0)
            panel_title = f"{group_name} (n={len(groups[group_name])})"
            if row == 0:
                panel_title = f"{title}\n{panel_title}"
            ax.set_title(panel_title, fontsize=8, pad=4)
            ax.set_xticks(positions)
            ax.set_ylim(0.20, 0.90)
            ax.set_yticks(np.arange(0.20, 0.91, 0.10))
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
            ax.set_ylabel("GC fraction", fontsize=6)
            ax.set_xlabel("Core base position", fontsize=6, labelpad=2)
            ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, labelbottom=True, labelleft=True)
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
            ax.legend(fontsize=6, frameon=True, facecolor="white", edgecolor="none", framealpha=1,
                      handlelength=1.4)

    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.15, top=0.90, wspace=wspace, hspace=hspace)
    for row, label in enumerate("AB"):
        axes[row, 0].text(
            -0.16, 1.02, label, transform=axes[row, 0].transAxes,
            fontsize=10, fontfamily="Arial", fontweight="normal", ha="left", va="bottom",
        )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # Place the divider between complete panels, clear of the right column's y-axis labels.
    left_edge = max(ax.get_tightbbox(renderer).x1 for ax in axes[:, 0])
    right_edge = min(ax.get_tightbbox(renderer).x0 for ax in axes[:, 1])
    divider_x = 0.5 * (left_edge + right_edge) / fig.bbox.width
    fig.add_artist(Line2D(
        [divider_x, divider_x], [axes[-1, 0].get_position().y0, axes[0, 0].get_position().y1],
        transform=fig.transFigure, color="black", linewidth=0.6,
    ))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"gc_fraction_len{length}_init{init_count}_seed{random_seed}.pdf"
    fig.savefig(output_path, format="pdf")
    print(f"Saved: {output_path}")
    plt.close(fig)
