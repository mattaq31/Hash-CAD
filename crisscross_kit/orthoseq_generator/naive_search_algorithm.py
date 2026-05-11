#!/usr/bin/env python3
"""
Live greedy baseline for orthogonal sequence search.

This module provides the on-the-fly counterpart to the dataset-backed naive
benchmark scaffold. It uses direct NUPACK calls against a live sequence source
and records diagnostics in the same general shape as the hybrid search.
"""

from __future__ import annotations

import logging
import time

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.energy_computations import (
    compute_nupack_energy,
    crossreference_sequences,
)

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())


def _status(message):
    print(message, flush=True)
    logger.info(message)


def naive_search(
    sequence_pairs,
    offtarget_limit,
    max_ontarget,
    min_ontarget,
    self_energy_limit,
    total_nupack_budget=None,
    progress_every=250,
    duplicate_streak_limit=1_000_000,
    min_progress_interval_s=1.0,
    stop_event=None,
    return_diagnostics=False,
):
    """
    Greedily build an orthogonal set by accepting one live candidate at a time.

    Procedure
    ---------
    1. Sample one fresh candidate pair from the live sequence source.
    2. Check its on-target and self-structure values directly with NUPACK.
    3. Reject the pair if either same-strand homodimer violates the off-target
       limit.
    4. Cross-reference the candidate against the already accepted set.
    5. Accept the pair if all checks pass, then continue until the total
       NUPACK budget is reached.
    """
    seq_length = getattr(sequence_pairs, "length", None)
    fivep_ext = getattr(sequence_pairs, "fivep_ext", None)
    threep_ext = getattr(sequence_pairs, "threep_ext", None)
    unwanted = getattr(sequence_pairs, "unwanted_substrings", None)
    apply_to = getattr(sequence_pairs, "apply_unwanted_to", None)

    material = hf.NUPACK_PARAMS.get("MATERIAL")
    celsius = hf.NUPACK_PARAMS.get("CELSIUS")
    sodium = hf.NUPACK_PARAMS.get("SODIUM")
    magnesium = hf.NUPACK_PARAMS.get("MAGNESIUM")

    if progress_every is not None:
        progress_every = int(progress_every)
        if progress_every < 1:
            raise ValueError("progress_every must be a positive integer or None.")
    duplicate_streak_limit = int(duplicate_streak_limit)
    if duplicate_streak_limit < 1:
        raise ValueError("duplicate_streak_limit must be a positive integer.")
    min_progress_interval_s = float(min_progress_interval_s)
    if min_progress_interval_s < 0:
        raise ValueError("min_progress_interval_s must be non-negative.")
    if total_nupack_budget is not None:
        total_nupack_budget = int(total_nupack_budget)
        if total_nupack_budget < 1:
            raise ValueError("total_nupack_budget must be a positive integer or None.")

    selected_pairs = []
    selected_pair_ids = []
    tested_pair_ids = set()
    attempts = 0
    total_nupack_calls = 0
    progress_rows = []
    stopped_reason = None
    start_t = time.time()
    last_progress_t = start_t - min_progress_interval_s
    duplicate_streak = 0

    logger.info(
        "Naive search start params: "
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
        f"progress every: {progress_every}, "
        f"duplicate streak limit: {duplicate_streak_limit}, "
        f"min progress interval s: {min_progress_interval_s}, "
        f"total NUPACK budget: {total_nupack_budget}"
    )

    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                stopped_reason = "stop_event"
                _status("Stop event detected. Stopping naive search.")
                break
            if total_nupack_budget is not None and total_nupack_calls >= total_nupack_budget:
                stopped_reason = "total_nupack_budget"
                _status("Total NUPACK budget reached. Stopping naive search.")
                break

            attempts += 1
            if progress_every and attempts % progress_every == 0:
                now_t = time.time()
                if (now_t - last_progress_t) >= min_progress_interval_s:
                    elapsed_s = now_t - start_t
                    _status(
                        f"Naive progress: {len(selected_pairs)} accepted "
                        f"after {attempts} attempts and {total_nupack_calls} NUPACK calls "
                        f"(elapsed={elapsed_s:.1f}s)."
                    )
                    last_progress_t = now_t

            pair_id, pair = sequence_pairs.sample_pair()
            if pair_id in tested_pair_ids:
                duplicate_streak += 1
                if duplicate_streak >= duplicate_streak_limit:
                    stopped_reason = (
                        f"duplicate_streak_limit_reached={duplicate_streak_limit}"
                    )
                    _status(
                        "Duplicate streak limit reached. "
                        f"Stopping naive search. duplicate_streak_limit={duplicate_streak_limit}"
                    )
                    break
                continue
            tested_pair_ids.add(pair_id)
            duplicate_streak = 0

            seq, rc_seq = pair

            if total_nupack_budget is not None and total_nupack_calls >= total_nupack_budget:
                stopped_reason = "total_nupack_budget"
                _status("Total NUPACK budget reached before on-target evaluation.")
                break
            total_nupack_calls += 1
            on_result = compute_nupack_energy(seq, rc_seq, type="total")
            if not isinstance(on_result, tuple):
                continue

            on_energy, self_e_seq, self_e_rc = on_result
            if not (min_ontarget <= on_energy <= max_ontarget):
                continue
            if self_e_seq < self_energy_limit or self_e_rc < self_energy_limit:
                continue

            if total_nupack_budget is not None and total_nupack_calls >= total_nupack_budget:
                stopped_reason = "total_nupack_budget"
                _status("Total NUPACK budget reached before homodimer evaluation.")
                break
            total_nupack_calls += 1
            homo_seq = compute_nupack_energy(seq, seq, type="total")

            if total_nupack_budget is not None and total_nupack_calls >= total_nupack_budget:
                stopped_reason = "total_nupack_budget"
                _status("Total NUPACK budget reached during homodimer evaluation.")
                break
            total_nupack_calls += 1
            homo_rc = compute_nupack_energy(rc_seq, rc_seq, type="total")

            homo_seq_energy = homo_seq[0] if isinstance(homo_seq, tuple) else homo_seq
            homo_rc_energy = homo_rc[0] if isinstance(homo_rc, tuple) else homo_rc
            if homo_seq_energy < offtarget_limit or homo_rc_energy < offtarget_limit:
                continue

            passed_crossref, crossref_nupack_calls = crossreference_sequences(
                pair,
                selected_pairs,
                offtarget_limit,
                max_pair_violations=0,
            )
            total_nupack_calls += crossref_nupack_calls
            if not passed_crossref:
                continue

            selected_pairs.append(pair)
            selected_pair_ids.append(int(pair_id))
            progress_rows.append(
                {
                    "step": "accepted_pair",
                    "attempt": int(attempts),
                    "pairs_found": len(selected_pairs),
                    "nupack_calls_executed": int(total_nupack_calls),
                    "candidate_pair_id": int(pair_id),
                    "on_target_energy": float(on_energy),
                    "notes": None,
                }
            )
            elapsed_s = time.time() - start_t
            _status(
                f"Accepted {len(selected_pairs)} "
                f"(attempt {attempts}, on={on_energy:.2f}, "
                f"total NUPACK calls={total_nupack_calls}, "
                f"elapsed={elapsed_s:.1f}s)"
            )
    except KeyboardInterrupt:
        stopped_reason = "keyboard_interrupt"
        _status("Interrupted by user. Saving best result so far...")

    elapsed_s = time.time() - start_t
    progress_rows.append(
        {
            "step": "final_summary",
            "attempt": int(attempts),
            "pairs_found": len(selected_pairs),
            "nupack_calls_executed": int(total_nupack_calls),
            "candidate_pair_id": None,
            "on_target_energy": None,
            "notes": stopped_reason,
        }
    )
    _status(
        f"Naive search finished with {len(selected_pairs)} pairs after {attempts} attempts "
        f"and {total_nupack_calls} NUPACK calls "
        f"(elapsed={elapsed_s:.1f}s)."
    )

    if return_diagnostics:
        return {
            "final_pairs": selected_pairs,
            "final_pair_ids": selected_pair_ids,
            "generation_data": progress_rows,
            "total_nupack_calls": int(total_nupack_calls),
            "search_params": {
                "offtarget_limit": float(offtarget_limit),
                "max_ontarget": float(max_ontarget),
                "min_ontarget": float(min_ontarget),
                "self_energy_limit": float(self_energy_limit),
                "initial_fresh_pair_count": None,
                "generations": None,
                "allowed_violations_initial": 0,
                "fresh_pair_search_budget": None,
                "total_nupack_budget": None if total_nupack_budget is None else int(total_nupack_budget),
                "prune_fraction": None,
                "fresh_pair_scale": None,
                "vc_max_iterations": None,
                "duplicate_streak_limit": int(duplicate_streak_limit),
                "min_progress_interval_s": float(min_progress_interval_s),
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
            "attempts": int(attempts),
        }
    return selected_pairs
