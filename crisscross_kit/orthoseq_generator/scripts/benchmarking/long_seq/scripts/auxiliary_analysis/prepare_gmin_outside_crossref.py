#!/usr/bin/env python3
"""Add GMIN to the saved initial-seed/outside-pool comparison without repeating the original preparation."""

from pathlib import Path
import random

import pandas as pd

from prepare_init900_outside_crossref import (
    build_matrix_column_labels,
    build_matrix_df,
    compute_flag_rows_against_selected,
    matrix_df_to_numpy_dict,
    row_to_pair,
)
from orthoseq_generator import helper_functions as hf
from orthoseq_generator.search_algorithm import _num_vertices_to_remove
from orthoseq_generator.search_report_reader import load_metadata, load_offtarget_matrices, load_seed_pairs
from orthoseq_generator.vertex_cover_algorithms import build_edges, iterative_vertex_cover_refinement


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    random_seed = 41
    tiebreak = None
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "len12", "5p_TTTT"),
        ("batch_x______sigma1p0_seed41", "len12", "5p_none"),
    ]

    for batch_name, length_label, condition_label in targets:
        batch_dir = module_dir / "data" / batch_name
        data_dir = batch_dir / length_label / condition_label
        report_stem = f"{length_label}_{condition_label}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init900_seed41.xlsx"
        output_dir = batch_dir / "auxiliary_analysis" / "init900_outside_crossref"
        output_dir = output_dir / f"{length_label}_{condition_label}"
        analysis_workbook = output_dir / "compatibility_analysis.xlsx"
        output_path = output_dir / "compatibility_analysis_gmin.xlsx"

        print(f"loading {analysis_workbook}", flush=True)
        sheets = pd.read_excel(analysis_workbook, sheet_name=None)
        outside_df = sheets["outside_pool"]
        comparison_sets_df = sheets["comparison_sets"]
        metadata = load_metadata(hybrid_report)
        seed_pair_df = load_seed_pairs(hybrid_report)
        indices = seed_pair_df["global_pair_id"].astype(int).tolist()
        seed_matrix_dict = load_offtarget_matrices(hybrid_report, family="seed")
        offtarget_limit = float(metadata["search.offtarget_limit"])
        prune_fraction = float(metadata["search.prune_fraction"])
        max_iterations = int(metadata["search.vc_max_iterations"])
        edges = build_edges(matrix_df_to_numpy_dict(seed_matrix_dict), indices, offtarget_limit)

        random.seed(random_seed)
        print(f"running GMIN refinement on {len(indices)} initial pairs...", flush=True)
        vertex_cover, _ = iterative_vertex_cover_refinement(
            indices, edges, num_vertices_to_remove=_num_vertices_to_remove(len(indices), prune_fraction),
            max_iterations=max_iterations, heuristics="Gmin", tiebreak=tiebreak,
        )
        gmin_df = seed_pair_df.loc[~seed_pair_df["global_pair_id"].isin(vertex_cover)].copy().reset_index(drop=True)
        gmin_pairs = [row_to_pair(row) for _, row in gmin_df.iterrows()]
        outside_pairs = {row_to_pair(row) for _, row in outside_df.iterrows()}
        if outside_pairs.intersection(gmin_pairs):
            raise ValueError("GMIN overlaps the saved outside pool; remove shared rows for all methods first.")

        # IDs belong to separate search runs; match cached columns by the actual sequence pairs.
        cached_flags = {}
        for set_name, sheet_name in [
            ("naive_first_m", "outside_vs_naive"),
            ("hybrid_seed_independent", "outside_vs_graph"),
        ]:
            selected_df = comparison_sets_df.loc[comparison_sets_df["set_name"] == set_name].sort_values("set_order")
            for (_, row), column in zip(selected_df.iterrows(), build_matrix_column_labels(selected_df)):
                cached_flags[row_to_pair(row)] = sheets[sheet_name][column].tolist()

        missing_pairs = [pair for pair in gmin_pairs if pair not in cached_flags]
        print(
            f"GMIN selected={len(gmin_pairs)}, cached={len(gmin_pairs) - len(missing_pairs)}, "
            f"new comparisons={len(missing_pairs)} x {len(outside_df)}", flush=True,
        )
        hf.set_nupack_params(
            material=str(metadata["nupack.material"]), celsius=float(metadata["nupack.celsius"]),
            sodium=float(metadata["nupack.sodium"]), magnesium=float(metadata["nupack.magnesium"]),
        )
        hf.set_energy_type(str(metadata["nupack.energy_type"]))
        if missing_pairs:
            missing_flags = compute_flag_rows_against_selected(
                outside_df, "gmin_seed_independent", missing_pairs, offtarget_limit,
            )
            for index, pair in enumerate(missing_pairs):
                cached_flags[pair] = [row[index] for row in missing_flags]

        gmin_flag_rows = [
            [cached_flags[pair][index] for pair in gmin_pairs] for index in range(len(outside_df))
        ]
        sheets["outside_vs_gmin"] = build_matrix_df(outside_df, gmin_flag_rows, gmin_df)
        gmin_df["set_name"] = "gmin_seed_independent"
        gmin_df["set_order"] = range(len(gmin_df))
        gmin_df["outside_violation_count"] = [sum(cached_flags[pair]) for pair in gmin_pairs]
        gmin_df["outside_conflict_probability"] = gmin_df["outside_violation_count"] / len(outside_df)
        sheets["inside_to_outside"] = pd.concat([sheets["inside_to_outside"], gmin_df], ignore_index=True)

        summary = {
            "gmin_source_workbook": str(analysis_workbook),
            "gmin_hybrid_report": str(hybrid_report),
            "gmin_random_seed": random_seed,
            "gmin_tiebreak": tiebreak,
            "gmin_prune_fraction": prune_fraction,
            "gmin_max_iterations": max_iterations,
            "gmin_seed_independent_size": len(gmin_pairs),
            "gmin_cached_pair_count": len(gmin_pairs) - len(missing_pairs),
            "gmin_new_pair_count": len(missing_pairs),
        }
        sheets["summary"] = pd.concat([
            sheets["summary"], pd.DataFrame([{"key": key, "value": value} for key, value in summary.items()]),
        ], ignore_index=True)
        with pd.ExcelWriter(output_path) as writer:
            for sheet_name, sheet_df in sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"GMIN mean conflict probability: {gmin_df['outside_conflict_probability'].mean():.4f}", flush=True)
        print(f"Saved: {output_path}", flush=True)
