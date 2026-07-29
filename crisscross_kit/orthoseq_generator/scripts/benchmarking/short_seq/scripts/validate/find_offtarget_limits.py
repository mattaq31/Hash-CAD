#!/usr/bin/env python3
"""
Find off-target cutoffs for target graph conflict densities.

This script searches over the actual energy values present in the saved
off-target matrices, so every probe corresponds to a possible graph change.
"""

from __future__ import annotations

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_dataset_tools import load_dataset
from benchmark_analysis import find_offtarget_limits_for_target_densities


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    dataset_dir = script_dir.parent / "data" / "len4_7_tttt5p" / "len5"
    target_densities = [0.1, 0.2, 0.3]

    dataset = load_dataset(dataset_dir)
    summaries = find_offtarget_limits_for_target_densities(dataset, target_densities)

    print(f"Dataset: {dataset_dir}")
    for summary in summaries:
        print("---")
        for key, value in summary.items():
            print(f"{key}: {value}")
