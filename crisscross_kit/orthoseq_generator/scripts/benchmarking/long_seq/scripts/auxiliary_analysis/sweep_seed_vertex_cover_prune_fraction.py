#!/usr/bin/env python3
"""
Sweep prune fractions on one saved long-seq seed graph.

Loads one saved TTTT init graph, rebuilds the seed conflict graph, and compares
retained set sizes for different prune fractions.
"""

from __future__ import annotations

from pathlib import Path
import random
import sys

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[6]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import (
    load_metadata,
    load_offtarget_matrices,
    load_seed_pairs,
)
from orthoseq_generator.vertex_cover_algorithms import (
    build_edges,
    iterative_vertex_cover_refinement,
)


def num_vertices_to_remove(vertex_count: int, prune_fraction: float) -> int:
    return max(1, int(round(vertex_count * prune_fraction)))


def load_seed_graph(report_path: Path):
    metadata = load_metadata(report_path)
    seed_pairs_df = load_seed_pairs(report_path)
    offtarget_dict = load_offtarget_matrices(report_path, family="seed")
    pair_ids = seed_pairs_df["global_pair_id"].astype(int).tolist()
    offtarget_limit = float(metadata["search.offtarget_limit"])
    edges = build_edges(offtarget_dict, pair_ids, offtarget_limit)
    return metadata, pair_ids, edges, offtarget_limit


def run_sweep(pair_ids, edges, prune_fractions, max_iterations, random_seed, context):
    result_rows = []
    trajectory_rows = []
    for prune_fraction in prune_fractions:
        random.seed(random_seed)
        vertex_cover, size_trajectories = iterative_vertex_cover_refinement(
            pair_ids,
            edges,
            num_vertices_to_remove=num_vertices_to_remove(len(pair_ids), prune_fraction),
            max_iterations=max_iterations,
            show_progress=False,
        )
        trajectory = size_trajectories[0]
        result_rows.append(
            {
                "report_name": context["report_name"],
                "batch_name": context["batch_name"],
                "sequence_length": context["sequence_length"],
                "five_prime_extension": context["five_prime_extension"],
                "init_count": context["init_count"],
                "offtarget_limit": context["offtarget_limit"],
                "max_iterations": context["max_iterations"],
                "random_seed": random_seed,
                "prune_fraction": prune_fraction,
                "num_vertices_to_remove": num_vertices_to_remove(len(pair_ids), prune_fraction),
                "seed_pair_count": len(pair_ids),
                "edge_count": len(edges),
                "vertex_cover_size": len(vertex_cover),
                "retained_pair_count": len(pair_ids) - len(vertex_cover),
                "trajectory_length": len(trajectory),
            }
        )
        for iteration, independent_set_size in enumerate(trajectory):
            trajectory_rows.append(
                {
                    "report_name": context["report_name"],
                    "batch_name": context["batch_name"],
                    "sequence_length": context["sequence_length"],
                    "five_prime_extension": context["five_prime_extension"],
                    "init_count": context["init_count"],
                    "offtarget_limit": context["offtarget_limit"],
                    "prune_fraction": prune_fraction,
                    "random_seed": random_seed,
                    "iteration": iteration,
                    "independent_set_size": independent_set_size,
                }
            )
    return pd.DataFrame(result_rows), pd.DataFrame(trajectory_rows)


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]

    batch_name = "batch_x_TTTT_sigma1p0_seed41"
    lengths = [10, 16, 20]
    init_counts = [250, 450, 900]
    prune_fractions = [0.025, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1]
    max_iterations = 1000
    random_seeds = [42,43]
    write_excel = True

    output_dir = (
        module_dir
        / "data"
        / batch_name
        / "auxiliary_analysis"
        / "prune_fraction_sweep"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    for length in lengths:
        for init_count in init_counts:
            report_path = (
                module_dir
                / "data"
                / batch_name
                / f"len{length}"
                / "5p_TTTT"
                / f"hybrid_len{length}_5p_TTTT_limitm8p16_budget10000000_init{init_count}_seed41.xlsx"
            )

            metadata, pair_ids, edges, offtarget_limit = load_seed_graph(report_path)

            for random_seed in random_seeds:
                output_path = output_dir / f"{report_path.stem}_prune_fraction_sweep_vcseed{random_seed}.xlsx"
                context = {
                    "report_name": report_path.name,
                    "report_path": str(report_path),
                    "batch_name": report_path.parents[2].name,
                    "length_dir": report_path.parents[1].name,
                    "five_prime_dir": report_path.parents[0].name,
                    "sequence_length": metadata.get("design.length", report_path.parents[1].name.removeprefix("len")),
                    "five_prime_extension": metadata.get(
                        "design.five_prime_extension",
                        report_path.parents[0].name.removeprefix("5p_"),
                    ),
                    "init_count": metadata.get("search.initial_fresh_pair_count"),
                    "offtarget_limit": offtarget_limit,
                    "max_iterations": max_iterations,
                    "random_seed": random_seed,
                    "prune_fractions": ", ".join(str(value) for value in prune_fractions),
                }
                results_df, trajectories_df = run_sweep(
                    pair_ids=pair_ids,
                    edges=edges,
                    prune_fractions=prune_fractions,
                    max_iterations=max_iterations,
                    random_seed=random_seed,
                    context=context,
                )
                context_rows = [{"key": key, "value": value} for key, value in context.items()]
                context_rows.extend(
                    {"key": f"metadata.{key}", "value": value}
                    for key, value in sorted(metadata.items())
                )
                context_df = pd.DataFrame(context_rows)

                print(f"report: {report_path}")
                print(f"vc_random_seed: {random_seed}")
                print(f"offtarget_limit: {offtarget_limit}")
                print(f"seed_pair_count: {len(pair_ids)}")
                print(f"edge_count: {len(edges)}")
                print(results_df.to_string(index=False))

                if write_excel:
                    with pd.ExcelWriter(output_path) as writer:
                        results_df.to_excel(writer, sheet_name="results", index=False)
                        trajectories_df.to_excel(writer, sheet_name="trajectories", index=False)
                        context_df.to_excel(writer, sheet_name="context", index=False)
                    print(f"wrote xlsx: {output_path}")
