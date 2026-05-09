#!/usr/bin/env python3
"""
Purpose:
    Run one live naive long-sequence benchmark condition from a generated
    condition TOML.
"""

import argparse
import os
from pathlib import Path
import random
import sys
import tomllib

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.naive_search_algorithm import naive_search
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data,
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)


def main():
    """
    Run one generated long-seq condition with the live naive algorithm.

    This runner is the execution counterpart to `prepare_conditions.py`. It
    consumes one generated condition TOML, rebuilds the live
    `SequencePairRegistry`, runs `naive_search(...)`, verifies the result with
    direct NUPACK recomputation, and writes the XLSX report plus the standard
    plots into the configured output folder.

    :returns: None
    :rtype: None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        required=True,
        help="Path to one long-seq condition TOML.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    with config_path.open("rb") as fh:
        config = tomllib.load(fh)

    run_cfg = config["run"]
    nupack_cfg = config["nupack"]
    naive_cfg = config.get("naive", {})

    RANDOM_SEED = int(run_cfg["random_seed"])
    random.seed(RANDOM_SEED)

    length = int(run_cfg["length"])
    fivep_ext = str(run_cfg.get("fivep_ext", ""))
    threep_ext = str(run_cfg.get("threep_ext", ""))
    unwanted_substrings = list(run_cfg.get("unwanted_substrings", []))
    apply_unwanted_to = str(run_cfg.get("apply_unwanted_to", "core"))

    hf.set_nupack_params(
        material=str(nupack_cfg["material"]),
        celsius=float(nupack_cfg["celsius"]),
        sodium=float(nupack_cfg["sodium"]),
        magnesium=float(nupack_cfg["magnesium"]),
    )

    sequence_pairs_object = sc.SequencePairRegistry(
        length=length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        unwanted_substrings=unwanted_substrings,
        apply_unwanted_to=apply_unwanted_to,
        seed=RANDOM_SEED,
        preselected_cores=None,
    )

    max_ontarget = float(run_cfg["max_ontarget"])
    min_ontarget = float(run_cfg["min_ontarget"])
    offtarget_limit = float(run_cfg["offtarget_limit"])
    self_energy_limit = float(run_cfg["self_energy_limit"])
    total_nupack_budget = int(run_cfg["total_nupack_budget"])
    progress_every = int(naive_cfg.get("progress_every", 250))

    fivep_label = f"5p_{fivep_ext}" if fivep_ext else "5p_none"
    threep_label = f"3p_{threep_ext}" if threep_ext else "3p_none"
    cutoff_label = str(offtarget_limit).replace("-", "m").replace(".", "p")
    stem = f"naive_{threep_label}_limit{cutoff_label}_seed{RANDOM_SEED}"
    benchmark_root = Path(__file__).resolve().parents[1]
    output_dir_cfg = config.get("output", {}).get("dir")
    if output_dir_cfg:
        output_dir = (
            Path(output_dir_cfg)
            if os.path.isabs(output_dir_cfg)
            else (benchmark_root / output_dir_cfg)
        )
    else:
        output_dir = benchmark_root / "data" / f"len{length}" / fivep_label
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Config: {config_path}")
    print(f"Output dir: {output_dir}")
    print(f"Total NUPACK budget: {total_nupack_budget}")

    search_result = naive_search(
        sequence_pairs_object,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        self_energy_limit,
        total_nupack_budget=total_nupack_budget,
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

    verified = verify_selected_pairs(selected_sequence_data, nupack_params=search_result["nupack"])
    validation_data = validate_selected_pairs(
        selected_sequence_data,
        verified,
        min_ontarget=min_ontarget,
        max_ontarget=max_ontarget,
        self_energy_limit=self_energy_limit,
        offtarget_limit=offtarget_limit,
    )
    report_path = write_hybrid_search_result_xlsx(
        output_dir / f"{stem}.xlsx",
        algorithm_name="naive_search",
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            **search_result["search_params"],
            "random_seed": RANDOM_SEED,
            "total_nupack_calls": search_result["total_nupack_calls"],
        },
        input_params={"source_kind": "on_the_fly_registry", **search_result["sequence_source"]},
        artifact_info={"dataset_dir": None, "dataset_toml": str(config_path), "dataset_npz": None},
        nupack_params=search_result["nupack"],
        generation_data=search_result["generation_data"],
        validation_data=validation_data,
        dataset_info={},
        extra_metadata={
            "benchmark_name": "long_seq",
            "best_generation_result_size": len(selected_sequence_data),
            "search.progress_every": progress_every,
            "search.attempts": search_result["attempts"],
            "stopped_reason": search_result["stopped_reason"],
        },
    )
    print(f"Saved verified run report to: {report_path}")

    sc.plot_on_off_target_histograms(
        verified["on_target_energies"],
        verified["off_target"],
        output_path=str(output_dir / f"{stem}_onoff.pdf"),
    )
    sc.plot_self_energy_histogram(
        [verified["self_energy_seqs"], verified["self_energy_rc_seqs"]],
        bins=30,
        output_path=str(output_dir / f"{stem}_self.pdf"),
    )


if __name__ == "__main__":
    main()
