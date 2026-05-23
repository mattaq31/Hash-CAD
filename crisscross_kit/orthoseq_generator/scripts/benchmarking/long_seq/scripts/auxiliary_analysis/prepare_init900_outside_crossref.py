#!/usr/bin/env python3
"""
Prepare initial-seed and outside-pool cross-reference data for one long-seq run.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[6]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.search_report_reader import (
    load_found_pairs,
    load_metadata,
    load_offtarget_matrices,
    load_search_progress,
    load_seed_pairs,
)
from orthoseq_generator.vertex_cover_algorithms import build_edges


def canonical_pair(seq: str, rc_seq: str) -> tuple[str, str]:
    return (seq, rc_seq) if seq <= rc_seq else (rc_seq, seq)


def row_to_pair(row: pd.Series) -> tuple[str, str]:
    return canonical_pair(str(row["seq"]), str(row["rc_seq"]))


def unpack_energy(result) -> float:
    return float(result[0] if isinstance(result, tuple) else result)


def parse_unwanted_substrings(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    text = str(value).strip()
    if not text:
        return []
    parsed = ast.literal_eval(text)
    return [str(item) for item in parsed]


def matrix_df_to_numpy_dict(matrix_dict: dict[str, pd.DataFrame]) -> dict[str, object]:
    return {key: df.to_numpy(dtype=float) for key, df in matrix_dict.items()}


def compute_seed_probability_df(
    seed_pair_df: pd.DataFrame,
    seed_matrix_dict: dict[str, pd.DataFrame],
    offtarget_limit: float,
) -> pd.DataFrame:
    indices = seed_pair_df["global_pair_id"].astype(int).tolist()
    edges = build_edges(matrix_df_to_numpy_dict(seed_matrix_dict), indices, offtarget_limit)
    adjacency = {vertex: set() for vertex in indices}
    for u, v in edges:
        if u == v:
            continue
        adjacency[u].add(v)
        adjacency[v].add(u)

    denominator = max(len(indices) - 1, 1)
    rows = []
    for _, row in seed_pair_df.iterrows():
        global_pair_id = int(row["global_pair_id"])
        conflict_count = len(adjacency[global_pair_id])
        rows.append(
            {
                "pair_idx": int(row["pair_idx"]),
                "global_pair_id": global_pair_id,
                "seq": str(row["seq"]),
                "rc_seq": str(row["rc_seq"]),
                "conflict_count": conflict_count,
                "conflict_probability": float(conflict_count / denominator),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["conflict_probability", "global_pair_id"],
        ascending=[False, True],
    )


def reconstruct_seed_independent_df(
    seed_pair_df: pd.DataFrame,
    hybrid_found_df: pd.DataFrame,
    search_progress_df: pd.DataFrame | None,
) -> pd.DataFrame:
    seed_ids = set(seed_pair_df["global_pair_id"].astype(int).tolist())
    independent_df = hybrid_found_df.loc[
        hybrid_found_df["global_pair_id"].astype(int).isin(seed_ids)
    ].copy()

    expected_size = None
    if search_progress_df is not None and "pass" in search_progress_df.columns:
        seed_rows = search_progress_df.loc[search_progress_df["pass"] == "seed"].copy()
        if not seed_rows.empty and "pairs_after_vc" in seed_rows.columns:
            value = pd.to_numeric(seed_rows.iloc[-1]["pairs_after_vc"], errors="coerce")
            if pd.notna(value):
                expected_size = int(value)

    if expected_size is not None and len(independent_df) != expected_size:
        raise ValueError(
            "Reconstructed seed independent set size does not match the seed-stage "
            f"progress row: got {len(independent_df)}, expected {expected_size}."
        )

    return independent_df.reset_index(drop=True)


def build_registry_from_metadata(metadata: dict, outside_seed: int | None):
    length = int(metadata["input.length"])
    fivep_ext = str(metadata.get("input.fivep_ext") or "")
    threep_ext = str(metadata.get("input.threep_ext") or "")
    unwanted_substrings = parse_unwanted_substrings(metadata.get("input.unwanted_substrings"))
    apply_unwanted_to = str(metadata.get("input.apply_unwanted_to") or "core")
    if outside_seed is None:
        raise ValueError("outside_seed must be set explicitly for independent outside-pool sampling.")
    registry_seed = int(outside_seed)

    hf.set_nupack_params(
        material=str(metadata.get("nupack.material") or "dna"),
        celsius=float(metadata.get("nupack.celsius") or 37.0),
        sodium=float(metadata.get("nupack.sodium") or 0.05),
        magnesium=float(metadata.get("nupack.magnesium") or 0.025),
    )
    hf.set_energy_type("total")

    registry = sc.SequencePairRegistry(
        length=length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        unwanted_substrings=unwanted_substrings,
        apply_unwanted_to=apply_unwanted_to,
        seed=registry_seed,
        preselected_cores=None,
    )
    return registry, registry_seed


def pair_conflicts(
    pair_a: tuple[str, str],
    pair_b: tuple[str, str],
    offtarget_limit: float,
) -> bool:
    for seq_a in pair_a:
        for seq_b in pair_b:
            if unpack_energy(sc.compute_nupack_energy(seq_a, seq_b, type=hf.ENERGY_TYPE)) < offtarget_limit:
                return True
    return False


def count_conflicts_against_set(
    candidate_pair: tuple[str, str],
    reference_pairs: list[tuple[str, str]],
    offtarget_limit: float,
) -> int:
    return sum(
        1 for reference_pair in reference_pairs
        if pair_conflicts(candidate_pair, reference_pair, offtarget_limit)
    )


def conflict_flags_against_set(
    candidate_pair: tuple[str, str],
    reference_pairs: list[tuple[str, str]],
    offtarget_limit: float,
) -> list[int]:
    return [
        int(pair_conflicts(candidate_pair, reference_pair, offtarget_limit))
        for reference_pair in reference_pairs
    ]


def sample_outside_crossref_rows(
    *,
    registry,
    outside_pool_size: int,
    max_sample_attempts: int,
    excluded_pairs: set[tuple[str, str]],
    hybrid_pairs: list[tuple[str, str]],
    naive_pairs: list[tuple[str, str]],
    energy_min: float,
    energy_max: float,
    self_energy_limit: float,
    offtarget_limit: float,
) -> tuple[list[dict], dict, list[list[int]], list[list[int]]]:
    rows = []
    attempts = 0
    seen_pairs = set()
    excluded_hits = 0
    duplicate_hits = 0
    failed_energy = 0
    failed_homodimer = 0
    naive_flag_rows = []
    hybrid_flag_rows = []

    while len(rows) < outside_pool_size and attempts < max_sample_attempts:
        attempts += 1
        sampled_pair_id, sampled_pair = registry.sample_pair()
        seq, rc_seq = canonical_pair(*sampled_pair)
        pair = (seq, rc_seq)

        if pair in excluded_pairs:
            excluded_hits += 1
            continue
        if pair in seen_pairs:
            duplicate_hits += 1
            continue

        on_target_result = sc.compute_nupack_energy(seq, rc_seq, type=hf.ENERGY_TYPE)
        on_target_energy = float(on_target_result[0])
        self_energy_seq = float(on_target_result[1])
        self_energy_rc_seq = float(on_target_result[2])
        if not (
            energy_min <= on_target_energy <= energy_max
            and self_energy_seq >= self_energy_limit
            and self_energy_rc_seq >= self_energy_limit
        ):
            failed_energy += 1
            continue

        homo_seq_energy = unpack_energy(sc.compute_nupack_energy(seq, seq, type=hf.ENERGY_TYPE))
        homo_rc_energy = unpack_energy(sc.compute_nupack_energy(rc_seq, rc_seq, type=hf.ENERGY_TYPE))
        if homo_seq_energy < offtarget_limit or homo_rc_energy < offtarget_limit:
            failed_homodimer += 1
            continue

        hybrid_flags = conflict_flags_against_set(pair, hybrid_pairs, offtarget_limit)
        naive_flags = conflict_flags_against_set(pair, naive_pairs, offtarget_limit)
        hybrid_violation_count = int(sum(hybrid_flags))
        naive_violation_count = int(sum(naive_flags))
        seen_pairs.add(pair)
        rows.append(
            {
                "outside_idx": len(rows),
                "sampled_pair_id": int(sampled_pair_id),
                "seq": seq,
                "rc_seq": rc_seq,
                "on_target_energy": on_target_energy,
                "self_energy_seq": self_energy_seq,
                "self_energy_rc_seq": self_energy_rc_seq,
                "homo_seq_energy": float(homo_seq_energy),
                "homo_rc_energy": float(homo_rc_energy),
                "hybrid_violation_count": int(hybrid_violation_count),
                "hybrid_conflict_probability": float(hybrid_violation_count / len(hybrid_pairs)),
                "naive_violation_count": int(naive_violation_count),
                "naive_conflict_probability": float(naive_violation_count / len(naive_pairs)),
            }
        )
        naive_flag_rows.append(naive_flags)
        hybrid_flag_rows.append(hybrid_flags)

        if len(rows) % 25 == 0 or len(rows) == outside_pool_size:
            print(
                "outside_pool_progress "
                f"accepted={len(rows)}/{outside_pool_size} "
                f"registry_draws={attempts} "
                f"excluded={excluded_hits} "
                f"duplicates={duplicate_hits} "
                f"failed_energy={failed_energy} "
                f"failed_homodimer={failed_homodimer}",
                flush=True,
            )

    stats = {
        "attempts": int(attempts),
        "excluded_hits": int(excluded_hits),
        "duplicate_hits": int(duplicate_hits),
        "failed_energy": int(failed_energy),
        "failed_homodimer": int(failed_homodimer),
        "accepted": int(len(rows)),
    }
    return rows, stats, naive_flag_rows, hybrid_flag_rows


def build_comparison_sets_df(
    hybrid_independent_df: pd.DataFrame,
    naive_first_m_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for set_name, source_df in (
        ("hybrid_seed_independent", hybrid_independent_df),
        ("naive_first_m", naive_first_m_df),
    ):
        for order_idx, (_, row) in enumerate(source_df.iterrows()):
            pair = row_to_pair(row)
            rows.append(
                {
                    "set_name": set_name,
                    "set_order": int(order_idx),
                    "global_pair_id": int(row["global_pair_id"]),
                    "seq": pair[0],
                    "rc_seq": pair[1],
                }
            )
    return pd.DataFrame(rows)


def build_matrix_column_labels(selected_df: pd.DataFrame) -> list[str]:
    return [
        f"ord{order_idx:02d}_id{int(row['global_pair_id'])}"
        for order_idx, (_, row) in enumerate(selected_df.iterrows())
    ]


def build_matrix_df(
    outside_df: pd.DataFrame,
    flag_rows: list[list[int]],
    selected_df: pd.DataFrame,
) -> pd.DataFrame:
    matrix_df = pd.DataFrame(flag_rows, columns=build_matrix_column_labels(selected_df))
    matrix_df.insert(0, "rc_seq", outside_df["rc_seq"].tolist())
    matrix_df.insert(0, "seq", outside_df["seq"].tolist())
    matrix_df.insert(0, "outside_idx", outside_df["outside_idx"].tolist())
    return matrix_df


def compute_flag_rows_against_selected(
    outside_df: pd.DataFrame,
    set_name: str,
    selected_pairs: list[tuple[str, str]],
    offtarget_limit: float,
) -> list[list[int]]:
    flag_rows = []
    total = len(outside_df)
    for row_idx, (_, row) in enumerate(outside_df.iterrows(), start=1):
        flag_rows.append(
            conflict_flags_against_set(
                row_to_pair(row),
                selected_pairs,
                offtarget_limit,
            )
        )
        if row_idx % 25 == 0 or row_idx == total:
            print(
                f"compatibility_progress set={set_name} rows={row_idx}/{total}",
                flush=True,
            )
    return flag_rows


def build_inside_against_outside_df(
    naive_first_m_df: pd.DataFrame,
    hybrid_independent_df: pd.DataFrame,
    naive_flag_rows: list[list[int]],
    hybrid_flag_rows: list[list[int]],
) -> pd.DataFrame:
    rows = []
    outside_count = max(len(naive_flag_rows), len(hybrid_flag_rows), 1)

    for selected_idx, (_, row) in enumerate(naive_first_m_df.iterrows()):
        candidate_pair = row_to_pair(row)
        outside_violation_count = int(sum(flags[selected_idx] for flags in naive_flag_rows))
        rows.append(
            {
                "set_name": "naive_first_m",
                "set_order": int(selected_idx),
                "global_pair_id": int(row["global_pair_id"]),
                "seq": candidate_pair[0],
                "rc_seq": candidate_pair[1],
                "outside_violation_count": outside_violation_count,
                "outside_conflict_probability": float(outside_violation_count / outside_count),
            }
        )

    for selected_idx, (_, row) in enumerate(hybrid_independent_df.iterrows()):
        candidate_pair = row_to_pair(row)
        outside_violation_count = int(sum(flags[selected_idx] for flags in hybrid_flag_rows))
        rows.append(
            {
                "set_name": "hybrid_seed_independent",
                "set_order": int(selected_idx),
                "global_pair_id": int(row["global_pair_id"]),
                "seq": candidate_pair[0],
                "rc_seq": candidate_pair[1],
                "outside_violation_count": outside_violation_count,
                "outside_conflict_probability": float(outside_violation_count / outside_count),
            }
        )

    return pd.DataFrame(rows)


def write_analysis_workbook(
    workbook_path: Path,
    summary: dict,
    seed_probability_df: pd.DataFrame,
    comparison_sets_df: pd.DataFrame,
    outside_pool_df: pd.DataFrame,
    outside_to_inside_df: pd.DataFrame,
    inside_against_outside_df: pd.DataFrame,
    naive_matrix_df: pd.DataFrame,
    hybrid_matrix_df: pd.DataFrame,
) -> None:
    summary_df = pd.DataFrame(
        [
            {
                "key": key,
                "value": json.dumps(value) if isinstance(value, (dict, list)) else value,
            }
            for key, value in summary.items()
        ]
    )
    with pd.ExcelWriter(workbook_path) as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        seed_probability_df.to_excel(writer, sheet_name="seed_conflict_probability", index=False)
        comparison_sets_df.to_excel(writer, sheet_name="comparison_sets", index=False)
        outside_pool_df.to_excel(writer, sheet_name="outside_pool", index=False)
        outside_to_inside_df.to_excel(writer, sheet_name="outside_to_inside", index=False)
        inside_against_outside_df.to_excel(writer, sheet_name="inside_to_outside", index=False)
        naive_matrix_df.to_excel(writer, sheet_name="outside_vs_naive", index=False)
        hybrid_matrix_df.to_excel(writer, sheet_name="outside_vs_graph", index=False)


if __name__ == "__main__":
    batch_dir = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "batch_x______sigma1p0_seed41"
    )
    data_dir = batch_dir / "len12" / "5p_none"
    hybrid_report = (
        data_dir
        / "hybrid_len12_5p_none_limitm8p16_budget10000000_init900_seed41.xlsx"
    )
    naive_report = (
        data_dir
        / "naive_len12_5p_none_limitm8p16_budget10000000_seed41.xlsx"
    )
    output_dir = batch_dir / "auxiliary_analysis" / "init900_outside_crossref" / "len12_5p_none"
    outside_pool_size = 1000
    outside_seed = 1041
    max_sample_attempts = 1_000_000

    output_dir.mkdir(parents=True, exist_ok=True)

    print("loading reports...", flush=True)
    hybrid_metadata = load_metadata(hybrid_report)
    seed_pair_df = load_seed_pairs(hybrid_report)
    if seed_pair_df is None:
        raise ValueError("Hybrid report does not contain `seed_pass_pairs`.")
    hybrid_found_df = load_found_pairs(hybrid_report)
    naive_found_df = load_found_pairs(naive_report)
    search_progress_df = load_search_progress(hybrid_report)
    seed_matrix_dict = load_offtarget_matrices(hybrid_report, family="seed")
    print(
        f"loaded seed_pass_pairs={len(seed_pair_df)} "
        f"hybrid_found_pairs={len(hybrid_found_df)} "
        f"naive_found_pairs={len(naive_found_df)}",
        flush=True,
    )

    offtarget_limit = float(hybrid_metadata["search.offtarget_limit"])
    energy_min = float(hybrid_metadata["search.min_ontarget"])
    energy_max = float(hybrid_metadata["search.max_ontarget"])
    self_energy_limit = float(hybrid_metadata["search.self_energy_limit"])

    print("computing initial-seed conflict probabilities...", flush=True)
    seed_probability_df = compute_seed_probability_df(seed_pair_df, seed_matrix_dict, offtarget_limit)
    print("reconstructing comparison sets...", flush=True)
    hybrid_independent_df = reconstruct_seed_independent_df(
        seed_pair_df,
        hybrid_found_df,
        search_progress_df,
    )
    m_value = len(hybrid_independent_df)
    naive_first_m_df = naive_found_df.head(m_value).copy().reset_index(drop=True)
    if len(naive_first_m_df) != m_value:
        raise ValueError(
            f"Naive workbook has only {len(naive_first_m_df)} rows, but hybrid seed independent size is {m_value}."
        )
    print(
        f"comparison_set_sizes hybrid_seed_independent={m_value} "
        f"naive_first_m={len(naive_first_m_df)}",
        flush=True,
    )

    hybrid_pairs = [row_to_pair(row) for _, row in hybrid_independent_df.iterrows()]
    naive_pairs = [row_to_pair(row) for _, row in naive_first_m_df.iterrows()]
    excluded_pairs = set(hybrid_pairs) | set(naive_pairs)

    seed_independent_pair_set = set(hybrid_pairs)
    seed_probability_df["is_hybrid_seed_independent"] = [
        row_to_pair(row) in seed_independent_pair_set
        for _, row in seed_probability_df.iterrows()
    ]

    workbook_path = output_dir / "compatibility_analysis.xlsx"

    print("building live registry...", flush=True)
    registry, registry_seed = build_registry_from_metadata(hybrid_metadata, outside_seed)
    print(
        f"sampling outside pool target={outside_pool_size} "
        f"registry_seed={registry_seed}",
        flush=True,
    )
    outside_rows, outside_stats, naive_flag_rows, hybrid_flag_rows = sample_outside_crossref_rows(
        registry=registry,
        outside_pool_size=outside_pool_size,
        max_sample_attempts=max_sample_attempts,
        excluded_pairs=excluded_pairs,
        hybrid_pairs=hybrid_pairs,
        naive_pairs=naive_pairs,
        energy_min=energy_min,
        energy_max=energy_max,
        self_energy_limit=self_energy_limit,
        offtarget_limit=offtarget_limit,
    )
    if len(outside_rows) != outside_pool_size:
        raise RuntimeError(
            f"Only sampled {len(outside_rows)} outside references out of requested "
            f"{outside_pool_size} within {max_sample_attempts} attempts."
        )
    outside_df = pd.DataFrame(outside_rows)

    print("writing outputs...", flush=True)
    comparison_sets_df = build_comparison_sets_df(hybrid_independent_df, naive_first_m_df)
    naive_matrix_df = build_matrix_df(outside_df, naive_flag_rows, naive_first_m_df)
    hybrid_matrix_df = build_matrix_df(outside_df, hybrid_flag_rows, hybrid_independent_df)
    print("deriving inside-against-outside summary...", flush=True)
    inside_against_outside_df = build_inside_against_outside_df(
        naive_first_m_df,
        hybrid_independent_df,
        naive_flag_rows,
        hybrid_flag_rows,
    )
    outside_to_inside_df = outside_df.loc[
        :,
        [
            "outside_idx",
            "sampled_pair_id",
            "seq",
            "rc_seq",
            "on_target_energy",
            "self_energy_seq",
            "self_energy_rc_seq",
            "homo_seq_energy",
            "homo_rc_energy",
            "hybrid_violation_count",
            "hybrid_conflict_probability",
            "naive_violation_count",
            "naive_conflict_probability",
        ],
    ].copy()

    summary = {
        "hybrid_report": str(hybrid_report),
        "naive_report": str(naive_report),
        "offtarget_limit": offtarget_limit,
        "energy_min": energy_min,
        "energy_max": energy_max,
        "self_energy_limit": self_energy_limit,
        "initial_seed_count": int(len(seed_pair_df)),
        "hybrid_seed_independent_size": int(m_value),
        "naive_first_m_size": int(len(naive_first_m_df)),
        "excluded_union_size": int(len(excluded_pairs)),
        "outside_pool_size": int(len(outside_df)),
        "outside_registry_seed": int(registry_seed),
        "outside_sampling_stats": outside_stats,
    }

    write_analysis_workbook(
        workbook_path,
        summary,
        seed_probability_df,
        comparison_sets_df,
        outside_df,
        outside_to_inside_df,
        inside_against_outside_df,
        naive_matrix_df,
        hybrid_matrix_df,
    )

    print(f"wrote_analysis_workbook={workbook_path}")
    print(f"hybrid_seed_independent_size={m_value}")
    print(f"outside_pool_size={len(outside_df)}")
