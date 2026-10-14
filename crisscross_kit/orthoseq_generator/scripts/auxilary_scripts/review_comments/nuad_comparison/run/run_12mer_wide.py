"""Run the 120-pair, extension-free 12-mer comparison with the saved sigma-1.0 on-target window."""

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
        kit_folder / "orthoseq_generator/scripts/benchmarking/zenodo/benchmark_data/full_benchmark_results/long_seq"
        / "data/batch_x______sigma1p0_seed41/len12/5p_none"
        / "hybrid_len12_5p_none_limitm8p16_budget10000000_init250_seed41.xlsx"
    )
    seed = 41
    association_budget = 10_000_000
    output_dir = folder / "results" / f"12mer_wide_{datetime.now():%Y%m%d_%H%M%S}"
    case = load_case(reference_report, seed, association_budget)
    run_benchmark(case, output_dir)
