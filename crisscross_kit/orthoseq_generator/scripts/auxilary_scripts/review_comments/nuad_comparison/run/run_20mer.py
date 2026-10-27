"""Run a fresh nuad comparison matching the saved 20-mer OrthoSeq library at 1 M sodium and zero magnesium."""

from datetime import datetime
from pathlib import Path
import sys


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[1]
    kit_folder = folder.parents[4]
    sys.path.insert(0, str(kit_folder))
    sys.path.insert(0, str(folder))
    from nuad_functions import load_case, run_benchmark
    from orthoseq_generator.search_report_reader import load_metadata

    reference_report = kit_folder / "orthoseq_generator/scripts/results/library_len20_Na1M_Mg0M_seed41.xlsx"
    reference_metadata = load_metadata(reference_report)
    seed = int(reference_metadata["search.random_seed"])
    association_budget = int(reference_metadata["search.total_nupack_budget"])
    output_dir = folder / "results" / f"20mer_Na1M_Mg0M_{datetime.now():%Y%m%d_%H%M%S}"
    case = load_case(reference_report, seed, association_budget)
    run_benchmark(case, output_dir)
