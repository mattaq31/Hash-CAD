#!/usr/bin/env python3

"""
Prepare a direct SeqWalk max-orthogonality Figure 5 dataset.

This script generates a direct SeqWalk `max_orthogonality` library, verifies
the full generated set thermodynamically, and writes a canonical XLSX report
for the pure SeqWalk comparison arm in Figure 5.
"""

from pathlib import Path
import random
import sys

import numpy as np
from seqwalk import design

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.search_reporting import (
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)


def build_seqwalk_selected_sequence_data(seqwalk_cores, fivep_ext, threep_ext):
    rows = []
    for idx, core_seq in enumerate(seqwalk_cores):
        seq = f"{fivep_ext}{core_seq}{threep_ext}"
        rc_seq = f"{fivep_ext}{sc.revcom(core_seq)}{threep_ext}"
        rows.append(
            {
                "pair_idx": idx,
                "global_pair_id": idx,
                "seq": seq,
                "rc_seq": rc_seq,
                "origin_core": core_seq,
                "origin_seq_with_flank": seq,
            }
        )
    return rows


def write_verified_seqwalk_report(
    seqwalk_cores,
    *,
    output_path,
    nupack_params,
    random_seed,
    length,
    fivep_ext,
    threep_ext,
    seqwalk_rcfree,
    seqwalk_alphabet,
    seqwalk_gc_lims,
    seqwalk_prevented_patterns,
    requested_target_count,
):
    selected_sequence_data = build_seqwalk_selected_sequence_data(
        seqwalk_cores,
        fivep_ext,
        threep_ext,
    )
    pair_count = len(selected_sequence_data)

    print(f"Computing energies for {pair_count} direct SeqWalk max-orthogonality sequence pairs...")
    verified = verify_selected_pairs(selected_sequence_data, nupack_params=nupack_params)
    on_target = np.asarray(verified["on_target_energies"], dtype=float)
    self_seq = np.asarray(verified["self_energy_seqs"], dtype=float)
    self_rc = np.asarray(verified["self_energy_rc_seqs"], dtype=float)
    off_target = verified["off_target"]
    observed_min_ontarget = float(np.min(on_target))
    observed_max_ontarget = float(np.max(on_target))
    observed_min_offtarget = float(
        np.min(
            np.concatenate(
                [
                    off_target["handle_handle_energies"].ravel(),
                    off_target["antihandle_handle_energies"].ravel(),
                    off_target["antihandle_antihandle_energies"].ravel(),
                ]
            )[
                np.concatenate(
                    [
                        off_target["handle_handle_energies"].ravel(),
                        off_target["antihandle_handle_energies"].ravel(),
                        off_target["antihandle_antihandle_energies"].ravel(),
                    ]
                )
                != 0.0
            ]
        )
    )
    observed_self_limit = float(np.min(np.concatenate([self_seq, self_rc])))
    validation_data = validate_selected_pairs(
        selected_sequence_data,
        verified,
        min_ontarget=observed_min_ontarget,
        max_ontarget=observed_max_ontarget,
        self_energy_limit=observed_self_limit,
        offtarget_limit=observed_min_offtarget,
    )
    total_nupack_calls = int(pair_count + 2 * pair_count * pair_count)

    report_path = write_hybrid_search_result_xlsx(
        output_path,
        algorithm_name="figure5_seqwalk_max_orthogonality",
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            "offtarget_limit": observed_min_offtarget,
            "max_ontarget": observed_max_ontarget,
            "min_ontarget": observed_min_ontarget,
            "self_energy_limit": observed_self_limit,
            "initial_fresh_pair_count": None,
            "total_nupack_budget": None,
            "prune_fraction": None,
            "vc_max_iterations": None,
            "random_seed": random_seed,
            "total_nupack_calls": total_nupack_calls,
            "search_duration_s": None,
        },
        input_params={
            "source_kind": "seqwalk_max_orthogonality",
            "length": length,
            "fivep_ext": fivep_ext,
            "threep_ext": threep_ext,
            "unwanted_substrings": None,
            "apply_unwanted_to": None,
            "used_seqwalk": True,
            "seqwalk_k": None,
            "seqwalk_rcfree": seqwalk_rcfree,
            "seqwalk_core_count": pair_count,
        },
        artifact_info={
            "dataset_dir": str(output_path.parent),
            "dataset_toml": None,
            "dataset_npz": None,
        },
        nupack_params=nupack_params,
        generation_data=[],
        validation_data=validation_data,
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
            "benchmark_name": "figure_5",
            "dataset_kind": "seqwalk_max_orthogonality",
            "sampling_method": "full_max_orthogonality_library",
            "seqwalk.requested_target_count": requested_target_count,
            "seqwalk.alphabet": seqwalk_alphabet,
            "seqwalk.gc_lims": seqwalk_gc_lims,
            "seqwalk.prevented_patterns": seqwalk_prevented_patterns,
            "observed.min_ontarget": observed_min_ontarget,
            "observed.max_ontarget": observed_max_ontarget,
            "observed.min_offtarget": observed_min_offtarget,
            "observed.self_energy_limit": observed_self_limit,
        },
    )
    print(f"Saved direct SeqWalk max-orthogonality dataset to: {report_path}")
    return report_path


if __name__ == "__main__":
    seq_length = 16
    random_seed = 42
    target_count = 40

    fivep_ext = ""
    threep_ext = ""

    seqwalk_rcfree = True
    seqwalk_alphabet = "ACGT"
    seqwalk_gc_lims = (7, 11)
    seqwalk_prevented_patterns = ["GGGG", "CCCC"]

    nupack_params = {
        "material": "dna",
        "celsius": 37.0,
        "sodium": 0.05,
        "magnesium": 0.025,
    }
    figure_dir = Path(__file__).resolve().parent
    data_dir = figure_dir / "data"

    hf.set_nupack_params(**nupack_params)
    hf.set_energy_type("total")

    print(
        f"Generating SeqWalk max-orthogonality cores for N={target_count}, "
        f"L={seq_length}, RCfree={seqwalk_rcfree}, seed={random_seed}..."
    )
    random.seed(random_seed)
    seqwalk_cores = list(
        design.max_orthogonality(
            int(target_count),
            int(seq_length),
            alphabet=seqwalk_alphabet,
            RCfree=bool(seqwalk_rcfree),
            GClims=seqwalk_gc_lims,
            prevented_patterns=seqwalk_prevented_patterns,
            verbose=True,
        )
    )
    print(f"Generated {len(seqwalk_cores)} SeqWalk max-orthogonality cores.")

    if len(seqwalk_cores) < target_count:
        raise RuntimeError(
            f"SeqWalk returned only {len(seqwalk_cores)} cores for requested target size {target_count}."
        )

    generated_core_count = len(seqwalk_cores)
    output_path = data_dir / (
        f"figure5_seqwalk_max_orthogonality_len{seq_length}_"
        f"n{generated_core_count}_seed{random_seed}.xlsx"
    )

    write_verified_seqwalk_report(
        seqwalk_cores,
        output_path=output_path,
        nupack_params=nupack_params,
        random_seed=random_seed,
        length=seq_length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        seqwalk_rcfree=seqwalk_rcfree,
        seqwalk_alphabet=seqwalk_alphabet,
        seqwalk_gc_lims=seqwalk_gc_lims,
        seqwalk_prevented_patterns=seqwalk_prevented_patterns,
        requested_target_count=target_count,
    )
