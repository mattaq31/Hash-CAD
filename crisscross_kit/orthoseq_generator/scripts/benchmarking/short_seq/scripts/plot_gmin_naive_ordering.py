"""Compare GMAX/GMIN and naive ordering in paired extension panels, saving mean ± SD figures with review data."""

from pathlib import Path

import pandas as pd

import plot_batch_benchmark as batch_plot
from plot_batch_benchmark import LEGEND_FONT_SIZE, MM_PER_INCH, build_summary_table, compute_plot_y_max
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

from orthoseq_generator.search_report_reader import load_metadata
from orthoseq_generator.algorithm_names import normalize_algorithm_name


FIGURE_WIDTH_MM = 165.1  # The SI's 6.5-inch text width leaves the normal one-inch margins on letter paper.
FIGURE_HEIGHT_MM = 65.0


def plot_comparison(summary_df, series_specs):
    """Place both extension conditions side by side with matching scales, y-labels and in-panel legends."""
    fig, axes = plt.subplots(
        1, 2, figsize=(FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH),
    )
    y_max = compute_plot_y_max(summary_df)
    lengths = sorted(summary_df["length"].unique())
    densities = sorted(summary_df["target_conflict_density"].unique())
    bar_width, subgroup_gap, length_gap = 0.45, 0.3, 0.9
    bars_per_length = len(densities) * len(series_specs)
    for ax, has_tttt5p in zip(axes, (False, True)):
        subset = summary_df.loc[summary_df["has_tttt5p"] == has_tttt5p]
        if subset.empty:
            raise ValueError(f"No comparison results for has_tttt5p={has_tttt5p}.")
        indexed = subset.set_index(["length", "target_conflict_density", "plot_series_key"])
        length_centers = []
        for length_idx, length in enumerate(lengths):
            length_start = length_idx * (bars_per_length * bar_width + len(densities) * subgroup_gap + length_gap)
            length_centers.append(
                length_start + 0.5 * ((bars_per_length - 1) * bar_width + (len(densities) - 1) * subgroup_gap)
            )
            for density_idx, density in enumerate(densities):
                subgroup_start = length_start + density_idx * (len(series_specs) * bar_width + subgroup_gap)
                subgroup_max = 0.0
                for series_idx, spec in enumerate(series_specs):
                    values = indexed.loc[(length, density, spec["key"])]
                    mean_value = float(values["mean_found_pair_count"])
                    std_value = float(values["std_found_pair_count"])
                    subgroup_max = max(subgroup_max, mean_value + std_value)
                    ax.bar(
                        subgroup_start + series_idx * bar_width, mean_value, width=bar_width, yerr=std_value,
                        capsize=1, color=spec["color"], edgecolor="black", linewidth=batch_plot.BAR_EDGE_LINEWIDTH,
                        error_kw={"elinewidth": batch_plot.ERRORBAR_LINEWIDTH,
                                  "capthick": batch_plot.ERRORBAR_LINEWIDTH},
                        label=spec["label"] if length_idx == 0 and density_idx == 0 else None,
                    )
                label_y = min(y_max * 0.98, subgroup_max + y_max * 0.10)
                ax.text(
                    subgroup_start + 0.5 * ((len(series_specs) - 1) * bar_width), label_y, f"{density:.1f}",
                    ha="center", va="top", fontsize=batch_plot.DENSITY_LABEL_FONT_SIZE,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
                )
        ax.set_title(batch_plot.GROUP_TITLES[has_tttt5p], fontsize=batch_plot.TITLE_FONT_SIZE, pad=6)
        ax.set_xlabel("Sequence length", fontsize=batch_plot.AXIS_LABEL_FONT_SIZE)
        ax.set_ylabel("Number of pairs found", fontsize=batch_plot.AXIS_LABEL_FONT_SIZE)
        ax.set_xticks(length_centers, [str(length) for length in lengths], fontsize=batch_plot.TICK_LABEL_FONT_SIZE)
        ax.set_ylim(0, y_max)
        ax.tick_params(axis="y", labelsize=batch_plot.TICK_LABEL_FONT_SIZE, width=batch_plot.AXIS_LINEWIDTH, length=2)
        ax.tick_params(axis="x", width=batch_plot.AXIS_LINEWIDTH, length=0, pad=2)
        for spine in ax.spines.values():
            spine.set_linewidth(batch_plot.AXIS_LINEWIDTH)
        ax.legend(
            loc="upper left", frameon=True, facecolor="white", edgecolor="none", framealpha=1.0,
            fontsize=LEGEND_FONT_SIZE, handlelength=1.0, borderaxespad=0.2,
        )
    fig.subplots_adjust(left=0.075, right=0.995, bottom=0.20, top=0.88, wspace=0.20)
    return fig


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[1]
    parent_dir = module_dir / "data" / "len4_7_tttt5p_noGGGG"
    review_parent_dir = module_dir / "data" / "len4_7_tttt5p_noGGGG_review"
    lengths = [4, 5, 6, 7]
    sources = [
        ("naive_rand_offline", "benchmark_x", "Naive random", "#808080"),
        ("naive_rank_offline", "benchmark_x_review", "Naive weaker-first", "#E69F00"),
        ("vertex_cover_GMAX_rule_offline", "benchmark_x", "GMAX", "#3B6FB6"),
        ("vertex_cover_GMIN_rule_offline", "benchmark_x_review", "GMIN", "#2A9D8F"),
    ]
    rows = []
    for has_tttt5p in (False, True):
        for length in lengths:
            for algorithm, benchmark_name, label, color in sources:
                source_parent = review_parent_dir if benchmark_name == "benchmark_x_review" else parent_dir
                dataset_dir = source_parent / f"len{length}{'_tttt5p' if has_tttt5p else ''}"
                report_dir = dataset_dir / "results" / benchmark_name
                for report_path in sorted(report_dir.glob("density*_limit*_seed*.xlsx")):
                    metadata = load_metadata(report_path)
                    if normalize_algorithm_name(metadata.get("algorithm_name")) != algorithm:
                        continue
                    density_label = report_path.name.split("_")[0].removeprefix("density")
                    rows.append({
                        "length": length,
                        "has_tttt5p": has_tttt5p,
                        "algorithm": algorithm,
                        "plot_series_key": algorithm,
                        "seed": int(metadata["search.random_seed"]),
                        "target_conflict_density": float(density_label.replace("p", ".")),
                        "found_pair_count": int(metadata["found_pair_count"]),
                        "report_path": str(report_path),
                    })

    runs_df = pd.DataFrame(rows)
    summary_df = build_summary_table(runs_df)
    series_specs = []
    for algorithm, benchmark_name, label, color in sources:
        counts = sorted(summary_df.loc[summary_df["algorithm"] == algorithm, "run_count"].unique())
        seed_label = "/".join(str(count) for count in counts)
        series_specs.append({"key": algorithm, "label": f"{label} (n={seed_label})", "color": color})
    fig = plot_comparison(summary_df, series_specs)
    plt.rcParams["pdf.fonttype"] = 42
    fig.canvas.draw()
    content_bbox = fig.get_tightbbox()
    # Crop only vertically so the export still matches the paper's text width.
    export_bbox = Bbox.from_extents(0, content_bbox.y0 - 0.02, fig.get_figwidth(), content_bbox.y1 + 0.02)
    output_path = review_parent_dir / "short_seq_gmin_naive_ordering.svg"
    fig.savefig(output_path, format="svg", bbox_inches=export_bbox, pad_inches=0)
    pdf_path = output_path.with_suffix(".pdf")
    fig.savefig(pdf_path, format="pdf", bbox_inches=export_bbox, pad_inches=0)
    plt.close(fig)
    print(f"Loaded {len(runs_df)} runs; bars show means with standard deviation across seeds.")
    print(f"Saved: {output_path}")
    print(f"Saved: {pdf_path}")
