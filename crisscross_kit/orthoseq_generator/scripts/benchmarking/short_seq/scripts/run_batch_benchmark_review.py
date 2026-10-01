"""Run ordered naive and GMIN across the saved short-sequence datasets for one review benchmark seed."""

import argparse
from datetime import datetime
from pathlib import Path
import sys
import time
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_algorithms import run_naive_search_to_xlsx, run_vertex_cover_search_to_xlsx
from benchmark_analysis import find_offtarget_limits_for_target_densities
from benchmark_dataset_tools import load_dataset, self_energy_limit_from_unpaired_fraction
from run_batch_benchmark import discover_dataset_dirs, write_summary_toml
from orthoseq_generator.search_report_reader import load_metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to one review benchmark job TOML.")
    args = parser.parse_args()
    config = tomllib.loads(Path(args.config).read_text())
    run_cfg = config["run"]

    module_dir = Path(__file__).resolve().parents[1]
    dataset_parent_name = run_cfg["dataset_parent_name"]
    benchmark_name = run_cfg["benchmark_name"]
    target_conflict_densities = run_cfg["target_conflict_densities"]
    seed = run_cfg["random_seed"]
    target_unpaired_fraction = run_cfg["target_unpaired_fraction"]
    vc_core_params = config["vertex_cover"]
    algorithms = run_cfg["algorithms"]
    if any(algorithm not in ("naive_ordered", "vertex_cover_GMIN") for algorithm in algorithms):
        raise ValueError("Review algorithms must be 'naive_ordered' or 'vertex_cover_GMIN'.")

    parent_dir = module_dir / "data" / dataset_parent_name
    dataset_dirs = discover_dataset_dirs(parent_dir)
    summary_path = parent_dir / f"benchmark_summary_{benchmark_name}_seed{seed}.toml"
    summary_runs = {}
    created_at = datetime.now().isoformat(timespec="seconds")
    if summary_path.exists():
        saved_summary = tomllib.loads(summary_path.read_text())
        created_at = saved_summary["created_at"]
        summary_runs = {
            (run["dataset_name"], run["target_conflict_density"], run["algorithm"]): run
            for run in saved_summary["runs"]
        }

    print(f"dataset parent: {parent_dir}", flush=True)
    print(f"benchmark name: {benchmark_name}, seed: {seed}", flush=True)
    print(f"discovered datasets: {[dataset_dir.name for dataset_dir in dataset_dirs]}", flush=True)

    for dataset_dir in dataset_dirs:
        dataset = load_dataset(dataset_dir)
        inputs = dataset["metadata"]["inputs"]
        derived = dataset["metadata"]["derived"]
        nupack = dataset["metadata"]["nupack"]
        cutoff_summaries = find_offtarget_limits_for_target_densities(dataset, target_conflict_densities)
        self_energy_limit = self_energy_limit_from_unpaired_fraction(target_unpaired_fraction, float(nupack["celsius"]))
        results_dir = dataset_dir / "results" / benchmark_name
        results_dir.mkdir(parents=True, exist_ok=True)

        for cutoff_summary in cutoff_summaries:
            target_density = float(cutoff_summary["target_conflict_density"])
            offtarget_limit = float(cutoff_summary["selected_offtarget_limit"])
            density_label = str(target_density).replace(".", "p")
            cutoff_label = str(offtarget_limit).replace(".", "p")

            for algorithm in algorithms:
                report_path = results_dir / f"density{density_label}_{algorithm}_limit{cutoff_label}_seed{seed}.xlsx"
                run_key = (dataset_dir.name, target_density, algorithm)
                duration_s = summary_runs.get(run_key, {}).get("duration_s")
                if report_path.exists():
                    metadata = load_metadata(report_path)
                    expected = {
                        "algorithm_name": algorithm, "benchmark_name": benchmark_name,
                        "input.length": int(inputs["length"]), "input.fivep_ext": inputs["fivep_ext"] or None,
                        "input.threep_ext": inputs["threep_ext"] or None,
                        "search.random_seed": seed, "search.offtarget_limit": offtarget_limit,
                        "search.self_energy_limit": self_energy_limit,
                        "search.min_ontarget": float(derived["min_ontarget_energy"]),
                        "search.max_ontarget": float(derived["max_ontarget_energy"]),
                    }
                    if algorithm == "vertex_cover_GMIN":
                        expected.update({f"search.{key}": value for key, value in vc_core_params.items()})
                    if any(metadata.get(key) != value for key, value in expected.items()):
                        raise ValueError(f"Saved report has different settings: {report_path}")
                    print(f"Skipping completed report: {report_path.name}", flush=True)
                else:
                    print(f"{dataset_dir.name} | density={target_density} | {algorithm} | seed={seed}", flush=True)
                    temporary_report = report_path.with_suffix(".tmp.xlsx")
                    start_t = time.perf_counter()
                    if algorithm == "naive_ordered":
                        run_naive_search_to_xlsx(
                            dataset_dir, output_path=temporary_report, offtarget_limit=offtarget_limit,
                            self_energy_limit=self_energy_limit, random_seed=seed, ordering="weaker_first",
                        )
                    else:
                        run_vertex_cover_search_to_xlsx(
                            dataset_dir, output_path=temporary_report, offtarget_limit=offtarget_limit,
                            self_energy_limit=self_energy_limit, random_seed=seed, heuristics="Gmin", **vc_core_params,
                        )
                    temporary_report.replace(report_path)
                    duration_s = time.perf_counter() - start_t
                    metadata = load_metadata(report_path)
                    print(f"Retained: {metadata['found_pair_count']}, duration: {duration_s:.2f} s", flush=True)

                run = {
                    "dataset_name": dataset_dir.name, "length": int(inputs["length"]),
                    "fivep_ext": str(inputs["fivep_ext"]), "threep_ext": str(inputs["threep_ext"]),
                    "has_tttt5p": inputs["fivep_ext"] == "TTTT", "algorithm": algorithm, "seed": seed,
                    "target_conflict_density": target_density, "selected_offtarget_limit": offtarget_limit,
                    "achieved_conflict_density": float(cutoff_summary["achieved_conflict_density"]),
                    "self_energy_limit": self_energy_limit, "found_pair_count": int(metadata["found_pair_count"]),
                    "report_path": str(report_path),
                }
                if algorithm == "vertex_cover_GMIN":
                    run.update(vc_core_params)
                if duration_s is not None:
                    run["duration_s"] = duration_s
                summary_runs[run_key] = run
                # Separate per-seed summaries prevent independent jobs from overwriting each other.
                temporary_summary = summary_path.with_suffix(".tmp.toml")
                write_summary_toml(
                    temporary_summary, created_at=created_at, benchmark_name=benchmark_name, dataset_parent=parent_dir,
                    target_conflict_densities=target_conflict_densities, seeds=[seed],
                    target_unpaired_fraction=target_unpaired_fraction, runs=list(summary_runs.values()),
                )
                temporary_summary.replace(summary_path)

    print(f"Saved: {summary_path}", flush=True)
