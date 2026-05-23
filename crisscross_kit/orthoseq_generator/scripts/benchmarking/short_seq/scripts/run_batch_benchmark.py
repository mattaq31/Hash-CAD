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
from itertools import product
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
from benchmark_dataset_tools import (
    load_dataset,
    self_energy_limit_from_unpaired_fraction,
)

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


def expand_param_grid(param_grid: dict) -> list[dict]:
    """Expand a small dict of scalar-or-list parameter values into run variants."""
    if not param_grid:
        return [{}]

    keys = list(param_grid.keys())
    value_lists = []
    for key in keys:
        raw_value = param_grid[key]
        if isinstance(raw_value, (list, tuple)):
            values = list(raw_value)
        else:
            values = [raw_value]
        if not values:
            raise ValueError(f"Parameter grid entry {key!r} must contain at least one value.")
        value_lists.append(values)

    return [dict(zip(keys, combo)) for combo in product(*value_lists)]


def slugify_param_value(value) -> str:
    """Convert one small parameter value into a filename-safe token."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value).replace("-", "m").replace(".", "p")
    return str(value).replace("-", "m").replace(".", "p").replace(" ", "")


def build_hybrid_variant_label(params: dict) -> str:
    """Build a stable filename suffix for one hybrid parameter choice."""
    key_aliases = {
        "initial_fresh_pair_count": "init",
        "prune_fraction": "prune",
        "vc_max_iterations": "vc",
    }
    pieces = []
    for key, value in params.items():
        key_label = key_aliases.get(key, key)
        pieces.append(f"{key_label}{slugify_param_value(value)}")
    return "_".join(pieces)


def write_summary_toml(
    output_path: Path,
    *,
    created_at: str,
    benchmark_name: str,
    dataset_parent: Path,
    target_conflict_densities: list[float],
    seeds: list[int],
    target_unpaired_fraction: float,
    runs: list[dict],
) -> None:
    """Write the compact parent-level summary for one named batch run."""
    unique_self_limits = sorted({float(run["self_energy_limit"]) for run in runs}) if runs else []
    lines = [
        f'created_at = {toml_literal(created_at)}',
        f'benchmark_name = {toml_literal(benchmark_name)}',
        f'dataset_parent = {toml_literal(str(dataset_parent))}',
        f'target_conflict_densities = {toml_literal(target_conflict_densities)}',
        f'seeds = {toml_literal(seeds)}',
        f'self_target_unpaired_fraction = {toml_literal(target_unpaired_fraction)}',
        "",
    ]
    if len(unique_self_limits) == 1:
        lines.insert(5, f'self_energy_limit = {toml_literal(unique_self_limits[0])}')
    for run in runs:
        lines.append("[[runs]]")
        for key, value in run.items():
            lines.append(f"{key} = {toml_literal(value)}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="ascii")


if __name__ == "__main__":
    dataset_parent_name = "len4_7_tttt5p_noGGGG"
    benchmark_name = "benchmark_x"
    target_conflict_densities = [0.1, 0.2, 0.3]
    seeds = [1,2,3,4,5]
    target_unpaired_fraction = 0.2
    vc_core_params = {
        "prune_fraction": 0.2,
        "vc_max_iterations": 1000,
    }
    hybrid_params_grid = {
        "initial_fresh_pair_count": [250, 450, 900],
        **vc_core_params,
    }
    vertex_cover_params = {
        **vc_core_params,
    }

    parent_dir = MODULE_DIR / "data" / dataset_parent_name
    dataset_dirs = discover_dataset_dirs(parent_dir)
    hybrid_param_variants = expand_param_grid(hybrid_params_grid)
    include_hybrid_variant_suffix = len(hybrid_param_variants) > 1

    print(f"dataset parent: {parent_dir}")
    print(f"benchmark name: {benchmark_name}")
    print(f"discovered datasets: {[dataset_dir.name for dataset_dir in dataset_dirs]}")
    print(f"target conflict densities: {target_conflict_densities}")
    print(f"seeds: {seeds}")
    print(f"self_target_unpaired_fraction: {target_unpaired_fraction}")
    print(f"hybrid param variants: {hybrid_param_variants}")

    summary_runs = []

    for dataset_dir in dataset_dirs:
        dataset = load_dataset(dataset_dir)
        inputs = dataset["metadata"]["inputs"]
        nupack = dataset["metadata"]["nupack"]
        self_energy_limit = self_energy_limit_from_unpaired_fraction(
            target_unpaired_fraction,
            float(nupack["celsius"]),
        )
        cutoff_summaries = find_offtarget_limits_for_target_densities(dataset, target_conflict_densities)
        results_dir = dataset_dir / "results" / benchmark_name
        results_dir.mkdir(parents=True, exist_ok=True)

        print(f"processing dataset: {dataset_dir.name}")
        print(f"  self_energy_limit={self_energy_limit}")
        for cutoff_summary in cutoff_summaries:
            target_density = float(cutoff_summary["target_conflict_density"])
            offtarget_limit = float(cutoff_summary["selected_offtarget_limit"])
            achieved_density = float(cutoff_summary["achieved_conflict_density"])
            density_label = str(target_density).replace(".", "p")
            cutoff_label = str(offtarget_limit).replace(".", "p")

            for seed in seeds:
                print(f"  naive | density={target_density} | cutoff={offtarget_limit} | seed={seed}")
                naive_path = results_dir / f"density{density_label}_naive_limit{cutoff_label}_seed{seed}.xlsx"
                run_naive_search_to_xlsx(
                    dataset_dir,
                    output_path=naive_path,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=self_energy_limit,
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
                        "self_energy_limit": self_energy_limit,
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
                    self_energy_limit=self_energy_limit,
                    random_seed=seed,
                    **vertex_cover_params,
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
                        "self_energy_limit": self_energy_limit,
                        "found_pair_count": read_found_pair_count(vc_path),
                        "report_path": str(vc_path),
                    }
                )

                for hybrid_params in hybrid_param_variants:
                    variant_label = build_hybrid_variant_label(hybrid_params)
                    variant_suffix = f"_{variant_label}" if include_hybrid_variant_suffix else ""
                    print(
                        "  hybrid_offline | "
                        f"density={target_density} | cutoff={offtarget_limit} | seed={seed} | "
                        f"params={hybrid_params}"
                    )
                    hybrid_path = (
                        results_dir
                        / f"density{density_label}_hybrid_offline_limit{cutoff_label}{variant_suffix}_seed{seed}.xlsx"
                    )
                    run_hybrid_search_offline_to_xlsx(
                        dataset_dir,
                        output_path=hybrid_path,
                        offtarget_limit=offtarget_limit,
                        self_energy_limit=self_energy_limit,
                        random_seed=seed,
                        **hybrid_params,
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
                            "self_energy_limit": self_energy_limit,
                            "initial_fresh_pair_count": int(hybrid_params["initial_fresh_pair_count"]),
                            "prune_fraction": float(hybrid_params["prune_fraction"]),
                            "vc_max_iterations": int(hybrid_params["vc_max_iterations"]),
                            "hybrid_variant_label": variant_label,
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
        target_conflict_densities=target_conflict_densities,
        seeds=seeds,
        target_unpaired_fraction=target_unpaired_fraction,
        runs=summary_runs,
    )
    print(f"summary toml saved to: {summary_path}")
