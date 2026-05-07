#!/usr/bin/env python3

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_algorithms import run_naive_search_to_xlsx


if __name__ == "__main__":
    dataset_dir = MODULE_DIR / "data" / "len4_7_tttt5p" / "len5"

    saved_path = run_naive_search_to_xlsx(
        dataset_dir,
        offtarget_limit=-6.2,
        self_energy_limit=-2.0,
        random_seed=41,
    )
    print(f"Saved naive benchmark result to: {saved_path}")
