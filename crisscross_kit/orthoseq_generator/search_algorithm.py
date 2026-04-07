#!/usr/bin/env python3
"""
search_algorithm.py

Purpose:
    Hybrid search helpers for selecting sequence pairs with energy filters,
    optional cross-reference (off-target) checks, and iterative graph pruning.
"""

import random
import logging

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.vertex_cover_algorithms import (
    build_edges,
    iterative_vertex_cover_multi,
)

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())


def estimate_offtarget_nupack_calls(num_sequence_pairs):
    """
    Estimates the deterministic number of NUPACK computations performed by
    `compute_offtarget_energies` for `num_sequence_pairs` pairs.
    """
    return 2 * num_sequence_pairs * num_sequence_pairs


def hybrid_search(
    sequence_pairs,
    offtarget_limit,
    max_ontarget,
    min_ontarget,
    self_energy_limit,
    init_subsetsize=200,
    generations=100,
    allowed_violations=0,
    max_nupack_calls=50000,
    prune_fraction=0.2,
    history_subset_scale=1.0,
    vc_multistart=30,
    vc_population_size=1,
    vc_max_iterations=5000,
    stop_event=None,
):
    """
    Searches for a large orthogonal sequence set by alternating between
    constraint-aware subset selection and graph-based pruning.

    Procedure
    ---------
    1. Sample a subset of candidate sequence pairs whose on-target and
       self-energy values pass the requested thresholds.
    2. Cross-reference those candidates against the currently preserved history
       set, rejecting candidates with too many off-target violations.
    3. Re-add the preserved history pairs to the working subset so previously
       good sequences remain available to the graph step.
    4. Compute the off-target interaction graph on the working subset.
    5. Run the iterative vertex-cover heuristic and keep the corresponding
       independent set.
    6. If the independent set improves on the best-so-far solution, replace the
       preserved history with that new best set.
    7. Repeat for the requested number of generations or until interrupted.

    Notes
    -----
    - `history_ids` and `history_pool` represent the same preserved set in two
      forms: IDs for bookkeeping and `(seq, rc_seq)` pairs for cross-reference
      checks.
    - If subset selection stops early because the NUPACK-call budget is hit,
      `allowed_violations` is increased by one before the next generation.
    - `compute_offtarget_energies` is deterministic for a given subset, so its
      NUPACK workload is estimated analytically and added to the running total.

    :param sequence_pairs: Candidate sequence source. Can be a
                           `SequencePairRegistry`-like object with
                           `sample_pair()` / `get_pair_by_id()` methods or a
                           list of `(index, (seq, rc_seq))` tuples.
    :type sequence_pairs: object or list

    :param offtarget_limit: Energy threshold below which an off-target
                            interaction is considered incompatible.
    :type offtarget_limit: float

    :param max_ontarget: Upper bound for acceptable on-target energy.
    :type max_ontarget: float

    :param min_ontarget: Lower bound for acceptable on-target energy.
    :type min_ontarget: float

    :param self_energy_limit: Minimum acceptable self-energy for each strand.
    :type self_energy_limit: float

    :param init_subsetsize: Initial number of new candidate pairs to request
                            per generation before preserved history is re-added.
    :type init_subsetsize: int

    :param generations: Maximum number of search generations to run.
    :type generations: int

    :param allowed_violations: Initial number of violating history-pool pairs a
                               new candidate may tolerate during cross-reference.
    :type allowed_violations: int

    :param max_nupack_calls: Maximum number of direct NUPACK computations
                             allowed during each subset-selection step.
    :type max_nupack_calls: int or None

    :param prune_fraction: Fraction of vertices to remove before each
                           vertex-cover repair step.
    :type prune_fraction: float

    :param history_subset_scale: Multiplier used to derive the next generation's
                                 requested fresh subset size from the number of
                                 preserved history pairs. If history is non-empty,
                                 the next `subsetsize` becomes
                                 `int(len(history_ids) * history_subset_scale)`.
    :type history_subset_scale: float

    :param vc_multistart: Number of independent starts used by the iterative
                          vertex-cover heuristic.
    :type vc_multistart: int

    :param vc_population_size: Maximum number of equal-quality covers retained
                               inside each vertex-cover run.
    :type vc_population_size: int

    :param vc_max_iterations: Maximum number of refinement iterations inside
                              each vertex-cover run.
    :type vc_max_iterations: int

    :param stop_event: Optional external stop signal.
    :type stop_event: threading.Event or None

    :returns: Final list of `(seq, rc_seq)` pairs for the best independent set
              found during the search.
    :rtype: list[tuple[str, str]]
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

    history_ids = set()
    history_pool = []
    non_cover_vertices = set()
    current_allowed_violations = allowed_violations
    total_nupack_calls = 0
    subsetsize = init_subsetsize

    if not 0 <= prune_fraction <= 1:
        raise ValueError("prune_fraction must be between 0 and 1.")
    if history_subset_scale < 0:
        raise ValueError("history_subset_scale must be non-negative.")
    if vc_multistart < 1:
        raise ValueError("vc_multistart must be at least 1.")
    if vc_population_size < 1:
        raise ValueError("vc_population_size must be at least 1.")
    if vc_max_iterations < 1:
        raise ValueError("vc_max_iterations must be at least 1.")

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
        f"initial subset size: {init_subsetsize}, "
        f"generations: {generations}, "
        f"allowed violations: {allowed_violations}, "
        f"max NUPACK calls: {max_nupack_calls}, "
        f"prune fraction: {prune_fraction}, "
        f"history subset scale: {history_subset_scale}, "
        f"vc multistart: {vc_multistart}, "
        f"vc population size: {vc_population_size}, "
        f"vc max iterations: {vc_max_iterations}"
    )

    try:
        for i in range(generations):
            if stop_event is not None and stop_event.is_set():
                print("Stop event detected. Stopping search...")
                logger.info("Stop event detected. Stopping hybrid search.")
                break

            subset, indices, stopped_early, subset_nupack_calls = sc.select_subset_in_energy_range(
                sequence_pairs,
                energy_min=min_ontarget,
                energy_max=max_ontarget,
                self_energy_min=self_energy_limit,
                max_size=subsetsize,
                Use_Library=False,
                avoid_indices=history_ids,
                timeout_s=None,
                history_pool=history_pool,
                allowed_violations=current_allowed_violations,
                offtarget_limit=offtarget_limit,
                max_nupack_calls=max_nupack_calls,
            )
            total_nupack_calls += subset_nupack_calls
            if stopped_early:
                current_allowed_violations += 1
                print(
                    "Subset selection stopped early; "
                    f"increasing allowed violations to {current_allowed_violations}."
                )
                logger.info(
                    "Subset selection stopped early; increasing allowed "
                    f"violations to {current_allowed_violations}."
                )
            else:
                print(
                    f"Current max_pair_violations: {current_allowed_violations}"
                )
                logger.info(
                    f"Current max_pair_violations: {current_allowed_violations}"
                )

            # Re-add preserved sequences so they remain visible to the graph step.
            sorted_history = sorted(history_ids)
            if isinstance(sequence_pairs, list):
                extra_pairs = [sequence_pairs[idx][1] for idx in sorted_history]
            else:
                extra_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted_history]
            subset += extra_pairs
            indices += list(sorted_history)

            if not indices:
                msg = (
                    "No sequences found in the requested energy range "
                    "(NUPACK call limit hit or constraints too strict)."
                )
                print(msg)
                logger.warning(msg)
                break

            # Ensure no duplicate indices
            assert len(indices) == len(set(indices)), (
                f"Duplicate index found! "
                f"indices={indices} "
                f"set(indices)={sorted(set(indices))}"
            )

            # This step dominates cost, so we track its deterministic workload
            # analytically instead of instrumenting the core computation path.
            off_e_subset = sc.compute_offtarget_energies(subset)
            total_nupack_calls += estimate_offtarget_nupack_calls(len(subset))
            logger.info("Building incompatibility graph...")
            Edges = build_edges(off_e_subset, indices, offtarget_limit)

            print(
                f"Running iterative_vertex_cover_multi with "
                f"population_size={vc_population_size}"
            )
            logger.info(
                "Running vertex cover heuristic. "
                f"Trying {vc_multistart} independent starts."
            )
            removed_vertices, _trajectories = iterative_vertex_cover_multi(
                indices,
                Edges,
                avoid_V=history_ids,
                multistart=vc_multistart,
                population_size=vc_population_size,
                max_iterations=vc_max_iterations,
                num_vertices_to_remove=int(len(indices) * prune_fraction),
                show_progress=False,
            )

            Vertices = set(indices)
            new_non_cover_vertices = Vertices - removed_vertices

            # Preserve only the current best independent set; the matching
            # sequence pool is rebuilt so subset selection can cross-reference it.
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

            subsetsize = (
                int(len(history_ids) * history_subset_scale)
                if history_ids
                else subsetsize
            )

            print(
                f"Generation: {i + 1:2d} | "
                f"Current number of pairs: {len(new_non_cover_vertices):3d} | "
                f"Largest number of pairs: {len(non_cover_vertices):3d} | "
                f"Total NUPACK calls: {total_nupack_calls}"
            )
            logger.info(
                f"Generation: {i + 1:2d} | "
                f"Current number of pairs: {len(new_non_cover_vertices):3d} | "
                f"Largest number of pairs: {len(non_cover_vertices):3d} | "
                f"Total NUPACK calls: {total_nupack_calls}"
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving best result so far...")
        logger.info("Interrupted by user. Saving best result so far...")

    if isinstance(sequence_pairs, list):
        final_pairs = [sequence_pairs[idx][1] for idx in sorted(non_cover_vertices)]
    else:
        final_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted(non_cover_vertices)]

    print(f"Total NUPACK calls overall: {total_nupack_calls}")
    logger.info(f"Total NUPACK calls overall: {total_nupack_calls}")
    hf.save_sequence_pairs_to_txt(final_pairs)
    return final_pairs


if __name__ == "__main__":
    # Local entrypoint mirroring the packaged hybrid search flow.
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)
    hf.set_nupack_params(material='dna', celsius=37, sodium=0.05, magnesium=0.025)
    sequence_pairs_object = sc.SequencePairRegistry(
        length=7,
        fivep_ext="TTTT",
        threep_ext="",
        unwanted_substrings=[],
        apply_unwanted_to="core",
        seed=RANDOM_SEED,
        preselected_cores=None,
    )
    max_ontarget = -9.128
    min_ontarget = -10.38
    offtarget_limit = -7.2
    self_energy_limit = -2

    hf.choose_precompute_library("8mers101.pkl")
    hf.USE_LIBRARY = False

    orthogonal_seq_pairs = hybrid_search(
        sequence_pairs_object,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        self_energy_limit,
        init_subsetsize=200,
        generations=3000,
        allowed_violations=1,
        vc_multistart=10,
        vc_population_size=1,
        vc_max_iterations=5000,
        max_nupack_calls=8000,
    )


    hf.save_sequence_pairs_to_txt(orthogonal_seq_pairs, filename="ortho_test7mers.txt")

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
