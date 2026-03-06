#!/usr/bin/env python3
"""
naive_search.py

Purpose:
    Naive baseline that greedily builds an orthogonal set of sequence pairs by
    sampling one candidate at a time and only accepting it if it meets on-target,
    self-energy, and off-target (cross-reference) constraints.
"""

import random
import time
from seqwalk import design

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


def crossreference_sequences(
    new_pair,
    pool,
    offtarget_limit,
    max_pair_violations=0,
    Use_Library=None,
):
    """
    Checks all off-target interactions between a new sequence pair and the pool.

    The comparisons include:
      - new seq vs each pool seq
      - new seq vs each pool rc
      - new rc vs each pool seq
      - new rc vs each pool rc

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


if __name__ == "__main__":
    # 1) Reproducibility: fix the RNG
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)
    hf.set_nupack_params(material='dna', celsius=37, sodium=0.050, magnesium=0.025)
    # 2) Registry that generates candidate sequence pairs on demand
    #seqwalk_cores = design.max_size(20, 8, alphabet="ACGT")
    sequence_pairs_object = sc.SequencePairRegistry(
        length=10,
        fivep_ext="TTTT",
        threep_ext="",
        unwanted_substrings=[],
        apply_unwanted_to="core",
        seed=RANDOM_SEED,
        preselected_cores=None,
    )

    # 3) Energy thresholds (use values established during pilot analysis)
    max_ontarget = -12.5
    min_ontarget = -14.5
    offtarget_limit = -7.9
    self_energy_limit = -0.5

    # 4) Configure cache and NUPACK parameters
    hf.choose_precompute_library("naive_search.pkl")
    hf.USE_LIBRARY = False

    # 5) Naive greedy search parameters
    target_size = 1000
    max_attempts = 95000000
    progress_every = 250

    selected_pairs = []
    selected_ids = set()
    attempts = 0

    start_time = time.time()

    try:
        while len(selected_pairs) < target_size and attempts < max_attempts:
            attempts += 1

            if attempts % progress_every == 0:
                print(
                    f"Progress: {len(selected_pairs)}/{target_size} "
                    f"after {attempts} attempts"
                )

            pair_id, pair = sequence_pairs_object.sample_pair()
            if pair_id in selected_ids:
                continue

            seq, rc_seq = pair

            on_result = sc.nupack_compute_energy_precompute_library_fast(
                seq, rc_seq, type="total", Use_Library=hf.USE_LIBRARY
            )
            if not isinstance(on_result, tuple):
                continue

            on_energy, self_e_seq, self_e_rc = on_result

            if not (min_ontarget <= on_energy <= max_ontarget):
                continue
            if self_e_seq < self_energy_limit or self_e_rc < self_energy_limit:
                continue

            homo_seq = sc.nupack_compute_energy_precompute_library_fast(
                seq, seq, type="total", Use_Library=hf.USE_LIBRARY
            )
            homo_rc = sc.nupack_compute_energy_precompute_library_fast(
                rc_seq, rc_seq, type="total", Use_Library=hf.USE_LIBRARY
            )
            homo_seq_energy = homo_seq[0] if isinstance(homo_seq, tuple) else homo_seq
            homo_rc_energy = homo_rc[0] if isinstance(homo_rc, tuple) else homo_rc
            if homo_seq_energy < offtarget_limit or homo_rc_energy < offtarget_limit:
                continue

            if not crossreference_sequences(
                pair,
                selected_pairs,
                offtarget_limit,
                Use_Library=hf.USE_LIBRARY,
            ):
                continue

            selected_pairs.append(pair)
            selected_ids.add(pair_id)

            print(
                f"Accepted {len(selected_pairs)}/{target_size} "
                f"(attempt {attempts}, on={on_energy:.2f})"
            )
    except KeyboardInterrupt:
        print("\nInterrupted. Saving current noflank_results...")

    elapsed_s = time.time() - start_time
    print(
        f"Done. Selected {len(selected_pairs)} pairs in {attempts} attempts "
        f"({elapsed_s:.1f}s)."
    )

    hf.save_sequence_pairs_to_txt(selected_pairs, filename="naive_orthogonal_pairs.txt")

    if not selected_pairs:
        print("No sequences found; skipping energy plots.")
        raise SystemExit(0)

    hf.USE_LIBRARY = False
    on_e, self_e_a, self_e_b = sc.compute_ontarget_energies(selected_pairs)
    off_e = sc.compute_offtarget_energies(selected_pairs)

    sc.plot_on_off_target_histograms(
        on_e,
        off_e,
        output_path="naive_ortho_energies.pdf",
    )

    sc.plot_self_energy_histogram(
        [self_e_a, self_e_b],
        bins=30,
        output_path="naive_self_energies.pdf",
    )
