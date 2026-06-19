#!/usr/bin/env python3

"""
Prepare the SeqWalk + postfilter Figure 5 dataset.

This runner generates SeqWalk cores, feeds them into the registry, and runs
the thermodynamic hybrid-search branch used as the barcode-preserving
comparison arm in Figure 5.
"""

from pathlib import Path
import random
import sys

from seqwalk import design

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.search_algorithm import hybrid_search
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data,
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)


def write_hybrid_seqwalk_report(
    registry,
    *,
    output_path,
    random_seed,
    min_ontarget,
    max_ontarget,
    offtarget_limit,
    self_energy_limit,
    initial_fresh_pair_count,
    total_nupack_budget,
    prune_fraction,
    vc_max_iterations,
):
    print("Running hybrid search on the SeqWalk-restricted candidate source...")
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
        stop_event=None,
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
    seed_sequence_data = build_selected_sequence_data(
        search_result["seed_pairs"],
        search_result["seed_pair_ids"],
    )

    report_path = write_hybrid_search_result_xlsx(
        output_path,
        algorithm_name="hybrid_search",
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            **search_result["search_params"],
            "random_seed": random_seed,
            "total_nupack_calls": search_result["total_nupack_calls"],
        },
        input_params={
            "source_kind": "seqwalk_preselected_registry",
            **search_result["sequence_source"],
        },
        artifact_info={
            "dataset_dir": None,
            "dataset_toml": None,
            "dataset_npz": None,
        },
        nupack_params=search_result["nupack"],
        generation_data=search_result["generation_data"],
        validation_data=validation_data,
        seed_sequence_data=seed_sequence_data,
        seed_verified=search_result["seed_verified"],
        dataset_info={},
        extra_metadata={
            "benchmark_name": "figure_5",
            "dataset_kind": "hybrid_search_from_seqwalk",
            "stopped_reason": search_result["stopped_reason"],
        },
    )
    print(f"Saved hybrid SeqWalk search report to: {report_path}")
    return report_path


if __name__ == "__main__":
    seq_length = 16
    seqwalk_k = 6
    seqwalk_rcfree = False
    random_seed = 42

    fivep_ext = ""
    threep_ext = ""
    unwanted_substrings = ["GGGG", "CCCC"]
    apply_unwanted_to = "full"
    prevented_patterns = []

    nupack_params = {
        "material": "dna",
        "celsius": 37.0,
        "sodium": 0.05,
        "magnesium": 0.025,
    }

    min_ontarget = -23.0
    max_ontarget = -16.2
    offtarget_limit = -11.143
    self_energy_limit = -1.0
    initial_fresh_pair_count = 900
    total_nupack_budget = 10_000_000
    prune_fraction = 0.2
    vc_max_iterations = 1000

    figure_dir = Path(__file__).resolve().parent
    data_dir = figure_dir / "data"
    hybrid_report_path = data_dir / (
        f"figure5_hybrid_len{seq_length}_noflank_seqwalk_k{seqwalk_k}_seed{random_seed}.xlsx"
    )

    data_dir.mkdir(parents=True, exist_ok=True)
    hf.set_nupack_params(**nupack_params)
    hf.set_energy_type("total")

    print(
        f"Generating SeqWalk cores for length={seq_length}, k={seqwalk_k}, "
        f"RCfree={seqwalk_rcfree}, seed={random_seed}..."
    )
    random.seed(random_seed)
    seqwalk_cores = list(
        design.max_size(
            int(seq_length),
            int(seqwalk_k),
            alphabet="ACGT",
            RCfree=bool(seqwalk_rcfree),
            prevented_patterns=prevented_patterns,
            verbose=True,
        )
    )
    print(f"Generated {len(seqwalk_cores)} SeqWalk cores.")

    registry = sc.SequencePairRegistry(
        length=seq_length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        unwanted_substrings=unwanted_substrings,
        apply_unwanted_to=apply_unwanted_to,
        seed=random_seed,
        preselected_cores=seqwalk_cores,
    )
    registry.use_seqwalk = True
    registry.seqwalk_k = seqwalk_k
    registry.seqwalk_rcfree = seqwalk_rcfree
    registry.seqwalk_core_count = len(seqwalk_cores)

    write_hybrid_seqwalk_report(
        registry,
        output_path=hybrid_report_path,
        random_seed=random_seed,
        min_ontarget=min_ontarget,
        max_ontarget=max_ontarget,
        offtarget_limit=offtarget_limit,
        self_energy_limit=self_energy_limit,
        initial_fresh_pair_count=initial_fresh_pair_count,
        total_nupack_budget=total_nupack_budget,
        prune_fraction=prune_fraction,
        vc_max_iterations=vc_max_iterations,
    )
