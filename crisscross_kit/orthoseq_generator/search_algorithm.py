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
    iterative_vertex_cover_refinement,
)

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())


def _status(message):
    print(message, flush=True)
    logger.info(message)


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
    initial_fresh_pair_count=200,
    generations=100,
    allowed_violations=0,
    max_nupack_calls=50000,
    prune_fraction=0.2,
    fresh_pair_scale=1.0,
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
    - `retained_pair_ids` and `retained_pairs` represent the same carried-forward
      best set in two forms: IDs for bookkeeping and `(seq, rc_seq)` pairs for
      cross-reference checks.
    - `max_ontarget` and `min_ontarget` bound the accepted on-target energy
      window for new candidates. A candidate is accepted only if
      `min_ontarget <= on_target_energy <= max_ontarget`.
    - `self_energy_limit` is a lower bound on acceptable self-structure
      energies for both strands in a pair.
    - `max_nupack_calls` is a per-generation budget for direct NUPACK
      computations made inside `select_subset_in_energy_range` while sampling
      and screening new candidates. It does not terminate the whole hybrid
      search, and it does not cap the later full-subset
      `compute_offtarget_energies` call.
    - If subset selection stops early because this per-generation sampling
      budget is hit, `allowed_violations` is increased by one before the next
      generation so later sampling becomes less strict.
    - `compute_offtarget_energies` is deterministic for a given subset, so its
      NUPACK workload is estimated analytically and added to the running total
      for reporting only.

    :param sequence_pairs: Candidate sequence source. Can be a
                           `SequencePairRegistry`-like object with
                           `sample_pair()` / `get_pair_by_id()` methods or a
                           list of `(index, (seq, rc_seq))` tuples.
    :type sequence_pairs: object or list

    :param offtarget_limit: Energy threshold below which an off-target
                            interaction is considered incompatible, both during
                            history cross-reference checks and when building the
                            incompatibility graph for the vertex-cover step.
    :type offtarget_limit: float

    :param max_ontarget: Upper bound for acceptable on-target energy.
    :type max_ontarget: float

    :param min_ontarget: Lower bound for acceptable on-target energy.
    :type min_ontarget: float

    :param self_energy_limit: Minimum acceptable self-energy for each strand.
    :type self_energy_limit: float

    :param initial_fresh_pair_count: Initial target number of fresh candidate
                                     pairs to collect in each generation before
                                     retained pairs are re-added.
    :type initial_fresh_pair_count: int

    :param generations: Maximum number of search generations to run.
    :type generations: int

    :param allowed_violations: Initial number of history-pool conflicts a new
                               candidate may tolerate during cross-reference.
                               This value can increase across generations if
                               subset selection repeatedly hits the sampling
                               NUPACK budget.
    :type allowed_violations: int

    :param max_nupack_calls: Maximum number of direct NUPACK computations
                             allowed during each generation's subset-selection
                             step. Hitting this limit stops candidate sampling
                             for that generation only.
    :type max_nupack_calls: int or None

    :param prune_fraction: Fraction of the current vertex cover to remove
                           before each repair iteration in the graph heuristic.
    :type prune_fraction: float

    :param fresh_pair_scale: Multiplier used to derive the next generation's
                             fresh-pair target from the number of retained best
                             pairs. If retained pairs are available, the next
                             target becomes
                             `int(len(retained_pair_ids) * fresh_pair_scale)`.
    :type fresh_pair_scale: float

    :param vc_max_iterations: Maximum number of repair/refinement iterations
                              inside the vertex-cover heuristic for one
                              generation.
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

    retained_pair_ids = set()
    retained_pairs = []
    non_cover_vertices = set()
    current_allowed_violations = allowed_violations
    total_nupack_calls = 0
    target_fresh_pair_count = initial_fresh_pair_count

    if not 0 <= prune_fraction <= 1:
        raise ValueError("prune_fraction must be between 0 and 1.")
    if fresh_pair_scale < 0:
        raise ValueError("fresh_pair_scale must be non-negative.")
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
        f"initial fresh pair count: {initial_fresh_pair_count}, "
        f"generations: {generations}, "
        f"allowed violations: {allowed_violations}, "
        f"max NUPACK calls: {max_nupack_calls}, "
        f"prune fraction: {prune_fraction}, "
        f"fresh pair scale: {fresh_pair_scale}, "
        f"vc max iterations: {vc_max_iterations}"
    )

    try:
        for i in range(generations):
            if stop_event is not None and stop_event.is_set():
                _status("Stop event detected. Stopping hybrid search.")
                break

            _status(
                f"Generation {i + 1}: selecting candidate subset "
                f"(target fresh pairs: {target_fresh_pair_count})..."
            )

            subset, indices, stopped_early, subset_nupack_calls = sc.select_subset_in_energy_range(
                sequence_pairs,
                energy_min=min_ontarget,
                energy_max=max_ontarget,
                self_energy_min=self_energy_limit,
                max_size=target_fresh_pair_count,
                avoid_indices=retained_pair_ids,
                timeout_s=None,
                retained_pairs=retained_pairs,
                allowed_violations=current_allowed_violations,
                offtarget_limit=offtarget_limit,
                max_nupack_calls=max_nupack_calls,
            )
            total_nupack_calls += subset_nupack_calls
            if stopped_early:
                current_allowed_violations += 1
                _status(
                    "Subset selection stopped early; "
                    f"increasing allowed violations to {current_allowed_violations}."
                )
            else:
                _status(
                    f"Generation {i + 1}: sampled {len(indices)} fresh pairs "
                    f"using {subset_nupack_calls} direct NUPACK calls. "
                    f"Current max_pair_violations: {current_allowed_violations}"
                )

            # Re-add preserved sequences so they remain visible to the graph step.
            sorted_retained_pair_ids = sorted(retained_pair_ids)
            if isinstance(sequence_pairs, list):
                extra_pairs = [sequence_pairs[idx][1] for idx in sorted_retained_pair_ids]
            else:
                extra_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted_retained_pair_ids]
            subset += extra_pairs
            indices += list(sorted_retained_pair_ids)

            if not indices:
                msg = (
                    "No sequences found in the requested energy range "
                    "(NUPACK call limit hit or constraints too strict)."
                )
                _status(msg)
                break

            # Ensure no duplicate indices
            assert len(indices) == len(set(indices)), (
                f"Duplicate index found! "
                f"indices={indices} "
                f"set(indices)={sorted(set(indices))}"
            )

            # This step dominates cost, so we track its deterministic workload
            # analytically instead of instrumenting the core computation path.
            _status(
                f"Generation {i + 1}: computing full off-target matrix for "
                f"{len(subset)} pairs..."
            )
            off_e_subset = sc.compute_offtarget_energies(subset)
            total_nupack_calls += estimate_offtarget_nupack_calls(len(subset))
            _status(f"Generation {i + 1}: building incompatibility graph...")
            Edges = build_edges(off_e_subset, indices, offtarget_limit)

            _status(
                f"Generation {i + 1}: refining graph solution "
                f"(max iterations: {vc_max_iterations})..."
            )
            removed_vertices, _trajectories = iterative_vertex_cover_refinement(
                indices,
                Edges,
                avoid_V=retained_pair_ids,
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
                    retained_pair_ids.clear()
                    retained_pairs = []
                non_cover_vertices = new_non_cover_vertices

                retained_pair_ids = set(non_cover_vertices)
                if isinstance(sequence_pairs, list):
                    retained_pairs = [sequence_pairs[idx][1] for idx in sorted(retained_pair_ids)]
                else:
                    retained_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted(retained_pair_ids)]

            target_fresh_pair_count = (
                int(len(retained_pair_ids) * fresh_pair_scale)
                if retained_pair_ids
                else target_fresh_pair_count
            )

            _status(
                f"Generation: {i + 1:2d} | "
                f"Current number of pairs: {len(new_non_cover_vertices):3d} | "
                f"Largest number of pairs: {len(non_cover_vertices):3d} | "
                f"Total NUPACK calls: {total_nupack_calls}"
            )

    except KeyboardInterrupt:
        _status("Interrupted by user. Saving best result so far...")

    if isinstance(sequence_pairs, list):
        final_pairs = [sequence_pairs[idx][1] for idx in sorted(non_cover_vertices)]
    else:
        final_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted(non_cover_vertices)]

    _status(f"Total NUPACK calls overall: {total_nupack_calls}")
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

    orthogonal_seq_pairs = hybrid_search(
        sequence_pairs_object,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        self_energy_limit,
        initial_fresh_pair_count=200,
        generations=3000,
        allowed_violations=1,
        vc_max_iterations=5000,
        max_nupack_calls=8000,
    )


    hf.save_sequence_pairs_to_txt(orthogonal_seq_pairs, filename="ortho_test7mers.txt")

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
