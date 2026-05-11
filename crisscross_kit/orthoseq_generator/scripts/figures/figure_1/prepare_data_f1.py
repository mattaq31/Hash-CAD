#!/usr/bin/env python3

"""
Prepare the Figure 1 random long-sequence dataset.

This script samples valid 12-mer sequence pairs without applying any search
filters, then computes the full on-target and off-target energy data and saves
the result as an XLSX workbook for plotting.
"""

from pathlib import Path
import random
import sys

import numpy as np

PACKAGE_DIR = Path(__file__).resolve().parents[4]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.search_reporting import verify_selected_pairs, write_hybrid_search_result_xlsx


if __name__ == "__main__":
    length = 12
    pair_count = 1000
    random_seed = 41

    fivep_ext = ""
    threep_ext = ""
    unwanted_substrings = ["GGGG", "CCCC"]
    apply_unwanted_to = "full"

    material = "dna"
    celsius = 37.0
    sodium = 0.05
    magnesium = 0.025
    nupack_params = {
        "material": material,
        "celsius": celsius,
        "sodium": sodium,
        "magnesium": magnesium,
    }

    output_path = (
        Path(__file__).resolve().parent
        / "data"
        / f"figure1_len{length}_noflank_random_{pair_count}pairs_seed{random_seed}.xlsx"
    )

    random.seed(random_seed)
    hf.set_nupack_params(**nupack_params)

    registry = sc.SequencePairRegistry(
        length=length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        unwanted_substrings=unwanted_substrings,
        apply_unwanted_to=apply_unwanted_to,
        seed=random_seed,
        preselected_cores=None,
    )

    selected_sequence_data = []
    seen_pair_ids = set()

    print(f"Sampling {pair_count} valid sequence pairs...")
    while len(selected_sequence_data) < pair_count:
        pair_id, (seq, rc_seq) = registry.sample_pair()
        if pair_id in seen_pair_ids:
            continue
        seen_pair_ids.add(pair_id)
        selected_sequence_data.append(
            {
                "pair_idx": len(selected_sequence_data),
                "global_pair_id": int(pair_id),
                "seq": seq,
                "rc_seq": rc_seq,
            }
        )

    print("Computing on-target and off-target energies...")
    verified = verify_selected_pairs(
        selected_sequence_data,
        nupack_params=nupack_params,
    )

    on_target = np.asarray(verified["on_target_energies"], dtype=float)
    total_nupack_calls = int(pair_count + 2 * pair_count * pair_count)

    report_path = write_hybrid_search_result_xlsx(
        output_path,
        algorithm_name="figure1_random_sample",
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            "offtarget_limit": None,
            "max_ontarget": None,
            "min_ontarget": None,
            "self_energy_limit": None,
            "initial_fresh_pair_count": None,
            "generations": None,
            "allowed_violations_initial": None,
            "fresh_pair_search_budget": None,
            "total_nupack_budget": None,
            "prune_fraction": None,
            "fresh_pair_scale": None,
            "vc_max_iterations": None,
            "random_seed": random_seed,
            "total_nupack_calls": total_nupack_calls,
            "num_vertices_to_remove_effective": None,
            "search_duration_s": None,
        },
        input_params={
            "source_kind": "random_registry_sample",
            "length": length,
            "fivep_ext": fivep_ext,
            "threep_ext": threep_ext,
            "unwanted_substrings": unwanted_substrings,
            "apply_unwanted_to": apply_unwanted_to,
        },
        artifact_info={
            "dataset_dir": str(output_path.parent),
            "dataset_toml": None,
            "dataset_npz": None,
        },
        nupack_params=nupack_params,
        generation_data=[],
        validation_data=[
            {"item": "selection", "value": "no on-target, self-energy, or off-target filters applied"},
        ],
        dataset_info={
            "range_sigma": None,
            "random_seed": random_seed,
            "total_candidate_count": pair_count,
            "matrix_candidate_count": pair_count,
            "mean_ontarget_energy": float(np.mean(on_target)),
            "std_ontarget_energy": float(np.std(on_target)),
            "min_ontarget_energy": float(np.min(on_target)),
            "max_ontarget_energy": float(np.max(on_target)),
        },
        extra_metadata={
            "benchmark_name": "figure_1",
            "dataset_kind": "selection_free_random_sample",
            "sampling_method": "direct_registry_sampling",
        },
    )

    print(f"Saved dataset to: {report_path}")
