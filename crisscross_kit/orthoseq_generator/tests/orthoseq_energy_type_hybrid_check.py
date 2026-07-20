#!/usr/bin/env python3
"""
Simple manual check for the two OrthoSeq energy conventions.

Run from the repository root:

    python tests/orthoseq_energy_type_hybrid_check.py

This writes three files into this same tests/ folder:

    hybrid_energy_type_total.xlsx
    hybrid_energy_type_total_bound_fraction.xlsx
    hybrid_energy_type_summary.toml
"""

from pathlib import Path
import os
import random
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "crisscross_kit"))

OUTPUT_DIR = Path(__file__).resolve().parent
os.environ.setdefault("ORTHOSEQ_NO_MP", "1")

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.search_algorithm import hybrid_search
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data,
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)
from orthoseq_generator.sequence_generation import SequencePairRegistry


if __name__ == "__main__":
    random_seed = 123
    energy_types = ["total", "total_bound_fraction"]

    length = 16
    fivep_ext = ""
    threep_ext = ""
    unwanted_substrings = ["GGGG", "CCCC"]
    apply_unwanted_to = "full"

    # Copied from the existing live search example, with a smaller budget.
    min_ontarget = -21.350806979612546
    max_ontarget = -19.308503678279084
    offtarget_limit = -8.160422784450315
    self_energy_limit = -0.9919471230992267
    initial_fresh_pair_count = 25
    total_nupack_budget = 10_000
    prune_fraction = 0.2
    vc_max_iterations = 1000

    hf.require_nupack()

    summary_lines = [
        f"random_seed = {random_seed}",
        f"length = {length}",
        f'threep_ext = "{threep_ext}"',
        f'fivep_ext = "{fivep_ext}"',
        f"min_ontarget = {min_ontarget}",
        f"max_ontarget = {max_ontarget}",
        f"offtarget_limit = {offtarget_limit}",
        f"self_energy_limit = {self_energy_limit}",
        f"initial_fresh_pair_count = {initial_fresh_pair_count}",
        f"total_nupack_budget = {total_nupack_budget}",
        "",
    ]
    final_pairs_by_energy_type = {}

    for energy_type in energy_types:
        print(f"\n=== Running energy_type={energy_type} ===")

        random.seed(random_seed)
        hf.set_nupack_params(material="dna", celsius=37.0, sodium=0.05, magnesium=0.025)
        hf.set_energy_type(energy_type)

        registry = SequencePairRegistry(
            length=length,
            fivep_ext=fivep_ext,
            threep_ext=threep_ext,
            unwanted_substrings=unwanted_substrings,
            apply_unwanted_to=apply_unwanted_to,
            seed=random_seed,
            preselected_cores=None,
        )

        search_result = hybrid_search(
            registry,
            offtarget_limit,
            max_ontarget,
            min_ontarget,
            self_energy_limit,
            initial_fresh_pair_count=initial_fresh_pair_count,
            total_nupack_budget=total_nupack_budget,
            prune_fraction=prune_fraction,
            vc_max_iterations=vc_max_iterations,
            return_diagnostics=True,
        )

        selected_sequence_data = build_selected_sequence_data(
            search_result["final_pairs"],
            search_result["final_pair_ids"],
            sequence_source=registry,
        )

        verified = verify_selected_pairs(selected_sequence_data, nupack_params=search_result["nupack"])
        validation_data = validate_selected_pairs(
            selected_sequence_data,
            verified,
            min_ontarget=min_ontarget,
            max_ontarget=max_ontarget,
            self_energy_limit=self_energy_limit,
            offtarget_limit=offtarget_limit,
        )

        report_path = OUTPUT_DIR / f"hybrid_energy_type_{energy_type}.xlsx"
        write_hybrid_search_result_xlsx(
            report_path,
            algorithm_name="hybrid_search_energy_type_check",
            selected_sequence_data=selected_sequence_data,
            verified=verified,
            search_params={
                **search_result["search_params"],
                "random_seed": random_seed,
                "total_nupack_calls": search_result["total_nupack_calls"],
            },
            input_params={"source_kind": "manual_test", **search_result["sequence_source"]},
            artifact_info={"dataset_dir": None, "dataset_toml": None, "dataset_npz": None},
            nupack_params=search_result["nupack"],
            generation_data=search_result["generation_data"],
            validation_data=validation_data,
            seed_sequence_data=build_selected_sequence_data(
                search_result["seed_pairs"],
                search_result["seed_pair_ids"],
                sequence_source=registry,
            ),
            seed_verified=search_result["seed_verified"],
            dataset_info={},
            extra_metadata={"stopped_reason": search_result["stopped_reason"]},
        )

        print(f"Saved report: {report_path}")
        print(f"Found pairs: {len(search_result['final_pairs'])}")
        final_pairs_by_energy_type[energy_type] = search_result["final_pairs"]

        summary_lines.extend(
            [
                "[[results]]",
                f'energy_type = "{energy_type}"',
                f'report_path = "{report_path}"',
                f"found_pair_count = {len(search_result['final_pairs'])}",
                f"total_nupack_calls = {search_result['total_nupack_calls']}",
                f'stopped_reason = "{search_result["stopped_reason"]}"',
                "",
            ]
        )

    same_final_pairs = (
        final_pairs_by_energy_type["total"]
        == final_pairs_by_energy_type["total_bound_fraction"]
    )
    summary_lines.insert(0, f"same_final_pairs = {str(same_final_pairs).lower()}")
    summary_path = OUTPUT_DIR / "hybrid_energy_type_summary.toml"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nSaved summary: {summary_path}")
    print(f"Same final sequence pairs: {same_final_pairs}")
