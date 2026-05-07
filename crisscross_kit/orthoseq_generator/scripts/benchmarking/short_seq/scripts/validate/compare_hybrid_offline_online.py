#!/usr/bin/env python3
"""
Compare the online and offline hybrid report outputs for one named benchmark
test run.

Purpose
-------
This validation script writes one offline-hybrid workbook and one live
online-hybrid workbook into the same benchmark-named results folder so their
metadata and progress sheets can be inspected side by side.
"""

from pathlib import Path
import random
import sys

import pandas as pd

MODULE_DIR = Path(__file__).resolve().parents[2]
PACKAGE_DIR = MODULE_DIR.parents[3]
for path in (MODULE_DIR, PACKAGE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from benchmark_algorithms import run_hybrid_search_offline_to_xlsx
from benchmark_dataset_tools import estimate_dataset_nupack_budget, load_dataset
from orthoseq_generator import helper_functions as hf
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data,
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)
from orthoseq_generator.search_algorithm import hybrid_search
from orthoseq_generator.sequence_generation import SequencePairRegistry


BENCHMARK_NAME = "benchmark_compare_hybrid"


def print_result(label, ids, pairs):
    print(f"{label} final ids:", ids)
    print(f"{label} final size:", len(pairs))
    print(f"{label} final pairs:")
    for pair_id, pair in zip(ids, pairs):
        print(pair_id, pair[0], pair[1])


def main():
    dataset_dir = MODULE_DIR / "data" / "len4_7_tttt5p" / "len6"
    dataset = load_dataset(dataset_dir)

    inputs = dataset["metadata"]["inputs"]
    derived = dataset["metadata"]["derived"]
    nupack_params = dataset["metadata"]["nupack"]
    total_nupack_budget = estimate_dataset_nupack_budget(dataset)

    offtarget_limit = -6.5
    self_energy_limit = -2.0
    initial_fresh_pair_count = 40
    generations = 2
    allowed_violations = 0
    fresh_pair_search_budget = 500
    prune_fraction = 0.2
    fresh_pair_scale = 1.0
    vc_max_iterations = 200
    random_seed = 44

    hf.set_nupack_params(
        material=nupack_params["material"],
        celsius=nupack_params["celsius"],
        sodium=nupack_params["sodium"],
        magnesium=nupack_params["magnesium"],
    )

    print("dataset:", dataset_dir)
    print("length:", inputs["length"])
    print("fivep_ext:", repr(inputs["fivep_ext"]))
    print("threep_ext:", repr(inputs["threep_ext"]))
    print("min_ontarget:", derived["min_ontarget_energy"])
    print("max_ontarget:", derived["max_ontarget_energy"])
    print("total_nupack_budget:", total_nupack_budget)

    print("starting offline...")
    results_dir = dataset_dir / "results" / BENCHMARK_NAME
    results_dir.mkdir(parents=True, exist_ok=True)
    cutoff_label = str(offtarget_limit).replace(".", "p")
    offline_path = run_hybrid_search_offline_to_xlsx(
        dataset_dir,
        output_path=results_dir / f"hybrid_offline_limit{cutoff_label}_seed{random_seed}.xlsx",
        offtarget_limit=offtarget_limit,
        self_energy_limit=self_energy_limit,
        initial_fresh_pair_count=initial_fresh_pair_count,
        generations=generations,
        allowed_violations=allowed_violations,
        fresh_pair_search_budget=fresh_pair_search_budget,
        prune_fraction=prune_fraction,
        fresh_pair_scale=fresh_pair_scale,
        vc_max_iterations=vc_max_iterations,
        random_seed=random_seed,
    )

    offline_rows = pd.read_excel(offline_path, sheet_name="selected_pairs")
    offline_ids = offline_rows["global_pair_id"].astype(int).tolist()
    offline_pairs = list(zip(offline_rows["seq"].astype(str), offline_rows["rc_seq"].astype(str)))

    print("starting online...")
    random.seed(random_seed)
    online_source = SequencePairRegistry(
        length=inputs["length"],
        fivep_ext=inputs["fivep_ext"],
        threep_ext=inputs["threep_ext"],
        unwanted_substrings=["AAAA", "CCCC", "GGGG", "TTTT"] if inputs["avoid_gggg"] else [],
        apply_unwanted_to="core",
        seed=random_seed,
    )

    online_result = hybrid_search(
        online_source,
        offtarget_limit,
        float(derived["max_ontarget_energy"]),
        float(derived["min_ontarget_energy"]),
        self_energy_limit,
        initial_fresh_pair_count=initial_fresh_pair_count,
        generations=generations,
        allowed_violations=allowed_violations,
        fresh_pair_search_budget=fresh_pair_search_budget,
        total_nupack_budget=total_nupack_budget,
        prune_fraction=prune_fraction,
        fresh_pair_scale=fresh_pair_scale,
        vc_max_iterations=vc_max_iterations,
        return_diagnostics=True,
    )

    online_sequence_data = build_selected_sequence_data(
        online_result["final_pairs"],
        online_result["final_pair_ids"],
    )
    online_verified = verify_selected_pairs(
        online_sequence_data,
        nupack_params=online_result["nupack"],
    )
    online_validation = validate_selected_pairs(
        online_sequence_data,
        online_verified,
        min_ontarget=float(derived["min_ontarget_energy"]),
        max_ontarget=float(derived["max_ontarget_energy"]),
        self_energy_limit=self_energy_limit,
        offtarget_limit=offtarget_limit,
    )
    online_path = results_dir / f"hybrid_online_limit{cutoff_label}_seed{random_seed}.xlsx"
    write_hybrid_search_result_xlsx(
        online_path,
        algorithm_name="hybrid_search",
        selected_sequence_data=online_sequence_data,
        verified=online_verified,
        search_params={
            **online_result["search_params"],
            "random_seed": random_seed,
            "total_nupack_calls": online_result["total_nupack_calls"],
        },
        sequence_source={"label": "on_the_fly_registry", **online_result["sequence_source"]},
        artifact_info={"dataset_dir": None, "dataset_toml": None, "dataset_npz": None},
        nupack_params=online_result["nupack"],
        generation_data=online_result["generation_data"],
        validation_data=online_validation,
        dataset_info={},
        extra_metadata={"benchmark_name": BENCHMARK_NAME},
    )

    print("benchmark name:", BENCHMARK_NAME)
    print("offline xlsx saved to:", offline_path)
    print("online xlsx saved to:", online_path)
    print_result("offline", offline_ids, offline_pairs)
    print_result("online", online_result["final_pair_ids"], online_result["final_pairs"])


if __name__ == "__main__":
    main()
