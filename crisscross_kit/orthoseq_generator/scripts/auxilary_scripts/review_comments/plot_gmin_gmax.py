"""Plot retained set sizes for the two prune fractions in the GMIN/GMAX scouting experiment."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


if __name__ == "__main__":
    experiment_dir = Path(__file__).resolve().parent / "results" / "length_init_count_prune_screen"
    result_path = experiment_dir / "batch_x_TTTT_sigma1p0_seed41_gmin_gmax_screen_20260929_202245.xlsx"
    output_dir = experiment_dir / "figures" / result_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    results_df = pd.read_excel(result_path, sheet_name="results")
    lengths = sorted(results_df["length"].unique())
    init_counts = sorted(results_df["init_count"].unique())
    prune_fractions = sorted(results_df["prune_fraction"].dropna().unique())
    algorithms = {
        "gmin_iterative": "Gmin\nrand",
        "gmin_overlap_iterative": "Gmin\nover",
        "gmax_random_iterative": "Gmax\nrand",
        "gmax_iterative": "Gmax\nover",
        "exact": "CP\nSAT",
    }
    colors = list(plt.get_cmap("tab20").colors[:4]) + ["0.55"]
    bar_width = 0.8 / len(algorithms)

    for prune_fraction in prune_fractions:
        fraction_df = results_df[
            (results_df["prune_fraction"] == prune_fraction) | (results_df["algorithm"] == "exact")
        ]
        fig, axes = plt.subplots(
            (len(lengths) + 1) // 2, 2, figsize=(18, 6 * ((len(lengths) + 1) // 2)), squeeze=False,
        )
        for ax, length in zip(axes.flat, lengths):
            bar_positions = []
            bar_labels = []
            for cluster_index, init_count in enumerate(init_counts):
                graph_df = fraction_df[
                    (fraction_df["length"] == length) & (fraction_df["init_count"] == init_count)
                ]
                for index, algorithm in enumerate(algorithms):
                    runs_df = graph_df[graph_df["algorithm"] == algorithm]
                    if runs_df.empty:
                        continue
                    values = runs_df["retained_pair_count"]
                    mean = values.mean()
                    position = cluster_index + (index - (len(algorithms) - 1) / 2) * bar_width
                    unproved = algorithm == "exact" and runs_df["optimal"].iloc[0] != True
                    bar_positions.append(position)
                    bar_labels.append(algorithms[algorithm] + ("*" if unproved else ""))
                    ax.bar(
                        position, mean, width=bar_width * 0.9, color=colors[index],
                        edgecolor="0.25", linewidth=0.4,
                        yerr=[[mean - values.min()], [values.max() - mean]],
                        capsize=2, error_kw={"elinewidth": 0.8},
                    )
                ax.text(
                    cluster_index, -0.18, f"Initial count\n{init_count}",
                    transform=ax.get_xaxis_transform(), ha="center", fontsize=10,
                )

            ax.set_title(f"Length {length}")
            ax.set_xticks(bar_positions, bar_labels, rotation=0, fontsize=8)
            ax.set_ylabel("Retained pairs")
            ax.set_xlim(-0.55, len(init_counts) - 0.45)
            # Use identical limits for a given length in both prune-fraction figures.
            length_values = results_df.loc[
                (results_df["length"] == length) & results_df["algorithm"].isin(algorithms), "retained_pair_count",
            ]
            ax.set_ylim(0, length_values.max() * 1.12)
            ax.set_axisbelow(True)
            ax.grid(axis="y", alpha=0.2)

        for ax in list(axes.flat)[len(lengths):]:
            ax.set_visible(False)
        fig.suptitle(
            f"Iterative and CP-SAT — prune fraction {prune_fraction:g}\nBars: means; whiskers: minimum–maximum across seeds",
            fontsize=14,
        )
        fig.text(0.5, 0.01, "over: overlap; *: CP-SAT optimality unproved", ha="center")
        fig.tight_layout(rect=(0, 0.035, 1, 0.93))
        output_path = output_dir / f"prune_{prune_fraction:g}_retained_pair_count.pdf"
        fig.savefig(output_path, dpi=200)
        print(f"Saved: {output_path}")
        plt.close(fig)
