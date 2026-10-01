"""Compare original GMAX/random-naive results with the new GMIN/weaker-first no-flank runs."""

from pathlib import Path

import pandas as pd

from plot_batch_benchmark import build_summary_table, compute_plot_y_max, plot_group
import matplotlib.pyplot as plt

from orthoseq_generator.search_report_reader import load_metadata


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[1]
    parent_dir = module_dir / "data" / "len4_7_tttt5p_noGGGG"
    lengths = [4, 5, 6, 7]
    sources = [
        ("naive", "benchmark_x", "density*_naive_limit*_seed*.xlsx", "Naive random", "#808080"),
        ("naive_ordered", "benchmark_x_review",
         "density*_naive_ordered_limit*_seed*.xlsx", "Naive weaker-first", "#E69F00"),
        ("gmax", "benchmark_x", "density*_vertex_cover_limit*_seed*.xlsx", "GMAX", "#3B6FB6"),
        ("vertex_cover_GMIN", "benchmark_x_review",
         "density*_vertex_cover_GMIN_limit*_seed*.xlsx", "GMIN", "#2A9D8F"),
    ]
    rows = []
    for length in lengths:
        dataset_dir = parent_dir / f"len{length}"
        for algorithm, benchmark_name, pattern, label, color in sources:
            for report_path in sorted((dataset_dir / "results" / benchmark_name).glob(pattern)):
                metadata = load_metadata(report_path)
                density_label = report_path.name.split("_")[0].removeprefix("density")
                rows.append({
                    "length": length,
                    "has_tttt5p": False,
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
    for algorithm, benchmark_name, pattern, label, color in sources:
        counts = sorted(summary_df.loc[summary_df["algorithm"] == algorithm, "run_count"].unique())
        seed_label = "/".join(str(count) for count in counts)
        series_specs.append({"key": algorithm, "label": f"{label} (n={seed_label})", "color": color})
    fig, _ = plot_group(
        summary_df, has_tttt5p=False, shared_y_max=compute_plot_y_max(summary_df), series_specs=series_specs,
    )
    output_path = parent_dir / "batch_benchmark_found_pair_count_gmin_naive_ordering_no_extension.svg"
    fig.savefig(output_path, format="svg")
    plt.close(fig)
    print(f"Loaded {len(runs_df)} runs; bars show means with SEM where multiple seeds are available.")
    print(f"Saved: {output_path}")
