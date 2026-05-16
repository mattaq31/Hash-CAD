#!/usr/bin/env python3
"""
search_algorithm.py

Purpose:
    Two-pass hybrid search for selecting large orthogonal DNA sequence sets.

    The algorithm works in two passes:

    Pass 1 (Seed): Collect a fixed number of candidate pairs filtered only by
    on-target energy and self-energy. Compute the full pairwise off-target
    matrix and run an iterative vertex-cover heuristic to resolve conflicts.
    Survivors become the retained set.

    Pass 2 (Collection): Collect additional candidate pairs that are each
    cross-referenced against the retained set (O(fresh * retained) checks).
    Because cross-referencing uses zero allowed violations, every accepted
    candidate is guaranteed compatible with all retained pairs. This means
    the final vertex cover only needs to resolve conflicts among the fresh
    candidates themselves (O(fresh^2)), not the full (fresh + retained)^2
    matrix. Survivors are unioned into the retained set.

    The module exposes `hybrid_search` as its main entry point, called by:
    - `scripts/run_sequence_search.py` (standalone CLI)
    - `streamlit_app/tabs/tab_search.py` (interactive UI)
    - `scripts/benchmarking/long_seq/scripts/run_long_seq_hybrid_search.py`
"""

import logging
import time

import numpy as np

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.vertex_cover_algorithms import (
    build_edges,
    iterative_vertex_cover_refinement,
)

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())


def _num_vertices_to_remove(vertex_count, prune_fraction):
    """
    Compute how many vertices to perturb per vertex-cover refinement step.

    Purpose
    -------
    The iterative vertex-cover heuristic removes a small subset of vertices
    each iteration to escape local optima. This helper translates the
    user-facing `prune_fraction` (0–1) into an absolute vertex count,
    guaranteeing at least 1 vertex is removed when the fraction is positive.

    :param vertex_count: Total number of vertices in the conflict graph.
    :type vertex_count: int
    :param prune_fraction: Fraction of vertices to perturb (0 disables).
    :type prune_fraction: float
    :returns: Number of vertices to remove per iteration.
    :rtype: int
    """
    if prune_fraction <= 0:
        return 0
    return max(1, int(round(int(vertex_count) * float(prune_fraction))))


def _status(message):
    print(message, flush=True)
    logger.info(message)


def _run_vertex_cover(subset, indices, offtarget_limit, prune_fraction, vc_max_iterations):
    """
    Compute off-target matrix, build conflict graph, and run vertex cover.

    Purpose
    -------
    This is the shared graph-pruning step used in both passes of the hybrid
    search and in progress-report peeks. It computes the full pairwise
    off-target energy matrix for the given subset, builds edges between pairs
    that violate the off-target threshold, and runs the iterative vertex-cover
    heuristic to find a large independent set (conflict-free subset).

    :param subset: Sequence pairs to evaluate, as (seq, rc_seq) tuples.
    :type subset: list[tuple[str, str]]
    :param indices: Stable pair IDs aligned with `subset`.
    :type indices: list[int]
    :param offtarget_limit: Energy threshold below which a pairwise
                            interaction counts as a conflict.
    :type offtarget_limit: float
    :param prune_fraction: Fraction of vertices perturbed per refinement step.
    :type prune_fraction: float
    :param vc_max_iterations: Maximum refinement iterations.
    :type vc_max_iterations: int
    :returns: (independent_set_ids, off_target_nupack_calls)
    :rtype: tuple[set[int], int]
    """
    off_target_nupack_calls = sc.estimate_offtarget_nupack_calls(len(subset))
    off_e_subset = sc.compute_offtarget_energies(subset)
    edges = build_edges(off_e_subset, indices, offtarget_limit)
    removed_vertices, _ = iterative_vertex_cover_refinement(
        indices,
        edges,
        avoid_V=None,
        max_iterations=vc_max_iterations,
        num_vertices_to_remove=_num_vertices_to_remove(len(indices), prune_fraction),
        show_progress=False,
    )
    independent_set = set(indices) - removed_vertices
    return independent_set, off_target_nupack_calls


def _pairs_from_ids(sequence_pairs, pair_ids):
    return [sequence_pairs.get_pair_by_id(idx) for idx in sorted(pair_ids)]


def _build_progress_row(
    *,
    pass_name,
    pairs_collected,
    pairs_after_vc,
    total_retained,
    nupack_calls_executed,
    stopped_early,
    attempts,
    passed_ontarget_and_self,
    passed_homodimer,
    accepted_into_pool,
    notes,
):
    """
    Build one standardized search-progress row for workbook/report consumers.

    The reporting contract is shared across naive and hybrid workflows, so the
    search code centralizes row construction to keep the per-pass logic focused
    on the algorithm rather than repeated sheet-oriented dict assembly.
    """
    return {
        "pass": pass_name,
        "pairs_collected": pairs_collected,
        "pairs_after_vc": pairs_after_vc,
        "total_retained": total_retained,
        "nupack_calls_executed": nupack_calls_executed,
        "stopped_early": stopped_early,
        "attempts": attempts,
        "passed_ontarget_and_self": passed_ontarget_and_self,
        "passed_homodimer": passed_homodimer,
        "accepted_into_pool": accepted_into_pool,
        "notes": notes,
    }


def _normalize_stop_reason(raw_reason):
    if raw_reason is None:
        return None
    if raw_reason == "stop_event":
        return "app_stop_event"
    if raw_reason == "nupack_limit":
        return "total_nupack_budget"
    return raw_reason


def _is_duplicate_streak_reason(raw_reason):
    return bool(raw_reason and raw_reason.startswith("duplicate_streak_limit_reached="))


def _run_seed_pass(
    *,
    sequence_pairs,
    offtarget_limit,
    max_ontarget,
    min_ontarget,
    self_energy_limit,
    initial_fresh_pair_count,
    total_nupack_budget,
    prune_fraction,
    vc_max_iterations,
    stop_event,
    start_t,
):
    """
    Run hybrid pass 1 and return only phase-local results.

    Accounting contract
    -------------------
    Count only search-essential NUPACK work for this phase:
    - subset selection
    - final seed vertex-cover matrix cost

    Do not count diagnostic/reporting recomputation such as `seed_verified`.
    """
    if stop_event is not None and stop_event.is_set():
        _status("Stop event detected before pass 1.")
        return {
            "seed_pairs": [],
            "seed_pair_ids": [],
            "seed_verified": None,
            "retained_pair_ids": set(),
            "retained_pairs": [],
            "accounted_nupack_calls": 0,
            "generation_row": None,
            "stop_reason": "app_stop_event",
            "continue_to_pass2": False,
        }

    _status(
        f"=== Pass 1: Initial sampling ==="
        f"\nSampling {initial_fresh_pair_count} candidate pairs (energy + self-energy filter)..."
    )
    subset, indices, raw_stop_reason, selection_nupack_calls, seed_stats = sc.select_subset_in_energy_range(
        sequence_pairs,
        energy_min=min_ontarget,
        energy_max=max_ontarget,
        self_energy_min=self_energy_limit,
        offtarget_limit=offtarget_limit,
        max_size=initial_fresh_pair_count,
        fresh_pair_search_budget=int(total_nupack_budget) if total_nupack_budget != np.inf else None,
        stop_event=stop_event,
    )
    seed_pairs = list(subset)
    seed_pair_ids = list(indices)
    _status(f"Selected {len(indices)} candidate pairs [{selection_nupack_calls} NUPACK calls]")

    canonical_stop_reason = _normalize_stop_reason(raw_stop_reason)
    if not indices:
        if raw_stop_reason == "stop_event":
            _status("Stop event detected during pass 1. Saving partial result.")
        elif raw_stop_reason == "keyboard_interrupt":
            _status("Keyboard interrupt detected during pass 1. Saving partial result.")
        elif _is_duplicate_streak_reason(raw_stop_reason):
            _status("Pool exhaustion heuristic reached during pass 1 before any candidate pairs were collected.")
        elif canonical_stop_reason == "total_nupack_budget":
            _status("NUPACK budget exhausted during pass 1 before any candidate pairs were collected.")
        else:
            _status("No sequences found.")
        return {
            "seed_pairs": seed_pairs,
            "seed_pair_ids": seed_pair_ids,
            "seed_verified": None,
            "retained_pair_ids": set(),
            "retained_pairs": [],
            "accounted_nupack_calls": selection_nupack_calls,
            "generation_row": None,
            "stop_reason": canonical_stop_reason or "no_sequences_found",
            "continue_to_pass2": False,
        }

    if raw_stop_reason == "stop_event":
        _status("Stop event detected during pass 1. Saving partial result.")
    elif raw_stop_reason == "keyboard_interrupt":
        _status("Keyboard interrupt detected during pass 1. Saving partial result.")

    seed_on_target, seed_self_seq, seed_self_rc = sc.compute_ontarget_energies(seed_pairs)
    _status(f"Running vertex cover on {len(subset)} pairs...")

    seed_off_target = sc.compute_offtarget_energies(subset)
    seed_verified = {
        "on_target_energies": seed_on_target,
        "self_energy_seqs": seed_self_seq,
        "self_energy_rc_seqs": seed_self_rc,
        "off_target": seed_off_target,
    }
    seed_vc_nupack_calls = sc.estimate_offtarget_nupack_calls(len(subset))
    edges = build_edges(seed_off_target, indices, offtarget_limit)
    removed_vertices, _ = iterative_vertex_cover_refinement(
        indices,
        edges,
        avoid_V=None,
        max_iterations=vc_max_iterations,
        num_vertices_to_remove=_num_vertices_to_remove(len(indices), prune_fraction),
        show_progress=False,
    )
    retained_pair_ids = set(indices) - removed_vertices
    retained_pairs = _pairs_from_ids(sequence_pairs, retained_pair_ids)

    phase_nupack_calls = selection_nupack_calls + seed_vc_nupack_calls
    elapsed_s = time.time() - start_t
    _status(
        f"Independent set: {len(retained_pair_ids)} pairs retained | "
        f"NUPACK calls: {phase_nupack_calls} | elapsed={elapsed_s:.1f}s"
    )

    generation_row = _build_progress_row(
        pass_name="seed",
        pairs_collected=len(indices),
        pairs_after_vc=len(retained_pair_ids),
        total_retained=len(retained_pair_ids),
        nupack_calls_executed=phase_nupack_calls,
        stopped_early=raw_stop_reason is not None,
        attempts=seed_stats["attempts"],
        passed_ontarget_and_self=seed_stats["passed_ontarget_and_self"],
        passed_homodimer=seed_stats["passed_homodimer"],
        accepted_into_pool=seed_stats["accepted_into_pool"],
        notes=raw_stop_reason,
    )

    stop_reason = None
    continue_to_pass2 = True
    if raw_stop_reason == "stop_event":
        stop_reason = canonical_stop_reason
        continue_to_pass2 = False
        _status("Stop event detected before pass 2.")
    elif raw_stop_reason == "keyboard_interrupt":
        stop_reason = canonical_stop_reason
        continue_to_pass2 = False
        _status("Keyboard interrupt detected during pass 1. Skipping pass 2.")
    elif _is_duplicate_streak_reason(raw_stop_reason):
        stop_reason = canonical_stop_reason
        continue_to_pass2 = False
        _status("Pool exhaustion heuristic reached during pass 1. Skipping pass 2.")
    elif total_nupack_budget != np.inf and phase_nupack_calls >= total_nupack_budget:
        stop_reason = "total_nupack_budget"
        continue_to_pass2 = False
        _status("NUPACK budget exhausted after pass 1.")

    return {
        "seed_pairs": seed_pairs,
        "seed_pair_ids": seed_pair_ids,
        "seed_verified": seed_verified,
        "retained_pair_ids": retained_pair_ids,
        "retained_pairs": retained_pairs,
        "accounted_nupack_calls": phase_nupack_calls,
        "generation_row": generation_row,
        "stop_reason": stop_reason,
        "continue_to_pass2": continue_to_pass2,
    }


def _run_collection_pass(
    *,
    sequence_pairs,
    retained_pair_ids,
    retained_pairs,
    offtarget_limit,
    max_ontarget,
    min_ontarget,
    self_energy_limit,
    remaining_budget,
    prune_fraction,
    vc_max_iterations,
    progress_report_interval_s,
    progress_report_interval_min,
    stop_event,
    start_t,
    base_nupack_calls,
):
    """
    Run hybrid pass 2 and return only phase-local results.

    Accounting contract
    -------------------
    Count only search-essential NUPACK work for this phase:
    - live cross-referenced collection
    - final pass-2 vertex-cover matrix cost

    Exclude progress-report peek VC work. Those calls are diagnostic only and
    intentionally stay out of the search budget/accounting.
    """
    if stop_event is not None and stop_event.is_set():
        _status("Stop event detected before pass 2.")
        return {
            "retained_pair_ids": retained_pair_ids,
            "retained_pairs": retained_pairs,
            "accounted_nupack_calls": 0,
            "generation_row": None,
            "stop_reason": "app_stop_event",
        }

    _status(
        f"=== Pass 2: Cross-referenced collection ==="
        f"\nCollecting candidate pairs cross-referenced against "
        f"{len(retained_pair_ids)} retained (NUPACK budget: {remaining_budget})..."
    )

    collection_state = {
        "subset": [],
        "indices": [],
        "tested_indices": set(retained_pair_ids),
        "attempts": 0,
        "nupack_calls": 0,
        "passed_ontarget_and_self": 0,
        "passed_homodimer": 0,
    }
    pass2_budget = int(remaining_budget) if remaining_budget != np.inf else None
    chunk_reason = None

    while True:
        chunk_timeout = progress_report_interval_s if progress_report_interval_s is not None else None
        _, _, chunk_reason, _, collection_state = sc.select_subset_in_energy_range(
            sequence_pairs,
            energy_min=min_ontarget,
            energy_max=max_ontarget,
            self_energy_min=self_energy_limit,
            retained_pairs=retained_pairs,
            allowed_violations=0,
            offtarget_limit=offtarget_limit,
            fresh_pair_search_budget=pass2_budget,
            timeout_s=chunk_timeout,
            stop_event=stop_event,
            quiet_timeout=(chunk_timeout is not None),
            prior_state=collection_state,
        )
        accounted_total_so_far = base_nupack_calls + collection_state["nupack_calls"]

        if chunk_reason != "timeout":
            break

        _status(f"--- Progress report triggered ({progress_report_interval_min} min interval reached) ---")
        if collection_state["indices"]:
            _status(
                f"Running peek vertex cover on {len(collection_state['indices'])} collected candidate pairs..."
            )
            peek_set, _ = _run_vertex_cover(
                collection_state["subset"],
                collection_state["indices"],
                offtarget_limit,
                prune_fraction,
                vc_max_iterations,
            )
            elapsed_s = time.time() - start_t
            _status(
                f"Candidate pairs collected so far: {len(collection_state['indices'])} | "
                f"Retained from seed: {len(retained_pair_ids)} | "
                f"New from collection (after peek VC): {len(peek_set)} | "
                f"Estimated total: {len(retained_pair_ids) + len(peek_set)} | "
                f"NUPACK calls: {accounted_total_so_far} | elapsed={elapsed_s:.1f}s"
                f"\n--- Continuing collection ---"
            )
        else:
            elapsed_s = time.time() - start_t
            _status(
                f"No candidate pairs collected yet | "
                f"NUPACK calls: {accounted_total_so_far} | elapsed={elapsed_s:.1f}s"
                f"\n--- Continuing collection ---"
            )

    subset = collection_state["subset"]
    indices = collection_state["indices"]
    _status(f"Collected {len(indices)} candidate pairs [{collection_state['nupack_calls']} pass 2 NUPACK calls]")

    pass2_vc_nupack_calls = 0
    canonical_stop_reason = _normalize_stop_reason(chunk_reason)
    updated_retained_pair_ids = set(retained_pair_ids)
    updated_retained_pairs = list(retained_pairs)

    if chunk_reason in {"stop_event", "keyboard_interrupt"}:
        _status("Stop detected during pass 2 collection. Skipping final vertex cover.")
    elif indices:
        _status(f"Running vertex cover on {len(indices)} candidate pairs...")
        independent_set, pass2_vc_nupack_calls = _run_vertex_cover(
            subset,
            indices,
            offtarget_limit,
            prune_fraction,
            vc_max_iterations,
        )
        updated_retained_pair_ids.update(independent_set)
        updated_retained_pairs = _pairs_from_ids(sequence_pairs, updated_retained_pair_ids)

        elapsed_s = time.time() - start_t
        _status(
            f"Independent set: {len(independent_set)} additional pairs found | "
            f"Total retained: {len(updated_retained_pair_ids)} | "
            f"NUPACK calls: {base_nupack_calls + collection_state['nupack_calls'] + pass2_vc_nupack_calls} | "
            f"elapsed={elapsed_s:.1f}s"
        )
    else:
        _status("No candidate pairs found.")

    phase_nupack_calls = collection_state["nupack_calls"] + pass2_vc_nupack_calls
    generation_row = _build_progress_row(
        pass_name="collection",
        pairs_collected=len(indices),
        pairs_after_vc=len(updated_retained_pair_ids) - len(retained_pair_ids) if indices else 0,
        total_retained=len(updated_retained_pair_ids),
        nupack_calls_executed=phase_nupack_calls,
        stopped_early=chunk_reason is not None,
        attempts=collection_state["attempts"],
        passed_ontarget_and_self=collection_state["passed_ontarget_and_self"],
        passed_homodimer=collection_state["passed_homodimer"],
        accepted_into_pool=collection_state["accepted_into_pool"],
        notes=chunk_reason,
    )
    return {
        "retained_pair_ids": updated_retained_pair_ids,
        "retained_pairs": updated_retained_pairs,
        "accounted_nupack_calls": phase_nupack_calls,
        "generation_row": generation_row,
        "stop_reason": canonical_stop_reason,
    }


def hybrid_search(
    sequence_pairs,
    offtarget_limit,
    max_ontarget,
    min_ontarget,
    self_energy_limit,
    initial_fresh_pair_count=200,
    total_nupack_budget=np.inf,
    prune_fraction=0.2,
    vc_max_iterations=5000,
    stop_event=None,
    return_diagnostics=False,
    progress_report_interval_min=None,
):
    """
    Search for a large orthogonal DNA sequence set using a two-pass strategy.

    Purpose
    -------
    This is the main entry point for orthogonal sequence selection. It
    combines energy-filtered sampling, pairwise cross-referencing, and
    graph-based conflict resolution to find the largest possible set of
    mutually orthogonal sequence pairs within a given compute budget.

    The two-pass design separates exploration (pass 1) from exploitation
    (pass 2). Pass 1 builds a diverse seed set cheaply. Pass 2 extends it
    by collecting only candidates that are already compatible with the seed,
    which reduces the final vertex-cover cost from O((seed+fresh)^2) to
    O(fresh^2).

    Pass 1 (Seed):
        Collect `initial_fresh_pair_count` candidate pairs filtered by
        on-target energy and self-energy. Compute the full pairwise off-target
        matrix and run the iterative vertex-cover heuristic to resolve
        conflicts. Survivors become the retained set. The seed off-target
        matrix is cached in the diagnostics for reporting without recomputation.

    Pass 2 (Collection):
        Collect candidate pairs cross-referenced against the retained set
        (zero allowed violations) until `total_nupack_budget` is exhausted or
        the pool is empty. Run vertex cover on fresh candidates only. Union
        survivors into the retained set. When `progress_report_interval_min`
        is set, collection is chunked into timed intervals; at each boundary
        a peek vertex cover is run on all accumulated candidates to report an
        estimated total without committing anything.

    Termination
    -----------
    The search terminates for one of these reasons, recorded in the
    diagnostics as `stopped_reason`:

    - ``"app_stop_event"``: external stop signal (threading.Event) was set
    - ``"keyboard_interrupt"``: user pressed Ctrl-C
    - ``"total_nupack_budget"``: NUPACK call budget exhausted
    - ``"duplicate_streak_limit_reached=<N>"``: live sampler repeatedly
      returned already-seen IDs and was treated as effectively exhausted
    - ``"no_sequences_found"``: no candidates passed energy filter in pass 1
    - ``"pool_exhausted"``: all candidates evaluated without budget/stop hit

    :param sequence_pairs: Candidate sequence source. Must provide
        `sample_pair()` for live draws and `get_pair_by_id(pair_id)` for stable
        lookup of retained IDs.
    :type sequence_pairs: SequencePairRegistry or compatible live source

    :param offtarget_limit: Energy threshold below which a pairwise
        interaction counts as a conflict edge in the vertex-cover graph.
    :type offtarget_limit: float

    :param max_ontarget: Upper bound for acceptable on-target energy.
    :type max_ontarget: float

    :param min_ontarget: Lower bound for acceptable on-target energy.
    :type min_ontarget: float

    :param self_energy_limit: Minimum acceptable self-energy (secondary
        structure) for each strand of a candidate pair.
    :type self_energy_limit: float

    :param initial_fresh_pair_count: Number of pairs to collect in pass 1
        before the first vertex-cover run.
    :type initial_fresh_pair_count: int

    :param total_nupack_budget: Overall NUPACK call budget for the entire
        search. Defaults to infinity (run until pool is exhausted or stopped).
    :type total_nupack_budget: float

    :param prune_fraction: Fraction of vertices perturbed per vertex-cover
        refinement iteration. Higher values escape local optima more
        aggressively but may discard good vertices.
    :type prune_fraction: float

    :param vc_max_iterations: Maximum iterations in vertex-cover refinement.
    :type vc_max_iterations: int

    :param stop_event: Optional external stop signal (threading.Event). When
        set, the search terminates gracefully and returns partial results.
        Used by the Streamlit app's "Stop Searching" button.
    :type stop_event: threading.Event or None

    :param return_diagnostics: When True, return a structured diagnostics dict
        instead of just the final pairs. The dict contains seed data, verified
        energies, generation progress, search parameters, and stop reason.
    :type return_diagnostics: bool

    :param progress_report_interval_min: If set, report estimated pair count
        during pass 2 at this interval (integer minutes, 30 s floor enforced).
        None disables progress reporting.
    :type progress_report_interval_min: int or None

    :returns: Final sequence pairs as (seq, rc_seq) tuples, or a diagnostics
        dict when `return_diagnostics=True`.
    :rtype: list[tuple[str, str]] or dict
    """
    if not hasattr(sequence_pairs, "sample_pair") or not hasattr(sequence_pairs, "get_pair_by_id"):
        raise TypeError(
            "hybrid_search requires a live sequence source with sample_pair() "
            "and get_pair_by_id(pair_id) methods."
        )

    seq_length = getattr(sequence_pairs, "length", None)
    fivep_ext = getattr(sequence_pairs, "fivep_ext", None)
    threep_ext = getattr(sequence_pairs, "threep_ext", None)
    unwanted = getattr(sequence_pairs, "unwanted_substrings", None)
    apply_to = getattr(sequence_pairs, "apply_unwanted_to", None)

    material = hf.NUPACK_PARAMS.get("MATERIAL")
    celsius = hf.NUPACK_PARAMS.get("CELSIUS")
    sodium = hf.NUPACK_PARAMS.get("SODIUM")
    magnesium = hf.NUPACK_PARAMS.get("MAGNESIUM")

    if not 0 <= prune_fraction <= 1:
        raise ValueError("prune_fraction must be between 0 and 1.")
    if vc_max_iterations < 1:
        raise ValueError("vc_max_iterations must be at least 1.")
    if total_nupack_budget != np.inf:
        total_nupack_budget = int(total_nupack_budget)
        if total_nupack_budget < 1:
            raise ValueError("total_nupack_budget must be a positive integer or inf.")

    if progress_report_interval_min is not None:
        progress_report_interval_s = max(30, int(progress_report_interval_min) * 60)
    else:
        progress_report_interval_s = None

    total_nupack_calls = 0
    retained_pair_ids = set()
    retained_pairs = []
    seed_pairs = []
    seed_pair_ids = []
    seed_verified = None
    generation_data = []
    stopped_reason = None
    start_t = time.time()

    logger.info(
        "Search start params: "
        f"length: {seq_length}, "
        f"5' extension: {fivep_ext!r}, "
        f"3' extension: {threep_ext!r}, "
        f"unwanted: {unwanted}, "
        f"apply to: {apply_to}, "
        f"material: {material}, "
        f"celsius: {celsius}, "
        f"sodium: {sodium}, "
        f"magnesium: {magnesium}, "
        f"min on-target: {min_ontarget}, "
        f"max on-target: {max_ontarget}, "
        f"min off-target: {offtarget_limit}, "
        f"min secondary-structure: {self_energy_limit}, "
        f"initial fresh pair count: {initial_fresh_pair_count}, "
        f"total NUPACK budget: {total_nupack_budget}, "
        f"prune fraction: {prune_fraction}, "
        f"vc max iterations: {vc_max_iterations}"
    )

    try:
        seed_outcome = _run_seed_pass(
            sequence_pairs=sequence_pairs,
            offtarget_limit=offtarget_limit,
            max_ontarget=max_ontarget,
            min_ontarget=min_ontarget,
            self_energy_limit=self_energy_limit,
            initial_fresh_pair_count=initial_fresh_pair_count,
            total_nupack_budget=total_nupack_budget,
            prune_fraction=prune_fraction,
            vc_max_iterations=vc_max_iterations,
            stop_event=stop_event,
            start_t=start_t,
        )
        total_nupack_calls += seed_outcome["accounted_nupack_calls"]
        seed_pairs = seed_outcome["seed_pairs"]
        seed_pair_ids = seed_outcome["seed_pair_ids"]
        seed_verified = seed_outcome["seed_verified"]
        retained_pair_ids = seed_outcome["retained_pair_ids"]
        retained_pairs = seed_outcome["retained_pairs"]
        if seed_outcome["generation_row"] is not None:
            generation_data.append(seed_outcome["generation_row"])
        stopped_reason = seed_outcome["stop_reason"]

        if seed_outcome["continue_to_pass2"]:
            remaining_budget = total_nupack_budget - total_nupack_calls
            collection_outcome = _run_collection_pass(
                sequence_pairs=sequence_pairs,
                retained_pair_ids=retained_pair_ids,
                retained_pairs=retained_pairs,
                offtarget_limit=offtarget_limit,
                max_ontarget=max_ontarget,
                min_ontarget=min_ontarget,
                self_energy_limit=self_energy_limit,
                remaining_budget=remaining_budget,
                prune_fraction=prune_fraction,
                vc_max_iterations=vc_max_iterations,
                progress_report_interval_s=progress_report_interval_s,
                progress_report_interval_min=progress_report_interval_min,
                stop_event=stop_event,
                start_t=start_t,
                base_nupack_calls=total_nupack_calls,
            )
            total_nupack_calls += collection_outcome["accounted_nupack_calls"]
            retained_pair_ids = collection_outcome["retained_pair_ids"]
            retained_pairs = collection_outcome["retained_pairs"]
            if collection_outcome["generation_row"] is not None:
                generation_data.append(collection_outcome["generation_row"])
            if collection_outcome["stop_reason"] is not None:
                stopped_reason = collection_outcome["stop_reason"]

    except KeyboardInterrupt:
        stopped_reason = "keyboard_interrupt"
        _status("Interrupted by user. Saving best result so far...")

    if stopped_reason is None:
        stopped_reason = "pool_exhausted"

    final_pair_ids = sorted(retained_pair_ids)
    final_pairs = _pairs_from_ids(sequence_pairs, retained_pair_ids)

    elapsed_s = time.time() - start_t
    _status(
        f"Total NUPACK calls overall: {total_nupack_calls} "
        f"(elapsed={elapsed_s:.1f}s)"
    )
    if return_diagnostics:
        return {
            "final_pairs": final_pairs,
            "final_pair_ids": final_pair_ids,
            "seed_pairs": seed_pairs,
            "seed_pair_ids": seed_pair_ids,
            "seed_verified": seed_verified,
            "generation_data": generation_data,
            "total_nupack_calls": int(total_nupack_calls),
            "search_params": {
                "offtarget_limit": float(offtarget_limit),
                "max_ontarget": float(max_ontarget),
                "min_ontarget": float(min_ontarget),
                "self_energy_limit": float(self_energy_limit),
                "initial_fresh_pair_count": int(initial_fresh_pair_count),
                "total_nupack_budget": float(total_nupack_budget),
                "prune_fraction": float(prune_fraction),
                "vc_max_iterations": int(vc_max_iterations),
                "search_duration_s": float(elapsed_s),
            },
            "sequence_source": {
                "length": seq_length,
                "fivep_ext": fivep_ext,
                "threep_ext": threep_ext,
                "unwanted_substrings": unwanted,
                "apply_unwanted_to": apply_to,
            },
            "nupack": {
                "material": material,
                "celsius": celsius,
                "sodium": sodium,
                "magnesium": magnesium,
            },
            "stopped_reason": stopped_reason,
        }
    return final_pairs
