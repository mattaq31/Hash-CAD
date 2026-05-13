#!/usr/bin/env python3
'''
run_naive_search.py

Purpose:
    This script performs the live naive orthogonal sequence search. It samples
    candidate sequence pairs on the fly and greedily accepts a pair only if it
    satisfies the requested on-target, self-energy, homodimer, and
    cross-reference constraints.

    This script mirrors the style of `run_sequence_search.py`, but uses the
    naive greedy search algorithm instead of the hybrid graph-refinement path.

Main Steps:
    1. Set a fixed random seed for reproducibility.
    2. Generate candidate sequence pairs on the fly from the registry.
    3. Define on-target, self-energy, and off-target constraints.
    4. Run the live naive search until the NUPACK budget is reached.
    5. Verify the final result and write a shared XLSX report.
    6. Plot the verified on-target, off-target, and self-energy distributions.

Usage:
    python run_naive_search.py
'''

import random
from pathlib import Path

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.naive_search_algorithm import naive_search
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data,
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)


if __name__ == "__main__":
    # 1) Set a random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # 2) Generate candidate sequence pairs on the fly
    sequence_pairs_object = sc.SequencePairRegistry(
        length=10,
        fivep_ext="",
        threep_ext="",
        unwanted_substrings=[],
        apply_unwanted_to="core",
        seed=RANDOM_SEED,
        preselected_cores=None,
    )

    # 3) Define energy thresholds based on prior analysis
    hf.set_nupack_params(material="rna", celsius=37, sodium=0.050, magnesium=0.025)
    hf.set_energy_type("total")
    max_ontarget = -15
    min_ontarget = -17.5
    offtarget_limit = -8.5
    self_energy_limit = -0.5
    progress_every = 250
    TOTAL_NUPACK_BUDGET = 200000
    print(f"Total NUPACK budget: {TOTAL_NUPACK_BUDGET}")

    # 4) Run the live naive search until the NUPACK budget is reached
    search_result = naive_search(
        sequence_pairs_object,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        self_energy_limit,
        total_nupack_budget=TOTAL_NUPACK_BUDGET,
        progress_every=progress_every,
        stop_event=None,
        return_diagnostics=True,
    )
    orthogonal_seq_pairs = search_result["final_pairs"]

    if not orthogonal_seq_pairs:
        print("No sequences found; skipping report and plots.")
        raise SystemExit(0)

    selected_sequence_data = build_selected_sequence_data(
        orthogonal_seq_pairs,
        search_result["final_pair_ids"],
    )

    # 5) Verify and save the selected orthogonal sequences as a run report
    verified = verify_selected_pairs(selected_sequence_data, nupack_params=search_result["nupack"])
    validation_data = validate_selected_pairs(
        selected_sequence_data,
        verified,
        min_ontarget=min_ontarget,
        max_ontarget=max_ontarget,
        self_energy_limit=self_energy_limit,
        offtarget_limit=offtarget_limit,
    )
    results_dir = Path(hf.get_default_results_folder())
    report_path = write_hybrid_search_result_xlsx(
        results_dir / "naive_search_10mers.xlsx",
        algorithm_name="naive_search",
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            **search_result["search_params"],
            "random_seed": RANDOM_SEED,
            "total_nupack_calls": search_result["total_nupack_calls"],
        },
        input_params={"source_kind": "on_the_fly_registry", **search_result["sequence_source"]},
        artifact_info={"dataset_dir": None, "dataset_toml": None, "dataset_npz": None},
        nupack_params=search_result["nupack"],
        generation_data=search_result["generation_data"],
        validation_data=validation_data,
        dataset_info={},
        extra_metadata={
            "best_generation_result_size": len(selected_sequence_data),
            "search.progress_every": progress_every,
            "search.attempts": search_result["attempts"],
            "stopped_reason": search_result["stopped_reason"],
        },
    )
    print(f"Saved verified run report to: {report_path}")

    # 6) Compute and plot the on-target and off-target energy distributions for the found pairs
    onef = verified["on_target_energies"]
    self_e_A = verified["self_energy_seqs"]
    self_e_B = verified["self_energy_rc_seqs"]
    offef = verified["off_target"]

    stats = sc.plot_on_off_target_histograms(
        onef,
        offef,
        output_path="naive_ortho_energies.pdf",
    )

    self_stats = sc.plot_self_energy_histogram(
        [self_e_A, self_e_B],
        bins=30,
        output_path="naive_self_energies.pdf",
    )
