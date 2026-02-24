#!/usr/bin/env python3
"""
prototyping.py

Purpose:
    Prototyping helpers for selecting sequence pairs with energy filters and
    optional cross-reference (off-target) checks.
"""

import random
import time
import numpy as np
from seqwalk import design

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.vertex_cover_algorithms import (
    build_edges,
    iterative_vertex_cover_multi,
)


def crossreference_sequences(
    new_pair,
    pool,
    offtarget_limit,
    max_pair_violations=0,
    Use_Library=None,
):
    """
    Checks off-target interactions between a new sequence pair and a pool.

    Counts violations per pool pair (not per sequence interaction). Returns
    False if violations exceed max_pair_violations.
    """
    if Use_Library is None:
        Use_Library = hf.USE_LIBRARY

    if not pool:
        return True

    seq, rc_seq = new_pair
    violations = 0

    for pool_seq, pool_rc in pool:
        violated = False
        for a in (seq, rc_seq):
            for b in (pool_seq, pool_rc):
                result = sc.nupack_compute_energy_precompute_library_fast(
                    a, b, type="total", Use_Library=Use_Library
                )
                energy = result[0] if isinstance(result, tuple) else result
                if energy < offtarget_limit:
                    violated = True
                    break
            if violated:
                break

        if violated:
            violations += 1
            if violations > max_pair_violations:
                return False

    return True


def select_subset_in_energy_range_with_crossref(
    sequence_pairs,
    history_pool,
    allowed_violations=0,
    offtarget_limit=None,
    energy_min=-np.inf,
    energy_max=np.inf,
    self_energy_min=-np.inf,
    max_size=np.inf,
    Use_Library=None,
    avoid_indices=None,
    timeout_s=600,
    progress_every=100,
):
    """
    Selects a random subset of sequence pairs whose on-target energies fall
    within a given range, with optional cross-reference checks against a
    history pool.

    Notes
    -----
    - Uses random sampling without full shuffling.
    - Stops when max_size is reached, candidates are exhausted, or timeout occurs.
    - Keeps returned sequence order aligned with returned indices list.
    - If offtarget_limit is None, cross-referencing is skipped.
    """

    if Use_Library is None:
        Use_Library = hf.USE_LIBRARY

    if avoid_indices is None:
        avoid_indices = set()

    if history_pool is None:
        history_pool = []

    subset = []
    indices = []
    tested_indices = set(avoid_indices)
    attempts = 0
    successes = 0

    start_t = time.time()

    if not hasattr(sequence_pairs, "sample_pair"):
        raise TypeError(
            "sequence_pairs must be an object with a sample_pair() method."
        )

    while len(indices) < max_size:
        if timeout_s is not None and (time.time() - start_t) >= timeout_s:
            print(
                f"Only {len(subset)} of requested {max_size} found (timeout)."
            )
            success_rate = (successes / attempts) if attempts else 0.0
            return subset, indices, success_rate, True

        pair_id, (seq, rc_seq) = sequence_pairs.sample_pair()

        if pair_id in tested_indices:
            continue

        tested_indices.add(pair_id)
        attempts += 1
        if progress_every and attempts % progress_every == 0:
            print(
                f"Progress: {len(subset)}/{max_size} "
                f"accepted after {attempts} attempts"
            )

        energy, self_e_seq, self_e_rc_seq = sc.nupack_compute_energy_precompute_library_fast(
            seq,
            rc_seq,
            type="total",
            Use_Library=Use_Library,
        )

        if not (
            energy_min <= energy <= energy_max
            and self_e_seq >= self_energy_min
            and self_e_rc_seq >= self_energy_min
        ):
            continue

        if offtarget_limit is not None:
            if not crossreference_sequences(
                (seq, rc_seq),
                history_pool,
                offtarget_limit,
                max_pair_violations=allowed_violations,
                Use_Library=Use_Library,
            ):
                continue

        subset.append((seq, rc_seq))
        indices.append(pair_id)
        successes += 1

    print(
        f"Selected {len(subset)} sequence pairs with energies in range "
        f"[{energy_min}, {energy_max}] and self energy above {self_energy_min}"
    )
    success_rate = (successes / attempts) if attempts else 0.0
    return subset, indices, success_rate, False


def evolutionary_vertex_cover_prototype(
    sequence_pairs,
    offtarget_limit,
    max_ontarget,
    min_ontarget,
    self_energy_limit,
    subsetsize=200,
    generations=100,
    allowed_violations=0,
    stop_event=None,
):
    """
    Prototype variant of evolutionary_vertex_cover that uses per-pair cross-referencing
    during subset selection. History is only updated when a strictly better solution
    is found; near-best updates are intentionally omitted.
    """
    history_ids = set()
    history_pool = []
    non_cover_vertices = set()
    current_allowed_violations = allowed_violations

    try:
        for i in range(generations):
            if stop_event is not None and stop_event.is_set():
                print("Stop event detected. Stopping search...")
                break

            subset, indices, _, timed_out = select_subset_in_energy_range_with_crossref(
                sequence_pairs,
                history_pool=history_pool,
                allowed_violations=current_allowed_violations,
                offtarget_limit=offtarget_limit,
                energy_min=min_ontarget,
                energy_max=max_ontarget,
                self_energy_min=self_energy_limit,
                max_size=subsetsize,
                Use_Library=False,
                avoid_indices=history_ids,
            )
            if timed_out:
                current_allowed_violations += 1
                print(
                    "Timeout hit during subset selection; "
                    f"increasing allowed violations to {current_allowed_violations}."
                )
            else:
                print(
                    f"Current max_pair_violations: {current_allowed_violations}"
                )

            # Re-add preserved sequences so they remain in the candidate pool
            sorted_history = sorted(history_ids)
            if isinstance(sequence_pairs, list):
                extra_pairs = [sequence_pairs[idx][1] for idx in sorted_history]
            else:
                extra_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted_history]
            subset += extra_pairs
            indices += list(sorted_history)

            if not indices:
                msg = "No sequences found in the requested energy range (timeout or constraints too strict)."
                print(msg)
                break

            # Ensure no duplicate indices
            assert len(indices) == len(set(indices)), (
                f"Duplicate index found! "
                f"indices={indices} "
                f"set(indices)={sorted(set(indices))}"
            )

            off_e_subset = sc.compute_offtarget_energies(subset)
            Edges = build_edges(off_e_subset, indices, offtarget_limit)

            multistart = 30
            removed_vertices = iterative_vertex_cover_multi(
                indices,
                Edges,
                avoid_V=history_ids,
                multistart=multistart,
                num_vertices_to_remove=len(indices) // 5,
            )

            Vertices = set(indices)
            new_non_cover_vertices = Vertices - removed_vertices

            if len(new_non_cover_vertices) >= len(non_cover_vertices):
                if len(new_non_cover_vertices) > len(non_cover_vertices):
                    history_ids.clear()
                    history_pool = []
                non_cover_vertices = new_non_cover_vertices

                history_ids = set(non_cover_vertices)
                if isinstance(sequence_pairs, list):
                    history_pool = [sequence_pairs[idx][1] for idx in sorted(history_ids)]
                else:
                    history_pool = [sequence_pairs.get_pair_by_id(idx) for idx in sorted(history_ids)]

            subsetsize = int(len(history_ids) * 1.0) if history_ids else subsetsize

            print(
                f"Generation: {i + 1:2d} | "
                f"Current number of pairs: {len(new_non_cover_vertices):3d} | "
                f"Largest number of pairs: {len(non_cover_vertices):3d} | "
                f"Carry over pairs: {len(history_ids):3d}"
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving best result so far...")

    if isinstance(sequence_pairs, list):
        final_pairs = [sequence_pairs[idx][1] for idx in sorted(non_cover_vertices)]
    else:
        final_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted(non_cover_vertices)]

    hf.save_sequence_pairs_to_txt(final_pairs)
    return final_pairs


if __name__ == "__main__":
    # Prototype entrypoint mirroring run_sequence_search.py
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)
    hf.set_nupack_params(material='dna', celsius=37, sodium=0.05, magnesium=0.025)
    seqwalk_cores = design.max_size(10, 5, alphabet="ACGT", RCfree=True)
    sequence_pairs_object = sc.SequencePairRegistry(
        length=10,
        fivep_ext="",
        threep_ext="",
        unwanted_substrings=[],
        apply_unwanted_to="core",
        seed=RANDOM_SEED,
        preselected_cores=seqwalk_cores,
    )
    max_ontarget = -23
    min_ontarget = -25
    offtarget_limit = -8.0
    self_energy_limit = -1.25

    hf.choose_precompute_library("8mers101.pkl")
    hf.USE_LIBRARY = False

    orthogonal_seq_pairs = evolutionary_vertex_cover_prototype(
        sequence_pairs_object,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        self_energy_limit,
        subsetsize=80,
        generations=1500,
        allowed_violations=1,
    )

    hf.save_sequence_pairs_to_txt(orthogonal_seq_pairs, filename="ortho_10mers7.txt")

    hf.USE_LIBRARY = False
    onef, self_e_A, self_e_B = sc.compute_ontarget_energies(orthogonal_seq_pairs)
    offef = sc.compute_offtarget_energies(orthogonal_seq_pairs)

    sc.plot_on_off_target_histograms(
        onef,
        offef,
        output_path="ortho_10mers.pdf",
    )

    sc.plot_self_energy_histogram(
        [self_e_A, self_e_B],
        bins=30,
        output_path="final_10mer_self_energies.pdf",
    )
