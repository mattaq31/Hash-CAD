#!/usr/bin/env python3

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_algorithms import run_hybrid_search_offline_to_xlsx
from benchmark_dataset_tools import estimate_dataset_nupack_budget, load_dataset


if __name__ == "__main__":
    dataset_dir = MODULE_DIR / "data" / "len4_7_tttt5p" / "len6"
    dataset = load_dataset(dataset_dir)
    total_nupack_budget = estimate_dataset_nupack_budget(dataset)
    print(f"Dataset virtual NUPACK budget: {total_nupack_budget}")

    saved_path = run_hybrid_search_offline_to_xlsx(
        dataset_dir,
        offtarget_limit=-6.2,
        self_energy_limit=-8.0,
        initial_fresh_pair_count=450,
        generations=5000,
        allowed_violations=1,
        fresh_pair_search_budget=5000,
        total_nupack_budget=total_nupack_budget,
        prune_fraction=0.2,
        fresh_pair_scale=1.0,
        vc_max_iterations=5000,
        random_seed=9,
    )
    print(f"Saved offline hybrid benchmark result to: {saved_path}")
