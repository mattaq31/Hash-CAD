"""Run the 41-pair, extension-free 6-mer comparison against its saved OrthoSeq reference."""

from datetime import datetime
from pathlib import Path
import sys


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[1]
    kit_folder = folder.parents[4]
    sys.path.insert(0, str(kit_folder))
    sys.path.insert(0, str(folder))
    from nuad_functions import load_case, run_benchmark

    reference_report = (
        kit_folder / "orthoseq_generator/scripts/benchmarking/zenodo/benchmark_data/full_benchmark_results"
        / "short_seq/data/len4_7_tttt5p_noGGGG/len6/results/benchmark_x"
        / "density0p1_vertex_cover_limit-6p583498094575131_seed2.xlsx"
    )
    seed = 41
    # Reconstructed full-dataset cost: 2,040 candidates + 2 * 627**2 off-target evaluations.
    association_budget = 788_298
    output_dir = folder / "results" / f"6mer_{datetime.now():%Y%m%d_%H%M%S}"
    case = load_case(reference_report, seed, association_budget)
    run_benchmark(case, output_dir)
