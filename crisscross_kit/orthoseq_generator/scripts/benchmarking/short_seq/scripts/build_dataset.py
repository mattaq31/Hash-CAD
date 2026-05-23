#!/usr/bin/env python3
"""
Build the canonical batch of short-sequence benchmark datasets.

Purpose
-------
This script is the first step of the saved-dataset benchmark workflow:

1. `build_dataset.py`
2. `run_batch_benchmark.py`
3. `plot_batch_benchmark.py`

It creates one dataset parent directory, writes the shared batch parameter
record, and then builds the per-condition `dataset.toml` / `dataset.npz`
bundles used by the benchmark runners.
"""

from __future__ import annotations

from pathlib import Path

import sys

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_dataset_tools import build_short_seq_dataset


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    batch_dir = script_dir.parent / "data" / "len4_7_tttt5p_noGGGG"
    batch_dir.mkdir(parents=True, exist_ok=True)

    range_sigma = 1.0
    threep_ext = ""
    unwanted_substrings = ["GGGG","CCCC"]
    apply_unwanted_to = "full"
    random_seed = 42
    material = "dna"
    celsius = 37
    sodium = 0.05
    magnesium = 0.025
    lengths = [4, 5, 6, 7]
    fivep_ext_variants = ["", "TTTT"]

    params_text = f"""range_sigma = {range_sigma}
threep_ext = "{threep_ext}"
unwanted_substrings = [{", ".join(f'"{substring}"' for substring in unwanted_substrings)}]
apply_unwanted_to = "{apply_unwanted_to}"
random_seed = {random_seed}
material = "{material}"
celsius = {celsius}
sodium = {sodium}
magnesium = {magnesium}
lengths = [{", ".join(str(length) for length in lengths)}]
fivep_ext_variants = [{", ".join(f'"{fivep_ext}"' for fivep_ext in fivep_ext_variants)}]
"""
    (batch_dir / "batch_params.toml").write_text(params_text, encoding="ascii")

    for length in lengths:
        for fivep_ext in fivep_ext_variants:
            dataset_name = f"len{length}" if not fivep_ext else f"len{length}_tttt5p"
            dataset_dir = batch_dir / dataset_name
            dataset_toml = dataset_dir / "dataset.toml"
            dataset_npz = dataset_dir / "dataset.npz"
            if dataset_toml.exists() and dataset_npz.exists():
                print(f"Dataset already exists and looks complete: {dataset_dir}", flush=True)
                print(f"Skipping existing dataset: {dataset_dir}", flush=True)
                continue
            build_short_seq_dataset(
                dataset_dir,
                length=length,
                range_sigma=range_sigma,
                fivep_ext=fivep_ext,
                threep_ext=threep_ext,
                unwanted_substrings=unwanted_substrings,
                apply_unwanted_to=apply_unwanted_to,
                random_seed=random_seed,
                material=material,
                celsius=celsius,
                sodium=sodium,
                magnesium=magnesium,
            )
            print(f"Saved dataset to: {dataset_dir}")
