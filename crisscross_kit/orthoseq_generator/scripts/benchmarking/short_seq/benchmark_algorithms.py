"""
Benchmark algorithm implementations for short-sequence datasets.
"""

from __future__ import annotations

from pathlib import Path
import random

import numpy as np

from benchmark_dataset_tools import (
    build_all_global_to_all_idx,
    build_global_to_matrix_idx,
    build_sub_offtarget_dict,
    estimate_dataset_nupack_budget,
    get_pair_by_global_id,
    get_selected_rows,
    load_dataset,
    resolve_dataset_input_params,
)
from benchmark_analysis import build_conflict_data
from orthoseq_generator.search_reporting import (
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)
from orthoseq_generator.search_algorithm import _build_progress_row, _num_vertices_to_remove
from orthoseq_generator.vertex_cover_algorithms import build_edges, iterative_vertex_cover_refinement


def _estimate_offtarget_nupack_calls(num_sequence_pairs: int) -> int:
    """Estimate the virtual cost of a full off-target matrix for a subset."""
    return 2 * int(num_sequence_pairs) * int(num_sequence_pairs)


def _status(message: str) -> None:
    """Emit a benchmark progress message immediately."""
    print(message, flush=True)


def _write_benchmark_result_xlsx(
    output_path: str | Path,
    *,
    algorithm_name: str,
    dataset: dict,
    selected_sequence_data: list[dict],
    verified: dict,
    search_params: dict,
    seed_sequence_data: list[dict] | None = None,
    seed_verified: dict | None = None,
    extra_metadata: dict | None = None,
    extra_sheets: dict[str, list[dict]] | None = None,
) -> Path:
    """
    Adapt benchmark-specific provenance and validation inputs to the shared
    report writer.

    Purpose
    -------
    Benchmark runs start from precomputed dataset artifacts rather than the
    live on-the-fly registry. This helper translates dataset-local metadata
    and found-pair report entries into the common XLSX reporting contract used
    by both benchmark and live workflows.

    :param output_path: Destination workbook path.
    :type output_path: str or pathlib.Path

    :param algorithm_name: Benchmark algorithm name recorded in the workbook.
    :type algorithm_name: str

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param selected_sequence_data: Canonical found-pair report rows.
    :type selected_sequence_data: list[dict]

    :param verified: Verified energy payload from `verify_selected_pairs`.
    :type verified: dict

    :param search_params: Benchmark search parameters to record under
                          `search.*`.
    :type search_params: dict

    :param extra_metadata: Optional extra metadata entries to append to the
                           shared workbook metadata.
    :type extra_metadata: dict or None

    :param extra_sheets: Optional extra benchmark-specific sheets.
    :type extra_sheets: dict[str, list[dict]] or None

    :returns: Path to the written workbook.
    :rtype: pathlib.Path
    """
    derived = dataset["metadata"]["derived"]
    validation_data = validate_selected_pairs(
        selected_sequence_data,
        verified,
        min_ontarget=float(derived["min_ontarget_energy"]),
        max_ontarget=float(derived["max_ontarget_energy"]),
        self_energy_limit=float(search_params["self_energy_limit"]) if "self_energy_limit" in search_params else float("-inf"),
        offtarget_limit=float(search_params["offtarget_limit"]),
    )
    dataset_inputs = dataset["metadata"].get("inputs", {})
    input_params = resolve_dataset_input_params(dataset_inputs)
    dataset_info = {
        "range_sigma": dataset_inputs.get("range_sigma"),
        "random_seed": dataset_inputs.get("random_seed"),
    }
    dataset_info.update(dataset["metadata"].get("derived", {}))
    dataset_nupack_budget = estimate_dataset_nupack_budget(dataset)
    output_path = Path(output_path)
    benchmark_name = output_path.parent.name if output_path.parent.name != "results" else None
    merged_extra_metadata = {
        "dataset.virtual_nupack_budget": dataset_nupack_budget,
        "benchmark_name": benchmark_name,
    }
    if extra_metadata:
        merged_extra_metadata.update(extra_metadata)

    return write_hybrid_search_result_xlsx(
        output_path,
        algorithm_name=algorithm_name,
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params=search_params,
        input_params={
            "source_kind": "benchmark_dataset",
            **input_params,
        },
        artifact_info={
            "dataset_dir": dataset["dataset_dir"],
            "dataset_toml": dataset["dataset_toml"],
            "dataset_npz": dataset["dataset_npz"],
        },
        nupack_params=dataset["metadata"].get("nupack", {}),
        generation_data=extra_sheets.get("search_progress", []) if extra_sheets else [],
        validation_data=validation_data,
        dataset_info=dataset_info,
        seed_sequence_data=seed_sequence_data,
        seed_verified=seed_verified,
        extra_sheets={k: v for k, v in (extra_sheets or {}).items() if k != "search_progress"},
        extra_metadata=merged_extra_metadata,
    )


def run_naive_search_to_xlsx(
    dataset_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    offtarget_limit: float,
    self_energy_limit: float,
    random_seed: int = 41,
) -> Path:
    """
    Run the benchmark naive search on a precomputed dataset and write a
    verified XLSX report.

    Purpose
    -------
    This function evaluates the simple greedy baseline that iterates over a
    shuffled candidate order, applies the cached self-energy filter, and
    rejects any pair that conflicts with the already accepted set.

    :param dataset_dir: Directory containing the saved benchmark dataset.
    :type dataset_dir: str or pathlib.Path

    :param output_path: Optional destination workbook path. When omitted, the
                        default benchmark filename is written under the
                        dataset's `results/` directory.
    :type output_path: str or pathlib.Path or None

    :param offtarget_limit: Conflict threshold applied to the cached
                            incompatibility data.
    :type offtarget_limit: float

    :param self_energy_limit: Minimum acceptable cached self-energy for both
                              strands in a candidate pair.
    :type self_energy_limit: float

    :param random_seed: Seed used to shuffle the candidate visitation order.
    :type random_seed: int

    :returns: Path to the written verified workbook.
    :rtype: pathlib.Path
    """
    dataset = load_dataset(dataset_dir)
    dataset_path = Path(dataset_dir)
    derived = dataset["metadata"]["derived"]
    if output_path is None:
        cutoff_label = str(offtarget_limit).replace(".", "p")
        output_path = dataset_path / "results" / f"naive_limit{cutoff_label}_seed{random_seed}.xlsx"
    all_idx_by_global = build_all_global_to_all_idx(dataset["all_global_pair_ids"])
    pair_conflict, self_violation = build_conflict_data(dataset, float(offtarget_limit))
    n = int(len(dataset["matrix_global_pair_ids"]))
    order = list(range(n))
    random.Random(random_seed).shuffle(order)
    selected_local_indices = []
    selected_mask = np.zeros(n, dtype=bool)
    for idx in order:
        global_id = int(dataset["matrix_global_pair_ids"][idx])
        all_idx = all_idx_by_global[global_id]
        self_e_seq = float(dataset["all_self_energy_seqs"][all_idx])
        self_e_rc = float(dataset["all_self_energy_rc_seqs"][all_idx])
        if self_e_seq < float(self_energy_limit) or self_e_rc < float(self_energy_limit):
            continue
        if self_violation[idx]:
            continue
        if np.any(pair_conflict[idx, selected_mask]):
            continue
        selected_local_indices.append(idx)
        selected_mask[idx] = True
    selected_sequence_data = get_selected_rows(
        dataset, [int(dataset["matrix_global_pair_ids"][idx]) for idx in selected_local_indices]
    )
    verified = verify_selected_pairs(selected_sequence_data, nupack_params=dataset["metadata"]["nupack"])
    progress_rows = [
        {
            "step": "final_summary",
            "pairs_in_graph_search": int(n),
            "pairs_found": len(selected_sequence_data),
            "nupack_calls_executed": None,
            "notes": "single_pass_greedy_selection",
        }
    ]
    return _write_benchmark_result_xlsx(
        output_path,
        algorithm_name="naive",
        dataset=dataset,
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            "offtarget_limit": float(offtarget_limit),
            "max_ontarget": float(derived["max_ontarget_energy"]),
            "min_ontarget": float(derived["min_ontarget_energy"]),
            "self_energy_limit": float(self_energy_limit),
            "random_seed": int(random_seed),
            "prune_fraction": None,
            "vc_max_iterations": None,
        },
        extra_sheets={"search_progress": progress_rows},
    )


def run_vertex_cover_search_to_xlsx(
    dataset_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    offtarget_limit: float,
    self_energy_limit: float,
    random_seed: int = 41,
    prune_fraction: float = 0.2,
    vc_max_iterations: int = 200,
    show_progress: bool = False,
) -> Path:
    """
    Run the standalone vertex-cover benchmark on a precomputed dataset and
    write a verified XLSX report.

    Purpose
    -------
    This function treats the self-energy-feasible benchmark incompatibility
    graph as input to the iterative vertex-cover refinement heuristic and
    reports the resulting independent set together with trajectory/progress
    data.

    :param dataset_dir: Directory containing the saved benchmark dataset.
    :type dataset_dir: str or pathlib.Path

    :param output_path: Optional destination workbook path. When omitted, the
                        default benchmark filename is written under the
                        dataset's `results/` directory.
    :type output_path: str or pathlib.Path or None

    :param offtarget_limit: Conflict threshold applied to the cached
                            incompatibility graph.
    :type offtarget_limit: float

    :param self_energy_limit: Minimum acceptable cached self-energy for both
                              strands in a candidate pair.
    :type self_energy_limit: float

    :param random_seed: Seed used by the refinement heuristic.
    :type random_seed: int

    :param prune_fraction: Fraction of the current cover removed before each
                           repair iteration.
    :type prune_fraction: float

    :param vc_max_iterations: Maximum number of refinement iterations for the
                              vertex-cover refinement routine.
    :type vc_max_iterations: int

    :param show_progress: Whether to print refinement progress from the
                          underlying vertex-cover routine.
    :type show_progress: bool

    :returns: Path to the written verified workbook.
    :rtype: pathlib.Path
    """
    dataset = load_dataset(dataset_dir)
    dataset_path = Path(dataset_dir)
    derived = dataset["metadata"]["derived"]
    if output_path is None:
        cutoff_label = str(offtarget_limit).replace(".", "p")
        output_path = dataset_path / "results" / f"vertex_cover_limit{cutoff_label}_seed{random_seed}.xlsx"
    if not 0 <= prune_fraction <= 1:
        raise ValueError("prune_fraction must be between 0 and 1.")
    random.seed(random_seed)
    all_idx_by_global = build_all_global_to_all_idx(dataset["all_global_pair_ids"])
    matrix_global_pair_ids = []
    matrix_local_indices = []
    for local_idx, global_id_raw in enumerate(dataset["matrix_global_pair_ids"]):
        global_id = int(global_id_raw)
        all_idx = all_idx_by_global[global_id]
        self_e_seq = float(dataset["all_self_energy_seqs"][all_idx])
        self_e_rc = float(dataset["all_self_energy_rc_seqs"][all_idx])
        if self_e_seq >= float(self_energy_limit) and self_e_rc >= float(self_energy_limit):
            matrix_global_pair_ids.append(global_id)
            matrix_local_indices.append(local_idx)
    offtarget_dict = {
        "handle_handle_energies": dataset["handle_handle_energies"][np.ix_(matrix_local_indices, matrix_local_indices)],
        "antihandle_handle_energies": dataset["handle_antihandle_energies"][np.ix_(matrix_local_indices, matrix_local_indices)],
        "antihandle_antihandle_energies": dataset["antihandle_antihandle_energies"][np.ix_(matrix_local_indices, matrix_local_indices)],
    }
    edges = build_edges(offtarget_dict, matrix_global_pair_ids, float(offtarget_limit))
    vertices = set(matrix_global_pair_ids)
    n_remove = _num_vertices_to_remove(len(vertices), prune_fraction)
    vertex_cover, trajectories = iterative_vertex_cover_refinement(
        vertices,
        edges,
        avoid_V=None,
        num_vertices_to_remove=n_remove,
        max_iterations=vc_max_iterations,
        limit=+np.inf,
        show_progress=show_progress,
    )
    selected_sequence_data = get_selected_rows(dataset, sorted(vertices - vertex_cover))
    verified = verify_selected_pairs(selected_sequence_data, nupack_params=dataset["metadata"]["nupack"])
    progress_rows = [
        {
            "iteration": i_idx,
            "pairs_in_graph_search": len(vertices),
            "pairs_found": int(size),
            "nupack_calls_executed": None,
            "notes": f"trajectory_{t_idx}",
        }
        for t_idx, trajectory in enumerate(trajectories)
        for i_idx, size in enumerate(trajectory, start=1)
    ]
    vc_rows = [
        {"trajectory_idx": t_idx, "iteration_idx": i_idx, "independent_set_size": int(size)}
        for t_idx, trajectory in enumerate(trajectories)
        for i_idx, size in enumerate(trajectory, start=1)
    ]
    return _write_benchmark_result_xlsx(
        output_path,
        algorithm_name="vertex_cover",
        dataset=dataset,
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            "offtarget_limit": float(offtarget_limit),
            "max_ontarget": float(derived["max_ontarget_energy"]),
            "min_ontarget": float(derived["min_ontarget_energy"]),
            "self_energy_limit": float(self_energy_limit),
            "random_seed": int(random_seed),
            "prune_fraction": float(prune_fraction),
            "vc_max_iterations": int(vc_max_iterations),
            "num_vertices_to_remove_effective": int(n_remove),
        },
        extra_sheets={"search_progress": progress_rows, "vc_trajectory": vc_rows},
    )


def _crossreference_sequences_offline(
    candidate_global_id: int,
    retained_pair_ids,
    dataset: dict,
    offtarget_limit: float,
    max_pair_violations: int = 0,
    matrix_idx_by_global: dict[int, int] | None = None,
):
    """
    Check whether one candidate is compatible with the retained offline
    history set.

    Purpose
    -------
    The offline hybrid benchmark mirrors the live search step that screens new
    candidates against the currently retained best set before building the full
    graph. This helper performs that compatibility check using only the cached
    matrices and also reports the equivalent virtual NUPACK-call count for
    budgeting.
    """
    if not retained_pair_ids:
        return True, 0
    if matrix_idx_by_global is None:
        matrix_idx_by_global = build_global_to_matrix_idx(dataset["matrix_global_pair_ids"])
    candidate_idx = matrix_idx_by_global[int(candidate_global_id)]
    hh = dataset["handle_handle_energies"]
    hah = dataset["handle_antihandle_energies"]
    ahah = dataset["antihandle_antihandle_energies"]
    violations = 0
    virtual_nupack_calls = 0
    for retained_global_id in retained_pair_ids:
        retained_idx = matrix_idx_by_global[int(retained_global_id)]
        triangular_idx = (max(candidate_idx, retained_idx), min(candidate_idx, retained_idx))
        violated = False
        for test in (
            hh[triangular_idx],
            hah[candidate_idx, retained_idx],
            hah[retained_idx, candidate_idx],
            ahah[triangular_idx],
        ):
            virtual_nupack_calls += 1
            if test < offtarget_limit:
                violated = True
                break
        if violated:
            violations += 1
            if violations > max_pair_violations:
                return False, virtual_nupack_calls
    return True, virtual_nupack_calls


def _passes_homodimer_filter_offline(
    candidate_global_id: int,
    dataset: dict,
    offtarget_limit: float,
    matrix_idx_by_global: dict[int, int] | None = None,
) -> tuple[bool, int]:
    """
    Mirror the live same-strand homodimer screen using cached dataset matrices.

    The live selector spends two NUPACK calls here: `seq/seq` and `rc/rc`.
    The offline benchmark treats the corresponding cached diagonal lookups as
    two virtual calls so accounting stays comparable.
    """
    if matrix_idx_by_global is None:
        matrix_idx_by_global = build_global_to_matrix_idx(dataset["matrix_global_pair_ids"])
    candidate_idx = matrix_idx_by_global.get(int(candidate_global_id))
    if candidate_idx is None:
        return False, 0
    homo_seq = float(dataset["handle_handle_energies"][candidate_idx, candidate_idx])
    homo_rc = float(dataset["antihandle_antihandle_energies"][candidate_idx, candidate_idx])
    return homo_seq >= float(offtarget_limit) and homo_rc >= float(offtarget_limit), 2


def _build_verified_from_dataset(dataset: dict, selected_global_ids) -> dict:
    """Assemble a report-style verified payload from cached dataset arrays."""
    global_ids = [int(global_id) for global_id in selected_global_ids]
    all_idx_by_global = build_all_global_to_all_idx(dataset["all_global_pair_ids"])
    return {
        "on_target_energies": np.array(
            [float(dataset["all_on_target_energies"][all_idx_by_global[global_id]]) for global_id in global_ids],
            dtype=float,
        ),
        "self_energy_seqs": np.array(
            [float(dataset["all_self_energy_seqs"][all_idx_by_global[global_id]]) for global_id in global_ids],
            dtype=float,
        ),
        "self_energy_rc_seqs": np.array(
            [float(dataset["all_self_energy_rc_seqs"][all_idx_by_global[global_id]]) for global_id in global_ids],
            dtype=float,
        ),
        "off_target": build_sub_offtarget_dict(dataset, global_ids),
    }


def _run_vertex_cover_offline(
    selected_global_ids,
    dataset: dict,
    offtarget_limit: float,
    prune_fraction: float,
    vc_max_iterations: int,
):
    """Run the cached off-target graph step used by offline hybrid pass 1/2."""
    indices = [int(global_id) for global_id in selected_global_ids]
    off_target_nupack_calls = _estimate_offtarget_nupack_calls(len(indices))
    off_e_subset = build_sub_offtarget_dict(dataset, indices)
    edges = build_edges(off_e_subset, indices, offtarget_limit)
    removed_vertices, _ = iterative_vertex_cover_refinement(
        indices,
        edges,
        avoid_V=None,
        max_iterations=vc_max_iterations,
        num_vertices_to_remove=_num_vertices_to_remove(len(indices), prune_fraction),
        show_progress=False,
    )
    return set(indices) - removed_vertices, off_target_nupack_calls


def _select_subset_in_energy_range_offline(
    dataset: dict,
    *,
    energy_min: float,
    energy_max: float,
    self_energy_min: float,
    max_size: int,
    avoid_indices=None,
    retained_pair_ids=None,
    offtarget_limit: float | None = None,
):
    """
    Sample a fresh offline working subset from the saved dataset.

    Purpose
    -------
    This helper is the dataset-backed analogue of the live subset-selection
    step inside the hybrid search. It repeatedly samples unseen global IDs from
    the full saved pool, filters them by cached on-target and self-energy
    values, mirrors the live same-strand homodimer filter using cached
    diagonal matrix values, optionally cross-references them against the
    retained history set, and stops when the target subset size is reached or
    the finite candidate list is exhausted.
    """
    if avoid_indices is None:
        avoid_indices = set()
    if retained_pair_ids is None:
        retained_pair_ids = []
    eligible_global_ids = [int(global_id) for global_id in dataset["all_global_pair_ids"]]
    random.shuffle(eligible_global_ids)
    all_idx_by_global = build_all_global_to_all_idx(dataset["all_global_pair_ids"])
    matrix_idx_by_global = build_global_to_matrix_idx(dataset["matrix_global_pair_ids"])
    subset = []
    indices = []
    nupack_calls = 0
    attempts = 0
    passed_ontarget_and_self = 0
    passed_homodimer = 0

    for global_id in eligible_global_ids:
        if len(indices) >= max_size:
            break
        if int(global_id) in avoid_indices:
            continue
        attempts += 1
        all_idx = all_idx_by_global[int(global_id)]
        nupack_calls += 1
        on_energy = float(dataset["all_on_target_energies"][all_idx])
        self_e_seq = float(dataset["all_self_energy_seqs"][all_idx])
        self_e_rc = float(dataset["all_self_energy_rc_seqs"][all_idx])
        if not (energy_min <= on_energy <= energy_max and self_e_seq >= self_energy_min and self_e_rc >= self_energy_min):
            continue
        passed_ontarget_and_self += 1
        if offtarget_limit is not None:
            passed_homo, homodimer_calls = _passes_homodimer_filter_offline(
                int(global_id), dataset, float(offtarget_limit), matrix_idx_by_global=matrix_idx_by_global
            )
            nupack_calls += homodimer_calls
            if not passed_homo:
                continue
            passed_homodimer += 1
            passed_crossref, crossref_calls = _crossreference_sequences_offline(
                int(global_id),
                retained_pair_ids,
                dataset,
                float(offtarget_limit),
                max_pair_violations=0,
                matrix_idx_by_global=matrix_idx_by_global,
            )
            nupack_calls += crossref_calls
            if not passed_crossref:
                continue
        subset.append(get_pair_by_global_id(dataset, global_id))
        indices.append(global_id)
    stop_reason = None if len(indices) >= max_size else "pool_exhausted"
    return subset, indices, stop_reason, nupack_calls, {
        "attempts": int(attempts),
        "passed_ontarget_and_self": int(passed_ontarget_and_self),
        "passed_homodimer": int(passed_homodimer),
        "accepted_into_pool": len(indices),
    }


def run_hybrid_search_offline_to_xlsx(
    dataset_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    offtarget_limit: float,
    self_energy_limit: float,
    initial_fresh_pair_count: int = 200,
    prune_fraction: float = 0.2,
    vc_max_iterations: int = 5000,
    random_seed: int = 42,
) -> Path:
    """
    Run the offline hybrid benchmark on a precomputed dataset and write a
    verified XLSX report.

    Purpose
    -------
    This is the dataset-backed mirror of the current live hybrid workflow. It
    follows the same two-pass structure:
    1. collect one seed subset with on-target, self-energy, and homodimer
       filtering, then run vertex cover on that subset;
    2. if pass 1 filled its requested seed size without exhausting the finite
       candidate list, collect additional candidates cross-referenced against
       the retained seed set, then run vertex cover on those fresh candidates
       only and union the survivors into the final retained set.

    Unlike the live registry-backed search, the offline benchmark has an exact
    finite candidate list, so termination uses true pool exhaustion rather than
    the duplicate-streak heuristic.

    :param dataset_dir: Directory containing the saved benchmark dataset.
    :type dataset_dir: str or pathlib.Path

    :param output_path: Optional destination workbook path. When omitted, the
                        default benchmark filename is written under the
                        dataset's `results/` directory.
    :type output_path: str or pathlib.Path or None

    :param offtarget_limit: Conflict threshold applied during subset screening
                            and graph construction.
    :type offtarget_limit: float

    :param self_energy_limit: Minimum acceptable cached self-energy for both
                              strands in a candidate pair.
    :type self_energy_limit: float

    :param initial_fresh_pair_count: Number of pass-1 seed candidates to
                                     collect before the first vertex-cover run.
    :type initial_fresh_pair_count: int

    :param prune_fraction: Fraction of the current cover removed before each
                           repair iteration.
    :type prune_fraction: float

    :param vc_max_iterations: Maximum number of refinement iterations inside
                              the vertex-cover step.
    :type vc_max_iterations: int

    :param random_seed: Seed controlling offline candidate sampling and graph
                        refinement.
    :type random_seed: int

    :returns: Path to the written verified workbook.
    :rtype: pathlib.Path
    """
    dataset = load_dataset(dataset_dir)
    dataset_path = Path(dataset_dir)
    derived = dataset["metadata"]["derived"]
    min_ontarget = float(derived["min_ontarget_energy"])
    max_ontarget = float(derived["max_ontarget_energy"])
    if output_path is None:
        cutoff_label = str(offtarget_limit).replace(".", "p")
        output_path = dataset_path / "results" / f"hybrid_offline_limit{cutoff_label}_seed{random_seed}.xlsx"
    random.seed(random_seed)
    if not 0 <= prune_fraction <= 1:
        raise ValueError("prune_fraction must be between 0 and 1.")
    if vc_max_iterations < 1:
        raise ValueError("vc_max_iterations must be at least 1.")

    _status(
        "Offline hybrid start: "
        f"initial fresh pairs={initial_fresh_pair_count}, "
        "termination=exact_pool_exhaustion"
    )
    retained_pair_ids = set()
    retained_pairs = []
    total_nupack_calls = 0
    generation_data = []
    stopped_reason = None

    _status(
        f"=== Initial graph search ===\n"
        f"Selecting {initial_fresh_pair_count} sequence pairs for the initial graph search..."
    )
    _, seed_pair_ids, seed_stop_reason, seed_selection_calls, seed_stats = _select_subset_in_energy_range_offline(
        dataset,
        energy_min=min_ontarget,
        energy_max=max_ontarget,
        self_energy_min=self_energy_limit,
        max_size=int(initial_fresh_pair_count),
        avoid_indices=set(),
        retained_pair_ids=[],
        offtarget_limit=offtarget_limit,
    )
    total_nupack_calls += seed_selection_calls
    _status(
        f"Selected {len(seed_pair_ids)} sequence pairs for the initial graph search "
        f"[{seed_selection_calls} virtual NUPACK calls]"
    )

    if not seed_pair_ids:
        raise ValueError(
            "Offline hybrid found no sequence pairs during the initial graph search; "
            "no report can be written."
        )

    seed_verified = _build_verified_from_dataset(dataset, seed_pair_ids)
    _status(f"Running graph search on {len(seed_pair_ids)} sequence pairs...")
    retained_pair_ids, seed_vc_calls = _run_vertex_cover_offline(
        seed_pair_ids,
        dataset,
        offtarget_limit,
        prune_fraction,
        vc_max_iterations,
    )
    total_nupack_calls += seed_vc_calls
    retained_pairs = [get_pair_by_global_id(dataset, global_id) for global_id in sorted(retained_pair_ids)]
    _status(
        f"Initial orthogonal sequence pairs identified: {len(retained_pair_ids)} | "
        f"NUPACK calls: {total_nupack_calls}"
    )
    generation_data.append(
        _build_progress_row(
            pass_name="seed",
            pairs_collected=len(seed_pair_ids),
            pairs_after_vc=len(retained_pair_ids),
            total_retained=len(retained_pair_ids),
            nupack_calls_executed=seed_selection_calls + seed_vc_calls,
            stopped_early=seed_stop_reason is not None,
            attempts=seed_stats["attempts"],
            passed_ontarget_and_self=seed_stats["passed_ontarget_and_self"],
            passed_homodimer=seed_stats["passed_homodimer"],
            accepted_into_pool=seed_stats["accepted_into_pool"],
            notes=seed_stop_reason,
        )
    )

    if seed_stop_reason == "pool_exhausted":
        stopped_reason = "pool_exhausted"
        _status("Offline hybrid exhausted the finite pool before candidate collection.")
    else:
        _status(
            f"=== Candidate collection ===\n"
            f"Collecting candidate sequence pairs against {len(retained_pair_ids)} "
            f"initial orthogonal sequence pairs..."
        )
        _, collection_pair_ids, collection_stop_reason, collection_calls, collection_stats = (
            _select_subset_in_energy_range_offline(
                dataset,
                energy_min=min_ontarget,
                energy_max=max_ontarget,
                self_energy_min=self_energy_limit,
                max_size=np.inf,
                avoid_indices=set(retained_pair_ids),
                retained_pair_ids=sorted(retained_pair_ids),
                offtarget_limit=offtarget_limit,
            )
        )
        total_nupack_calls += collection_calls
        _status(
            f"Collected {len(collection_pair_ids)} candidate sequence pairs "
            f"[{collection_calls} virtual NUPACK calls]"
        )

        added_pairs_after_vc = 0
        if collection_pair_ids:
            _status(f"Running final graph search on {len(collection_pair_ids)} candidate sequence pairs...")
            independent_set, collection_vc_calls = _run_vertex_cover_offline(
                collection_pair_ids,
                dataset,
                offtarget_limit,
                prune_fraction,
                vc_max_iterations,
            )
            total_nupack_calls += collection_vc_calls
            retained_pair_ids.update(independent_set)
            retained_pairs = [get_pair_by_global_id(dataset, global_id) for global_id in sorted(retained_pair_ids)]
            added_pairs_after_vc = len(independent_set)
            _status(
                f"Orthogonal sequence pairs found in candidate pool: {added_pairs_after_vc} | "
                f"Total orthogonal sequence pairs: {len(retained_pair_ids)} | "
                f"NUPACK calls: {total_nupack_calls}"
            )
        else:
            collection_vc_calls = 0
            _status("No candidate sequence pairs collected.")

        generation_data.append(
            _build_progress_row(
                pass_name="collection",
                pairs_collected=len(collection_pair_ids),
                pairs_after_vc=added_pairs_after_vc,
                total_retained=len(retained_pair_ids),
                nupack_calls_executed=collection_calls + collection_vc_calls,
                stopped_early=collection_stop_reason is not None,
                attempts=collection_stats["attempts"],
                passed_ontarget_and_self=collection_stats["passed_ontarget_and_self"],
                passed_homodimer=collection_stats["passed_homodimer"],
                accepted_into_pool=collection_stats["accepted_into_pool"],
                notes=collection_stop_reason,
            )
        )
        stopped_reason = collection_stop_reason or "pool_exhausted"

    _status(f"Offline hybrid total virtual NUPACK calls: {total_nupack_calls}")
    selected_sequence_data = get_selected_rows(dataset, sorted(retained_pair_ids))
    seed_sequence_data = get_selected_rows(dataset, seed_pair_ids)
    verified = verify_selected_pairs(selected_sequence_data, nupack_params=dataset["metadata"]["nupack"])
    return _write_benchmark_result_xlsx(
        output_path,
        algorithm_name="hybrid_offline",
        dataset=dataset,
        selected_sequence_data=selected_sequence_data,
        verified=verified,
        search_params={
            "offtarget_limit": float(offtarget_limit),
            "max_ontarget": float(max_ontarget),
            "min_ontarget": float(min_ontarget),
            "self_energy_limit": float(self_energy_limit),
            "initial_fresh_pair_count": int(initial_fresh_pair_count),
            "prune_fraction": float(prune_fraction),
            "vc_max_iterations": int(vc_max_iterations),
            "random_seed": int(random_seed),
            "total_nupack_calls": int(total_nupack_calls),
        },
        seed_sequence_data=seed_sequence_data,
        seed_verified=seed_verified,
        extra_metadata={
            "stopped_reason": stopped_reason,
        },
        extra_sheets={"search_progress": generation_data},
    )
