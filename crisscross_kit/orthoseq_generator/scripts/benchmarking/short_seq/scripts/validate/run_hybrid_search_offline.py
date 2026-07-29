#!/usr/bin/env python3

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_algorithms import run_hybrid_search_offline_to_xlsx


if __name__ == "__main__":
    dataset_dir = MODULE_DIR / "data" / "len4_7_tttt5p" / "len6"
    saved_path = run_hybrid_search_offline_to_xlsx(
        dataset_dir,
        offtarget_limit=-6.2,
        self_energy_limit=-8.0,
        initial_fresh_pair_count=450,
        prune_fraction=0.2,
        vc_max_iterations=5000,
        random_seed=9,
    )
    print(f"Saved offline hybrid benchmark result to: {saved_path}")
