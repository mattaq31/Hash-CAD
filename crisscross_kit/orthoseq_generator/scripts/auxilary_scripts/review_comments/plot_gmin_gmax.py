"""Plot paired GMIN/GMAX comparisons at the final 178 mm supplementary-figure width."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.legend_handler import HandlerTuple
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


if __name__ == "__main__":
    experiment_dir = Path(__file__).resolve().parent / "results" / "gmin_gmax_37C"
    output_dir = Path(__file__).resolve().parent / "plots" / "gmin_gmax_37C"
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["hatch.linewidth"] = 0.4
    algorithms = {
        "gmin_random": "rand",
        "gmin_rank": "rank",
        "gmin_rule": "rule",
        "gmax_random": "rand",
        "gmax_rank": "rank",
        "gmax_rule": "rule",
    }
    colors = ["#9ECAE1", "#4292C6", "#08519C", "#FDBE85", "#FD8D3C", "#D94701"]
    pair_width = 0.88 / len(algorithms)
    bar_width = pair_width * 0.43
    legend_handles = [
        tuple(Patch(facecolor=color, edgecolor="black", linewidth=0.35) for color in colors[:3]),
        tuple(Patch(facecolor=color, edgecolor="black", linewidth=0.35) for color in colors[3:]),
        Patch(facecolor="white", edgecolor="black", linewidth=0.35, hatch="///", label="Bare"),
        Patch(facecolor="white", edgecolor="black", linewidth=0.35, label="Iterative"),
    ]

    for condition, condition_title in [("TTTT", "TTTT extension"), ("none", "No extension")]:
        results_df = pd.concat([
            pd.read_excel(path, sheet_name="results")
            for path in sorted(experiment_dir.glob(f"gmin_gmax_len*_5p_{condition}.xlsx"))
        ], ignore_index=True)
        lengths = sorted(results_df["length"].unique())
        init_counts = sorted(results_df["init_count"].unique())
        summary = results_df.groupby(["length", "init_count", "algorithm"])["retained_pair_count"].agg(
            ["mean", "std"]
        )
        mean_counts = summary["mean"].unstack("algorithm")
        mean_gaps = pd.DataFrame(index=list(algorithms))
        for mode, suffix in [("Bare", ""), ("Iterative", "_iterative")]:
            mode_means = mean_counts[[algorithm + suffix for algorithm in algorithms]]
            # Give each graph equal weight and compare within the same refinement mode.
            best_means = mode_means.max(axis=1)
            mean_gaps[mode] = (100 * mode_means.rsub(best_means, axis=0).div(best_means, axis=0)).mean().to_numpy()
        for page_start in range(0, len(lengths), 6):
            page_lengths = lengths[page_start:page_start + 6]
            fig, axes = plt.subplots(3, 2, figsize=(178 / 25.4, 162 / 25.4))
            for ax, length in zip(axes.flat, page_lengths):
                bar_positions = []
                bar_labels = []
                for cluster_index, init_count in enumerate(init_counts):
                    for index, (algorithm, label) in enumerate(algorithms.items()):
                        position = cluster_index + (index - (len(algorithms) - 1) / 2) * pair_width
                        for mode_index, (suffix, hatch) in enumerate([("", "///"), ("_iterative", None)]):
                            values = summary.loc[(length, init_count, algorithm + suffix)]
                            offset = (mode_index - 0.5) * bar_width
                            ax.bar(
                                position + offset, values["mean"], width=bar_width, color=colors[index],
                                hatch=hatch, edgecolor="black", linewidth=0.3, yerr=values["std"],
                                capsize=1, error_kw={"elinewidth": 0.5, "capthick": 0.5},
                            )
                        bar_positions.append(position)
                        bar_labels.append(label)
                    cluster_summary = summary.loc[(length, init_count)]
                    cluster_top = (cluster_summary["mean"] + cluster_summary["std"]).max()
                    ax.annotate(f"Vertices = {init_count}", xy=(cluster_index, cluster_top),
                                xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=6)

                length_summary = summary.loc[length]
                ymax = (length_summary["mean"] + length_summary["std"]).max()
                ax.set_ylim(0, np.ceil(ymax * 1.35))
                ax.set_xlim(-0.5, len(init_counts) - 0.5)
                ax.set_title(f"{length}-mers", fontsize=8, pad=4)
                ax.set_box_aspect(1 / 2)
                ax.set_xticks(bar_positions, bar_labels, rotation=0, ha="center")
                ax.set_xlabel("Algorithm variant", fontsize=8, labelpad=2)
                ax.set_ylabel("Number of pairs found", fontsize=8, labelpad=2)
                ax.set_axisbelow(True)
                ax.grid(axis="y", color="0.85", linewidth=0.4)
                ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, pad=1)
                for tick_label in ax.get_xticklabels():
                    tick_label.set_fontfamily("Arial Narrow")
                ax.legend(handles=legend_handles, labels=["GMIN", "GMAX", "Bare", "Iterative"],
                          handler_map={tuple: HandlerTuple(ndivide=None, pad=0.15)},
                          loc="upper left", ncol=2, frameon=False,
                          fontsize=6, handlelength=3, handleheight=1.1, columnspacing=0.8,
                          borderaxespad=0.4, labelspacing=0.3)
                for spine in ax.spines.values():
                    spine.set_linewidth(0.5)

            for ax in list(axes.flat)[len(page_lengths):]:
                ax.set_visible(False)
            if page_start + len(page_lengths) == len(lengths) and len(page_lengths) < axes.size:
                ax = axes.flat[len(page_lengths)]
                ax.set_visible(True)
                ax.set_axis_off()
                ax.set_box_aspect(1 / 2)
                ax.set_title("Average percentage gap to best", fontsize=8, pad=4, y=0.79)
                for table_index, mode in enumerate(["Bare", "Iterative"]):
                    left = table_index * 0.52
                    ax.text(left + 0.24, 0.76, mode, transform=ax.transAxes, fontsize=7,
                            ha="center", va="top")
                    table_rows = [
                        [f"{algorithm.split('_')[0].upper()} {algorithms[algorithm]}", f"{gap:.2f}%"]
                        for algorithm, gap in mean_gaps[mode].sort_values(kind="stable").items()
                    ]
                    table = ax.table(cellText=table_rows, colLabels=["Variant", "Gap (%)"],
                                     cellLoc="center", colWidths=[0.65, 0.35], bbox=[left, -0.01, 0.48, 0.66])
                    table.auto_set_font_size(False)
                    table.set_fontsize(6)
                    for (row, column), cell in table.get_celld().items():
                        cell.set_edgecolor("0.8")
                        cell.set_linewidth(0.4)
                        if row == 0:
                            cell.set_facecolor("0.94")
            fig.suptitle(f"GMIN vs GMAX ({condition_title})", fontsize=10, y=0.985)
            # Physical panel dimensions stay identical on every page, including the final partial page.
            fig.subplots_adjust(left=0.065, right=0.995, bottom=0.075, top=0.94, wspace=0.14, hspace=0.26)
            output_path = output_dir / f"paired_5p_{condition}_page{page_start // 6 + 1}.pdf"
            fig.canvas.draw()
            content_bbox = fig.get_tightbbox(fig.canvas.get_renderer())
            # Crop only vertically so all exports retain the same physical width.
            export_bbox = Bbox.from_extents(0, content_bbox.y0 - 0.04, fig.get_figwidth(), content_bbox.y1 + 0.04)
            fig.savefig(output_path, bbox_inches=export_bbox)
            print(f"Saved: {output_path}")
            plt.close(fig)
