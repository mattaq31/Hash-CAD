#!/usr/bin/env python3
'''
run_orthoseq_assembly_search.py

Purpose:
    Auxiliary copy of scripts/run_sequence_search.py to reproduce the assembly-model search.
    This script performs the actual selection of an orthogonal set of DNA sequence pairs
    using the hybrid search algorithm. It selects sequences whose on-target
    energies fall within a desired range and prunes off-target interactions via
    iterative graph-based refinement.

    This script is intended to be run **after** initial exploration with
    `preanalyze_sequences.py` and optionally `analyze_on_target_range.py` to determine
    sensible energy cutoffs.

Main Steps:
    1. Set a fixed random seed for reproducibility.
    2. Generate the full pool of sequence pairs (with optional flanking sequences).
    3. Define energy cutoffs for on-target and off-target interactions based on prior analysis.
    4. Run the hybrid search algorithm to find a set of sequences with minimal cross-interaction.
    5. Save the selected sequences to file for downstream use.
    6. Recompute and visualize final on- and off-target energy distributions.

Usage:
    python run_orthoseq_assembly_search.py
'''

import random
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.search_algorithm import hybrid_search
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
    TOTAL_NUPACK_BUDGET = float("inf")
    INITIAL_FRESH_PAIR_COUNT = 450
    VC_MAX_ITERATIONS = 5000
    PRUNE_FRACTION = 0.4
    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    res_name = f"orthoseq_assembly_search_{run_timestamp}.xlsx"
    folder = Path(__file__).resolve().parents[1]
    data_dir = folder / "data"
    plots_dir = folder / "plots" / "assembly_37C_Na50mM_Mg12p5mM" / "search_runs"
    data_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    nupack_params = {
        "material": "dna", "celsius": 37.0, "sodium": 0.05, "magnesium": 0.0125, "energy_type": "total",
    }
    plt.switch_backend("Agg")

    # Preserve the settings of the completed comparison search.
    max_ontarget = -11.7
    min_ontarget = -12.5
    offtarget_limit = -8.05
    self_energy_limit = -0.5
    sequence_pairs_object = sc.SequencePairRegistry(
        length=9,
        fivep_ext="T" * 12,
        threep_ext="",
        unwanted_substrings=["AAA", "CCC", "GGG", "TTT"],
        apply_unwanted_to="core",
        seed=RANDOM_SEED,
    )


    print(f"Total NUPACK budget: {TOTAL_NUPACK_BUDGET}")
    print(f"Initial graph search requested pairs: {INITIAL_FRESH_PAIR_COUNT}")

    # Configure once before execution; checkpoints and both passes use these settings.
    hf.set_nupack_params(**{key: value for key, value in nupack_params.items() if key != "energy_type"})
    hf.set_energy_type(nupack_params["energy_type"])
    hf.set_algorithm(heuristics="Gmax", tiebreak="rule")

    search_result = hybrid_search(
        sequence_pairs_object,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        self_energy_limit,
        initial_fresh_pair_count=INITIAL_FRESH_PAIR_COUNT,
        total_nupack_budget=TOTAL_NUPACK_BUDGET,
        prune_fraction=PRUNE_FRACTION,
        vc_max_iterations=VC_MAX_ITERATIONS,
        stop_event=None,
        return_diagnostics=True,
    )
    orthogonal_seq_pairs = search_result["final_pairs"]
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
    seed_sequence_data = build_selected_sequence_data(
        search_result["seed_pairs"],
        search_result["seed_pair_ids"],
    )
    seed_verified = search_result["seed_verified"]

    report_path = write_hybrid_search_result_xlsx(
        data_dir / res_name,
        algorithm_name="hybrid_search",
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
        seed_sequence_data=seed_sequence_data,
        seed_verified=seed_verified,
        dataset_info={},
        extra_metadata={
            "stopped_reason": search_result["stopped_reason"],
        },
    )
    print(f"Saved verified run report to: {report_path}")

    # 6) Compute and plot the on-target and off-target energy distributions for the found pairs
    onef = verified["on_target_energies"]
    self_e_A = verified["self_energy_seqs"]
    self_e_B = verified["self_energy_rc_seqs"]
    offef = verified["off_target"]

    sc.plot_on_off_target_histograms(
        onef,
        offef,
        output_path=plots_dir / f"orthoseq_assembly_search_{run_timestamp}_on_off_target.pdf",
        show_plot=False,
    )

    sc.plot_self_energy_histogram(
        [self_e_A, self_e_B], bins=30,
        output_path=plots_dir / f"orthoseq_assembly_search_{run_timestamp}_self_folding.pdf", show_plot=False,
    )
