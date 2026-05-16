"""
Verified reporting helpers for orthoseq search runs.

Historically this module started around the hybrid-search workflow, but the
shared workbook writer is now used by live hybrid runs, offline benchmark
hybrid runs, standalone vertex-cover benchmarks, and naive benchmarks.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.energy_computations import compute_offtarget_energies, compute_ontarget_energies

NA_VALUE = "N.A."
RUN_METADATA_KEY_ORDER = [
    "algorithm_name",
    "benchmark_name",
    "created_at",
    "found_pair_count",
    "verified_with_direct_nupack",
    "artifact.dataset_dir",
    "artifact.dataset_toml",
    "artifact.dataset_npz",
    "input.source_kind",
    "input.length",
    "input.fivep_ext",
    "input.threep_ext",
    "input.unwanted_substrings",
    "input.apply_unwanted_to",
    "search.offtarget_limit",
    "search.min_ontarget",
    "search.max_ontarget",
    "search.self_energy_limit",
    "search.random_seed",
    "search.total_nupack_calls",
    "search.total_nupack_budget",
    "search.prune_fraction",
    "search.vc_max_iterations",
    "search.initial_fresh_pair_count",
    "search.search_duration_s",
    "stopped_reason",
    "nupack.material",
    "nupack.celsius",
    "nupack.sodium",
    "nupack.magnesium",
    "dataset.range_sigma",
    "dataset.random_seed",
    "dataset.total_candidate_count",
    "dataset.matrix_candidate_count",
    "dataset.mean_ontarget_energy",
    "dataset.std_ontarget_energy",
    "dataset.min_ontarget_energy",
    "dataset.max_ontarget_energy",
    "dataset.virtual_nupack_budget",
]


def _metadata_display_value(value):
    """Convert missing metadata values into a stable workbook sentinel."""
    return NA_VALUE if value is None else value


def verify_selected_pairs(selected_sequence_data: list[dict], nupack_params: dict | None = None) -> dict:
    """
    Recompute on-target, self-structure, and off-target energies for a final
    found-pair set.

    Purpose
    -------
    Reporting should be based on direct post-run NUPACK verification rather
    than cached estimates or search-time heuristics. This helper converts the
    found-pair report entries back into sequence pairs, optionally re-applies
    the recorded NUPACK parameters, and computes the verified energy values
    used in the final workbook.

    :param selected_sequence_data: Report entries for the found-pair set. Each
                                   entry must contain `seq` and `rc_seq`, and
                                   may also contain IDs or cached metadata.
    :type selected_sequence_data: list[dict]

    :param nupack_params: Optional NUPACK parameter bundle with keys
                          `material`, `celsius`, `sodium`, and `magnesium`.
                          When provided, these values are applied before
                          verification so the report reflects the intended
                          thermodynamic model.
    :type nupack_params: dict or None

    :returns: Verified on-target, self-energy, and off-target data ready for
              report writing.
    :rtype: dict
    """
    selected_pairs = [(entry["seq"], entry["rc_seq"]) for entry in selected_sequence_data]
    if not selected_pairs:
        raise ValueError("Selected set is empty; cannot verify with direct NUPACK calls.")

    if nupack_params:
        hf.set_nupack_params(
            material=nupack_params["material"],
            celsius=nupack_params["celsius"],
            sodium=nupack_params["sodium"],
            magnesium=nupack_params["magnesium"],
        )

    on_target, self_seq, self_rc = compute_ontarget_energies(selected_pairs)
    off_target = compute_offtarget_energies(selected_pairs)
    return {
        "on_target_energies": on_target,
        "self_energy_seqs": self_seq,
        "self_energy_rc_seqs": self_rc,
        "off_target": off_target,
    }


def validate_selected_pairs(
    selected_sequence_data: list[dict],
    verified: dict,
    *,
    min_ontarget: float,
    max_ontarget: float,
    self_energy_limit: float,
    offtarget_limit: float,
) -> list[dict]:
    """
    Summarize whether a verified found-pair set satisfies the intended search
    criteria.

    Purpose
    -------
    The workbook should not only contain verified energies, but also a compact
    pass/fail summary of the constraints that matter for benchmarking and final
    review. This helper checks the verified values against the requested
    on-target window, self-energy bound, and pairwise off-target cutoff.

    :param selected_sequence_data: Report entries for the found-pair set. Only
                                   the number of selected pairs matters here;
                                   the actual energy checks are based on the
                                   `verified` payload.
    :type selected_sequence_data: list[dict]

    :param verified: Verified energy data returned by `verify_selected_pairs`.
    :type verified: dict

    :param min_ontarget: Lower bound for acceptable on-target energy.
    :type min_ontarget: float

    :param max_ontarget: Upper bound for acceptable on-target energy.
    :type max_ontarget: float

    :param self_energy_limit: Minimum acceptable self-energy for both strands
                              of each selected pair.
    :type self_energy_limit: float

    :param offtarget_limit: Conflict threshold below which any verified
                            off-target interaction counts as a violation.
    :type offtarget_limit: float

    :returns: Validation entries suitable for the workbook's `validation`
              sheet.
    :rtype: list[dict]
    """
    on_target = verified["on_target_energies"]
    self_seq = verified["self_energy_seqs"]
    self_rc = verified["self_energy_rc_seqs"]
    off_target = verified["off_target"]

    pair_count = len(selected_sequence_data)
    off_target_violations = 0
    hh = off_target["handle_handle_energies"]
    hah = off_target["antihandle_handle_energies"]
    ahah = off_target["antihandle_antihandle_energies"]
    for i in range(pair_count):
        for j in range(i + 1):
            if (
                hh[i, j] < offtarget_limit
                or ahah[i, j] < offtarget_limit
                or (i != j and (hah[i, j] < offtarget_limit or hah[j, i] < offtarget_limit))
            ):
                off_target_violations += 1

    on_target_ok = [min_ontarget <= float(value) <= max_ontarget for value in on_target]
    self_energy_ok = [
        float(seq_value) >= self_energy_limit and float(rc_value) >= self_energy_limit
        for seq_value, rc_value in zip(self_seq, self_rc)
    ]

    return [
        {"check": "selected_set_nonempty", "passed": bool(selected_sequence_data), "value": len(selected_sequence_data)},
        {"check": "all_on_target_in_range", "passed": all(on_target_ok), "value": sum(on_target_ok)},
        {"check": "all_self_energies_above_limit", "passed": all(self_energy_ok), "value": sum(self_energy_ok)},
        {"check": "off_target_violations", "passed": off_target_violations == 0, "value": off_target_violations},
    ]


def build_selected_sequence_data(
    final_pairs: list[tuple[str, str]],
    pair_ids: list[int],
) -> list[dict]:
    """
    Build the canonical per-pair report entries for the `found_pairs` sheet.

    Purpose
    -------
    Search functions naturally return `(seq, rc_seq)` tuples and stable pair
    IDs, while the report writer expects a sheet-oriented structure. This
    helper turns the algorithm result into the standard found-pair row format
    used throughout reporting.

    :param final_pairs: Final selected sequence pairs in report order.
    :type final_pairs: list[tuple[str, str]]

    :param pair_ids: Stable global IDs aligned with `final_pairs`.
    :type pair_ids: list[int]

    :returns: Selected-sequence report entries containing local sheet order,
              global IDs, and the two sequences for each pair.
    :rtype: list[dict]
    """
    if len(final_pairs) != len(pair_ids):
        raise ValueError("final_pairs and pair_ids must have the same length.")
    selected_sequence_data = []
    for idx, (seq, rc_seq) in enumerate(final_pairs):
        entry = {
            "pair_idx": idx,
            "global_pair_id": int(pair_ids[idx]),
            "seq": seq,
            "rc_seq": rc_seq,
        }
        selected_sequence_data.append(entry)
    return selected_sequence_data


def write_hybrid_search_result_xlsx(
    output_path: str | Path,
    *,
    algorithm_name: str,
    selected_sequence_data: list[dict],
    verified: dict,
    search_params: dict,
    input_params: dict,
    artifact_info: dict,
    nupack_params: dict,
    generation_data: list[dict],
    validation_data: list[dict],
    dataset_info: dict | None = None,
    seed_sequence_data: list[dict] | None = None,
    seed_verified: dict | None = None,
    extra_sheets: dict[str, list[dict]] | None = None,
    extra_metadata: dict | None = None,
) -> Path:
    """
    Write the canonical verified XLSX report for live or benchmark search runs.

    Purpose
    -------
    This is the single shared workbook writer for orthoseq search outputs. It
    assumes callers have already prepared found-pair report entries, post-run
    verified energies, validation summaries, and progress data. The function's
    job is to serialize that standardized reporting contract into a consistent
    Excel artifact.

    The function name is legacy: despite the `hybrid` wording, this is the
    shared workbook writer used across the benchmark and live-search code
    paths.

    The `generation_data` input is written to the workbook's
    `search_progress` sheet. Callers are responsible for providing the shared
    progress rows directly; this writer does not normalize or repair them.

    :param output_path: Destination workbook path.
    :type output_path: str or pathlib.Path

    :param algorithm_name: Name recorded in the workbook metadata.
    :type algorithm_name: str

    :param selected_sequence_data: Canonical entries for the `found_pairs`
                                   sheet.
    :type selected_sequence_data: list[dict]

    :param verified: Verified energy payload from `verify_selected_pairs`.
    :type verified: dict

    :param search_params: Search parameters to record under `search.*`.
    :type search_params: dict

    :param input_params: Canonical input parameters recorded under
                         `input.*`.
    :type input_params: dict

    :param artifact_info: Shared artifact/file provenance recorded under
                          `artifact.*`.
    :type artifact_info: dict

    :param nupack_params: NUPACK settings recorded under `nupack.*`.
    :type nupack_params: dict

    :param generation_data: Standardized progress entries for the
                            `search_progress` sheet.
    :type generation_data: list[dict]

    :param validation_data: Standardized validation entries for the
                            `validation` sheet.
    :type validation_data: list[dict]

    :param dataset_info: Optional dataset-specific properties recorded under
                         `dataset.*`. Callers that do not have a backing
                         dataset may leave these fields empty.
    :type dataset_info: dict or None

    :param extra_sheets: Optional algorithm-specific sheets to append in
                         addition to the shared report contract.
    :type extra_sheets: dict[str, list[dict]] or None

    :param extra_metadata: Optional additional metadata keys to merge into the
                           workbook's `run_metadata` sheet.
    :type extra_metadata: dict or None

    :returns: Path to the written workbook.
    :rtype: pathlib.Path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    found_pair_count = len(selected_sequence_data)
    if found_pair_count != len(verified["on_target_energies"]):
        raise ValueError("selected_sequence_data length must match verified energy array length.")

    metadata_values = {
        "algorithm_name": algorithm_name,
        "benchmark_name": None,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "found_pair_count": found_pair_count,
        "verified_with_direct_nupack": True,
        "artifact.dataset_dir": artifact_info.get("dataset_dir"),
        "artifact.dataset_toml": artifact_info.get("dataset_toml"),
        "artifact.dataset_npz": artifact_info.get("dataset_npz"),
        "input.source_kind": input_params.get("source_kind"),
        "input.length": input_params.get("length"),
        "input.fivep_ext": input_params.get("fivep_ext"),
        "input.threep_ext": input_params.get("threep_ext"),
        "input.unwanted_substrings": input_params.get("unwanted_substrings"),
        "input.apply_unwanted_to": input_params.get("apply_unwanted_to"),
        "search.offtarget_limit": search_params.get("offtarget_limit"),
        "search.max_ontarget": search_params.get("max_ontarget"),
        "search.min_ontarget": search_params.get("min_ontarget"),
        "search.self_energy_limit": search_params.get("self_energy_limit"),
        "search.initial_fresh_pair_count": search_params.get("initial_fresh_pair_count"),
        "search.prune_fraction": search_params.get("prune_fraction"),
        "search.vc_max_iterations": search_params.get("vc_max_iterations"),
        "search.random_seed": search_params.get("random_seed"),
        "search.total_nupack_budget": search_params.get("total_nupack_budget"),
        "search.total_nupack_calls": search_params.get("total_nupack_calls"),
        "search.search_duration_s": search_params.get("search_duration_s"),
        "nupack.material": nupack_params.get("material"),
        "nupack.celsius": nupack_params.get("celsius"),
        "nupack.sodium": nupack_params.get("sodium"),
        "nupack.magnesium": nupack_params.get("magnesium"),
        "dataset.range_sigma": (dataset_info or {}).get("range_sigma"),
        "dataset.random_seed": (dataset_info or {}).get("random_seed"),
        "dataset.total_candidate_count": (dataset_info or {}).get("total_candidate_count"),
        "dataset.matrix_candidate_count": (dataset_info or {}).get("matrix_candidate_count"),
        "dataset.mean_ontarget_energy": (dataset_info or {}).get("mean_ontarget_energy"),
        "dataset.std_ontarget_energy": (dataset_info or {}).get("std_ontarget_energy"),
        "dataset.min_ontarget_energy": (dataset_info or {}).get("min_ontarget_energy"),
        "dataset.max_ontarget_energy": (dataset_info or {}).get("max_ontarget_energy"),
        "dataset.virtual_nupack_budget": None,
    }
    if extra_metadata:
        metadata_values.update(extra_metadata)
    metadata_rows = [
        {"key": key, "value": _metadata_display_value(metadata_values.get(key))}
        for key in RUN_METADATA_KEY_ORDER
    ]
    extra_keys = [key for key in metadata_values if key not in RUN_METADATA_KEY_ORDER]
    metadata_rows.extend(
        {"key": key, "value": _metadata_display_value(metadata_values[key])}
        for key in sorted(extra_keys)
    )

    found_pairs_sheet = [dict(entry) for entry in selected_sequence_data]
    for idx, entry in enumerate(found_pairs_sheet):
        entry["on_target_energy_verified"] = verified["on_target_energies"][idx]
        entry["self_energy_seq_verified"] = verified["self_energy_seqs"][idx]
        entry["self_energy_rc_seq_verified"] = verified["self_energy_rc_seqs"][idx]

    handle_labels = []
    antihandle_labels = []
    for idx, entry in enumerate(found_pairs_sheet):
        pair_label = entry.get("global_pair_id", entry.get("pair_idx", idx))
        handle_labels.append(f"{pair_label}:H:{entry['seq']}")
        antihandle_labels.append(f"{pair_label}:A:{entry['rc_seq']}")

    with pd.ExcelWriter(output_path) as writer:
        pd.DataFrame(metadata_rows).to_excel(writer, sheet_name="run_metadata", index=False)
        pd.DataFrame(found_pairs_sheet).to_excel(writer, sheet_name="found_pairs", index=False)
        pd.DataFrame(
            verified["off_target"]["handle_handle_energies"], index=handle_labels, columns=handle_labels
        ).to_excel(writer, sheet_name="selected_hh")
        pd.DataFrame(
            verified["off_target"]["antihandle_handle_energies"], index=handle_labels, columns=antihandle_labels
        ).to_excel(writer, sheet_name="selected_hah")
        pd.DataFrame(
            verified["off_target"]["antihandle_antihandle_energies"], index=antihandle_labels, columns=antihandle_labels
        ).to_excel(writer, sheet_name="selected_ahah")
        pd.DataFrame(generation_data).to_excel(writer, sheet_name="search_progress", index=False)
        pd.DataFrame(validation_data).to_excel(writer, sheet_name="validation", index=False)

        if seed_sequence_data is not None and seed_verified is not None:
            seed_sheet = [dict(entry) for entry in seed_sequence_data]
            for idx, entry in enumerate(seed_sheet):
                entry["on_target_energy_verified"] = seed_verified["on_target_energies"][idx]
                entry["self_energy_seq_verified"] = seed_verified["self_energy_seqs"][idx]
                entry["self_energy_rc_seq_verified"] = seed_verified["self_energy_rc_seqs"][idx]
            seed_h_labels = []
            seed_a_labels = []
            for idx, entry in enumerate(seed_sheet):
                pair_label = entry.get("global_pair_id", entry.get("pair_idx", idx))
                seed_h_labels.append(f"{pair_label}:H:{entry['seq']}")
                seed_a_labels.append(f"{pair_label}:A:{entry['rc_seq']}")
            pd.DataFrame(seed_sheet).to_excel(writer, sheet_name="seed_pass_pairs", index=False)
            pd.DataFrame(
                seed_verified["off_target"]["handle_handle_energies"],
                index=seed_h_labels, columns=seed_h_labels
            ).to_excel(writer, sheet_name="seed_hh")
            pd.DataFrame(
                seed_verified["off_target"]["antihandle_handle_energies"],
                index=seed_h_labels, columns=seed_a_labels
            ).to_excel(writer, sheet_name="seed_hah")
            pd.DataFrame(
                seed_verified["off_target"]["antihandle_antihandle_energies"],
                index=seed_a_labels, columns=seed_a_labels
            ).to_excel(writer, sheet_name="seed_ahah")

        if extra_sheets:
            for sheet_name, rows in extra_sheets.items():
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)
    return output_path
