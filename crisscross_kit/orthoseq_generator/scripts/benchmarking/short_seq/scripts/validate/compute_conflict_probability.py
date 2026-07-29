#!/usr/bin/env python3
"""
Load a short-sequence benchmark dataset and compute graph conflict density.

This uses the same graph construction as the search code:
- edges are built from the saved off-target matrices
- self-edges are included
- density denominator is written as:
    n + n(n-1)/2
"""

from __future__ import annotations

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_dataset_tools import load_dataset
from benchmark_analysis import compute_graph_conflict_density


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    dataset_dir = script_dir.parent / "data" / "len4_7_tttt5p" / "len5"
    offtarget_limit = -4.0

    dataset = load_dataset(dataset_dir)
    summary = compute_graph_conflict_density(dataset, offtarget_limit)

    print(f"Dataset: {dataset_dir}")
    for key, value in summary.items():
        print(f"{key}: {value}")
