"""Compare standalone and iterative GMIN/GMAX from a job TOML, saving and resuming each seed."""

import argparse
from pathlib import Path
import random
import sys
import time
import tomllib

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from orthoseq_generator.search_report_reader import load_metadata, load_offtarget_matrices, load_seed_pairs
from orthoseq_generator.search_algorithm import _num_vertices_to_remove
from orthoseq_generator.vertex_cover_algorithms import (
    build_edges, greedy_vertex_cover_gmin, greedy_vertex_cover_gmax, iterative_vertex_cover_refinement, rank_vertices,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to a generated comparison TOML.")
    args = parser.parse_args()
    config_text = Path(args.config).read_text()
    config = tomllib.loads(config_text)
    run_cfg = config["run"]
    project_dir = Path(__file__).resolve().parents[5]
    output_path = project_dir / config["output"]["file"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".tmp.xlsx")
    print(f"Results: {output_path}", flush=True)

    result_rows = []
    if output_path.exists():
        saved_config = pd.read_excel(output_path, sheet_name="config").iloc[0]["toml"]
        if tomllib.loads(saved_config) != config:
            raise ValueError("The existing workbook uses different settings; choose a new output file.")
        result_rows = pd.read_excel(output_path, sheet_name="results").to_dict("records")
    completed = {(row["init_count"], row["algorithm"], row["random_seed"]) for row in result_rows}

    for graph_cfg in config["graphs"]:
        init_count = graph_cfg["init_count"]
        report_path = project_dir / graph_cfg["report"]
        print(f"Length: {run_cfg['length']}, initial pool: {init_count}", flush=True)
        metadata = load_metadata(report_path)
        max_iterations = int(metadata["search.vc_max_iterations"])
        energy_cutoff = float(metadata["search.offtarget_limit"])
        seed_pairs_df = load_seed_pairs(report_path)
        pair_ids = seed_pairs_df["global_pair_id"].astype(int).tolist()
        # Stronger binding has a more negative free energy, so negate it before ranking.
        vertex_ranks = rank_vertices(dict(zip(pair_ids, -seed_pairs_df["on_target_energy_verified"])))
        offtarget_dict = load_offtarget_matrices(report_path, family="seed")
        offtarget_dict = {key: matrix.to_numpy() for key, matrix in offtarget_dict.items()}
        edges = build_edges(offtarget_dict, pair_ids, energy_cutoff)
        num_vertices_to_remove = _num_vertices_to_remove(len(pair_ids), run_cfg["prune_fraction"])

        for algorithm in run_cfg["algorithms"]:
            iterative = algorithm.endswith("_iterative")
            tiebreak = "rank" if "_rank" in algorithm else "rule" if "_rule" in algorithm else None
            ranks = vertex_ranks if tiebreak == "rank" else None
            for random_seed in run_cfg["random_seeds"]:
                if (init_count, algorithm, random_seed) in completed:
                    continue
                print(f"{algorithm}, seed: {random_seed}", flush=True)
                random.seed(random_seed)
                start_t = time.perf_counter()
                if iterative:
                    vertex_cover, _ = iterative_vertex_cover_refinement(
                        pair_ids, edges, avoid_V=None, num_vertices_to_remove=num_vertices_to_remove,
                        max_iterations=max_iterations, show_progress=False,
                        heuristics="Gmin" if algorithm.startswith("gmin_") else "Gmax",
                        tiebreak=tiebreak, vertex_ranks=ranks,
                    )
                elif algorithm.startswith("gmax_"):
                    vertex_cover = greedy_vertex_cover_gmax(edges, cleanup=True, tiebreak=tiebreak, vertex_ranks=ranks)
                else:
                    vertex_cover = greedy_vertex_cover_gmin(pair_ids, edges, tiebreak=tiebreak, vertex_ranks=ranks)
                duration_s = time.perf_counter() - start_t
                retained_pair_ids = sorted(set(pair_ids) - vertex_cover)
                result_rows.append({
                    "batch_name": run_cfg["batch_name"],
                    "length": run_cfg["length"],
                    "init_count": init_count,
                    "report": graph_cfg["report"],
                    "energy_cutoff": energy_cutoff,
                    "algorithm": algorithm,
                    "rank_source": "negative_on_target_energy" if ranks is not None else None,
                    "prune_fraction": run_cfg["prune_fraction"] if iterative else None,
                    "num_vertices_to_remove": num_vertices_to_remove if iterative else None,
                    "max_iterations": max_iterations if iterative else None,
                    "random_seed": random_seed,
                    "retained_pair_count": len(retained_pair_ids),
                    "retained_pair_ids": ",".join(map(str, retained_pair_ids)),
                    "duration_s": duration_s,
                })
                results_df = pd.DataFrame(result_rows)
                summary_df = results_df.groupby(
                    ["length", "init_count", "algorithm", "prune_fraction"], sort=False, dropna=False,
                ).agg(
                    runs=("retained_pair_count", "count"),
                    mean_retained=("retained_pair_count", "mean"),
                    min_retained=("retained_pair_count", "min"),
                    max_retained=("retained_pair_count", "max"),
                    mean_duration_s=("duration_s", "mean"),
                )
                # Keep the previous workbook intact if interrupted during an Excel write.
                with pd.ExcelWriter(temporary_path) as writer:
                    results_df.to_excel(writer, sheet_name="results", index=False)
                    summary_df.to_excel(writer, sheet_name="summary")
                    pd.DataFrame({"toml": [config_text]}).to_excel(writer, sheet_name="config", index=False)
                temporary_path.replace(output_path)
                completed.add((init_count, algorithm, random_seed))
                print(f"Retained: {len(retained_pair_ids)}, duration: {duration_s:.2f} s", flush=True)

    print(f"Saved: {output_path}")
