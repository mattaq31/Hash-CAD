#!/usr/bin/env python3
"""
Run the saved-dataset benchmark workflow across every complete dataset in one
dataset parent.

Purpose
-------
This script is the main batch benchmark entrypoint. It discovers complete
datasets under the configured parent directory, resolves off-target cutoffs
from the requested target graph densities, runs the benchmark algorithms, and
writes both per-dataset XLSX workbooks and one parent-level summary TOML for
the named benchmark run.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from benchmark_algorithms import (
    run_hybrid_search_offline_to_xlsx,
    run_naive_search_to_xlsx,
    run_vertex_cover_search_to_xlsx,
)
from benchmark_analysis import find_offtarget_limits_for_target_densities
from benchmark_dataset_tools import estimate_dataset_nupack_budget, load_dataset


DATASET_PARENT_NAME = "len4_7_tttt5p"
BENCHMARK_NAME = "benchmark_2"
TARGET_CONFLICT_DENSITIES = [0.1,0.2,0.3]
SEEDS = [1,2,3,4,5]
SELF_ENERGY_LIMIT = -2.0

VC_CORE_PARAMS = {
    "prune_fraction": 0.2,
    "vc_max_iterations": 1000,
}

HYBRID_ONLY_PARAMS = {
    "initial_fresh_pair_count": 450,
    "generations": 5000,
    "allowed_violations": 0,
    "fresh_pair_search_budget": 5000,
    "fresh_pair_scale": 1.0,
}

HYBRID_PARAMS = {
    **VC_CORE_PARAMS,
    **HYBRID_ONLY_PARAMS,
}

VERTEX_COVER_PARAMS = {
    **VC_CORE_PARAMS,
}


def discover_dataset_dirs(parent_dir: Path) -> list[Path]:
    """
    Discover complete dataset directories inside one benchmark dataset parent.

    A child directory is considered runnable only when both `dataset.toml` and
    `dataset.npz` are present.
    """
    dataset_dirs = []
    for child in sorted(parent_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "dataset.toml").exists() and (child / "dataset.npz").exists():
            dataset_dirs.append(child)
    return dataset_dirs


def read_found_pair_count(report_path: Path) -> int:
    """Read the found-pair count from a benchmark workbook."""
    selected_pairs = pd.read_excel(report_path, sheet_name="found_pairs")
    return int(len(selected_pairs))


def toml_literal(value) -> str:
    """Serialize a small Python value into the limited TOML used here."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(toml_literal(item) for item in value) + "]"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def write_summary_toml(
    output_path: Path,
    *,
    created_at: str,
    benchmark_name: str,
    dataset_parent: Path,
    runs: list[dict],
) -> None:
    """Write the compact parent-level summary for one named batch run."""
    lines = [
        f'created_at = {toml_literal(created_at)}',
        f'benchmark_name = {toml_literal(benchmark_name)}',
        f'dataset_parent = {toml_literal(str(dataset_parent))}',
        f'target_conflict_densities = {toml_literal(TARGET_CONFLICT_DENSITIES)}',
        f'seeds = {toml_literal(SEEDS)}',
        f'self_energy_limit = {toml_literal(SELF_ENERGY_LIMIT)}',
        "",
    ]
    for run in runs:
        lines.append("[[runs]]")
        for key, value in run.items():
            lines.append(f"{key} = {toml_literal(value)}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="ascii")


if __name__ == "__main__":
    parent_dir = MODULE_DIR / "data" / DATASET_PARENT_NAME
    dataset_dirs = discover_dataset_dirs(parent_dir)
    benchmark_name = BENCHMARK_NAME

    print(f"dataset parent: {parent_dir}")
    print(f"benchmark name: {benchmark_name}")
    print(f"discovered datasets: {[dataset_dir.name for dataset_dir in dataset_dirs]}")
    print(f"target conflict densities: {TARGET_CONFLICT_DENSITIES}")
    print(f"seeds: {SEEDS}")
    print(f"self_energy_limit: {SELF_ENERGY_LIMIT}")

    summary_runs = []

    for dataset_dir in dataset_dirs:
        dataset = load_dataset(dataset_dir)
        inputs = dataset["metadata"]["inputs"]
        total_nupack_budget = estimate_dataset_nupack_budget(dataset)
        cutoff_summaries = find_offtarget_limits_for_target_densities(dataset, TARGET_CONFLICT_DENSITIES)
        results_dir = dataset_dir / "results" / benchmark_name
        results_dir.mkdir(parents=True, exist_ok=True)

        print(f"processing dataset: {dataset_dir.name}")
        print(f"  total_nupack_budget: {total_nupack_budget}")
        for cutoff_summary in cutoff_summaries:
            target_density = float(cutoff_summary["target_conflict_density"])
            offtarget_limit = float(cutoff_summary["selected_offtarget_limit"])
            achieved_density = float(cutoff_summary["achieved_conflict_density"])
            density_label = str(target_density).replace(".", "p")
            cutoff_label = str(offtarget_limit).replace(".", "p")

            for seed in SEEDS:
                print(f"  naive | density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                naive_path = results_dir / f"density{density_label}_naive_limit{cutoff_label}_seed{seed}.xlsx"
                run_naive_search_to_xlsx(
                    dataset_dir,
                    output_path=naive_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=SELF_ENERGY_LIMIT,
                    random_seed=seed,
                )
                summary_runs.append(
                    {
                        "dataset_name": dataset_dir.name,
                        "length": int(inputs["length"]),
                        "fivep_ext": str(inputs["fivep_ext"]),
                        "threep_ext": str(inputs["threep_ext"]),
                        "has_tttt5p": bool(inputs["fivep_ext"] == "TTTT"),
                        "algorithm": "naive",
                        "seed": int(seed),
                        "target_conflict_density": target_density,
                        "selected_offtarget_limit": offtarget_limit,
                        "achieved_conflict_density": achieved_density,
                        "found_pair_count": read_found_pair_count(naive_path),
                        "report_path": str(naive_path),
                    }
                )

                print(f"  vertex_cover | density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                vc_path = results_dir / f"density{density_label}_vertex_cover_limit{cutoff_label}_seed{seed}.xlsx"
                run_vertex_cover_search_to_xlsx(
                    dataset_dir,
                    output_path=vc_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=SELF_ENERGY_LIMIT,
                    random_seed=seed,
                    **VERTEX_COVER_PARAMS,
                )
                summary_runs.append(
                    {
                        "dataset_name": dataset_dir.name,
                        "length": int(inputs["length"]),
                        "fivep_ext": str(inputs["fivep_ext"]),
                        "threep_ext": str(inputs["threep_ext"]),
                        "has_tttt5p": bool(inputs["fivep_ext"] == "TTTT"),
                        "algorithm": "vertex_cover",
                        "seed": int(seed),
                        "target_conflict_density": target_density,
                        "selected_offtarget_limit": offtarget_limit,
                        "achieved_conflict_density": achieved_density,
                        "found_pair_count": read_found_pair_count(vc_path),
                        "report_path": str(vc_path),
                    }
                )

                print(f"  hybrid_offline | density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                hybrid_path = results_dir / f"density{density_label}_hybrid_offline_limit{cutoff_label}_seed{seed}.xlsx"
                run_hybrid_search_offline_to_xlsx(
                    dataset_dir,
                    output_path=hybrid_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=SELF_ENERGY_LIMIT,
                    total_nupack_budget=total_nupack_budget,
                    random_seed=seed,
                    **HYBRID_PARAMS,
                )
                summary_runs.append(
                    {
                        "dataset_name": dataset_dir.name,
                        "length": int(inputs["length"]),
                        "fivep_ext": str(inputs["fivep_ext"]),
                        "threep_ext": str(inputs["threep_ext"]),
                        "has_tttt5p": bool(inputs["fivep_ext"] == "TTTT"),
                        "algorithm": "hybrid_offline",
                        "seed": int(seed),
                        "target_conflict_density": target_density,
                        "selected_offtarget_limit": offtarget_limit,
                        "achieved_conflict_density": achieved_density,
                        "found_pair_count": read_found_pair_count(hybrid_path),
                        "report_path": str(hybrid_path),
                    }
                )

    summary_path = parent_dir / f"benchmark_summary_{benchmark_name}.toml"
    write_summary_toml(
        summary_path,
        created_at=datetime.now().isoformat(timespec="seconds"),
        benchmark_name=benchmark_name,
        dataset_parent=parent_dir,
        runs=summary_runs,
    )
    print(f"summary toml saved to: {summary_path}")
