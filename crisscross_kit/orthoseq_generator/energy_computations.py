import os
import multiprocessing as mp
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from tqdm import tqdm

from orthoseq_generator import helper_functions as hf

import logging

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())

def estimate_offtarget_nupack_calls(num_sequence_pairs):
    """
    Estimate the direct NUPACK calls required for a full pairwise off-target matrix.

    This helper is shared between the hybrid search accounting layer and the
    subset-selection budget guard. It intentionally counts only the search-time
    matrix evaluations, not any reporting or verification recomputation.
    """
    return 2 * int(num_sequence_pairs) * int(num_sequence_pairs)


def _parse_slurm_cpus(value):
    if not value:
        return None
    try:
        first = value.split(",")[0]
        first = first.split("(")[0]
        return int(first)
    except ValueError:
        return None


def slurm_cpus(default=1):
    for key in ("SLURM_CPUS_PER_TASK", "SLURM_JOB_CPUS_PER_NODE", "SLURM_CPUS_ON_NODE"):
        parsed = _parse_slurm_cpus(os.environ.get(key))
        if parsed:
            return max(1, parsed)
    return max(1, default)


def _max_workers(fraction=0.75):
    total = slurm_cpus(default=os.cpu_count() or 1)
    return max(1, total - 1)


def _mp_context_from_env():
    method = os.environ.get("ORTHOSEQ_MP_START", "").strip().lower()
    if not method:
        return None
    return mp.get_context(method)


def compute_nupack_energy(seq1, seq2, type="total"):
    """
    Computes the Gibbs free energy of hybridization between two DNA sequences
    using NUPACK.
    """
    from nupack import Complex, Model, Strand, complex_analysis

    A = Strand(seq1, name="H1")
    B = Strand(seq2, name="H2")

    try:
        if seq1 == seq2:
            complex_obj = Complex([A, A], name="(H1+H1)")
            mono_obj_A = Complex([A], name="(H1)")
            homo = True
        else:
            complex_obj = Complex([A, B], name="(H1+H2)")
            mono_obj_A = Complex([A], name="(H1)")
            mono_obj_B = Complex([B], name="(H2)")
            homo = False

        model1 = Model(
            material=hf.NUPACK_PARAMS["MATERIAL"],
            celsius=hf.NUPACK_PARAMS["CELSIUS"],
            sodium=hf.NUPACK_PARAMS["SODIUM"],
            magnesium=hf.NUPACK_PARAMS["MAGNESIUM"],
        )

        if type == "minimum":
            results = complex_analysis([complex_obj], model=model1, compute=["mfe"])
            mfe_list = results[complex_obj].mfe
            if len(mfe_list) == 0:
                return -1.0
            energy = mfe_list[0].energy
            G_A = 0
            G_B = 0
        elif type == "total":
            if homo:
                results = complex_analysis([complex_obj, mono_obj_A], model=model1, compute=["pfunc"])
                G_AB = results[complex_obj].free_energy
                G_A = results[mono_obj_A].free_energy
                G_B = G_A
                energy = G_AB - 2.0 * G_A
            else:
                results = complex_analysis(
                    [complex_obj, mono_obj_A, mono_obj_B],
                    model=model1,
                    compute=["pfunc"],
                )
                G_AB = results[complex_obj].free_energy
                G_A = results[mono_obj_A].free_energy
                G_B = results[mono_obj_B].free_energy
                energy = G_AB - G_A - G_B

            if energy > -1:
                energy = -1.0
        elif type == "totalu":
            if homo:
                results = complex_analysis([complex_obj, mono_obj_A], model=model1, compute=["pfunc"])
                G_AB = results[complex_obj].free_energy
                G_A = results[mono_obj_A].free_energy
                G_B = G_A
                energy = G_AB
            else:
                results = complex_analysis(
                    [complex_obj, mono_obj_A, mono_obj_B],
                    model=model1,
                    compute=["pfunc"],
                )
                G_AB = results[complex_obj].free_energy
                G_A = results[mono_obj_A].free_energy
                G_B = results[mono_obj_B].free_energy
                energy = G_AB

            if energy > -1:
                energy = -1.0
        else:
            raise ValueError('type must be either "minimum", "total", or "totalu"')

        return energy, G_A, G_B
    except Exception as exc:
        print(f"The following error occurred: {exc}")
        print(seq1, seq2)
        return -1.0


def _init_worker(energy_type, nupack_params):
    hf.NUPACK_PARAMS = nupack_params
    hf.ENERGY_TYPE = energy_type


def compute_pair_energy_on(i, seq, rc_seq):
    pair_e, self_e1, self_e2 = compute_nupack_energy(seq, rc_seq, type=hf.ENERGY_TYPE)
    return i, pair_e, self_e1, self_e2


def compute_ontarget_energies(sequence_list):
    energies = np.zeros(len(sequence_list))
    self_energies_seq = np.zeros(len(sequence_list))
    self_energies_rc_seq = np.zeros(len(sequence_list))

    print(f"Computing on-target energies for {len(sequence_list)} sequences...")
    logger.info(f"Computing on-target energies for {len(sequence_list)} sequences.")

    max_workers = _max_workers()
    print(f"Calculating with {max_workers} cores...")

    pool_args = (hf.ENERGY_TYPE, hf.NUPACK_PARAMS)
    if os.environ.get("ORTHOSEQ_NO_MP", "").strip().lower() in ("1", "true", "yes"):
        for i, (seq, rc_seq) in tqdm(enumerate(sequence_list), total=len(sequence_list)):
            _, energy, self_e_seq, self_e_rc_seq = compute_pair_energy_on(i, seq, rc_seq)
            energies[i] = energy
            self_energies_seq[i] = self_e_seq
            self_energies_rc_seq[i] = self_e_rc_seq
    else:
        mp_ctx = _mp_context_from_env()
        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_worker,
            initargs=pool_args,
            mp_context=mp_ctx,
        ) as executor:
            futures = []
            for i, (seq, rc_seq) in enumerate(sequence_list):
                futures.append(executor.submit(compute_pair_energy_on, i, seq, rc_seq))

            for future in tqdm(as_completed(futures), total=len(futures)):
                i, energy, self_e_seq, self_e_rc_seq = future.result()
                energies[i] = energy
                self_energies_seq[i] = self_e_seq
                self_energies_rc_seq[i] = self_e_rc_seq

    return energies, self_energies_seq, self_energies_rc_seq


def compute_pair_energy_off(i, j, seq1, seq2):
    bind_energy, _, _ = compute_nupack_energy(seq1, seq2, type=hf.ENERGY_TYPE)
    return i, j, bind_energy


def compute_offtarget_energies(sequence_pairs):
    handles = [seq for seq, rc_seq in sequence_pairs]
    antihandles = [rc_seq for seq, rc_seq in sequence_pairs]

    handle_handle_energies = np.zeros((len(handles), len(handles)))
    antihandle_antihandle_energies = np.zeros((len(antihandles), len(antihandles)))
    handle_antihandle_energies = np.zeros((len(handles), len(antihandles)))

    def parallel_energy_computation(seqs1, seqs2, energy_matrix, condition):
        max_workers = _max_workers()
        print(f"Calculating with {max_workers} cores...")
        pool_args = (hf.ENERGY_TYPE, hf.NUPACK_PARAMS)

        if os.environ.get("ORTHOSEQ_NO_MP", "").strip().lower() in ("1", "true", "yes"):
            for i, seq1 in enumerate(seqs1):
                for j, seq2 in enumerate(seqs2):
                    if condition(i, j):
                        _, _, energy = compute_pair_energy_off(i, j, seq1, seq2)
                        energy_matrix[i, j] = energy
        else:
            mp_ctx = _mp_context_from_env()
            with ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=_init_worker,
                initargs=pool_args,
                mp_context=mp_ctx,
            ) as executor:
                futures = []
                for i, seq1 in enumerate(seqs1):
                    for j, seq2 in enumerate(seqs2):
                        if condition(i, j):
                            futures.append(executor.submit(compute_pair_energy_off, i, j, seq1, seq2))

                for future in tqdm(as_completed(futures), total=len(futures)):
                    i, j, energy = future.result()
                    energy_matrix[i, j] = energy

    print("Computing off-target energies for plus-plus interactions")
    computations = int(len(handles) * (len(handles) + 1) / 2)
    logger.info(f"Computing off-target energies for {computations} plus-plus interactions")
    parallel_energy_computation(handles, handles, handle_handle_energies, lambda i, j: j <= i)

    print("Computing off-target energies for minus-minus interactions")
    computations = int(len(antihandles) * (len(antihandles) + 1) / 2)
    logger.info(f"Computing off-target energies for {computations} minus-minus interactions")
    parallel_energy_computation(
        antihandles,
        antihandles,
        antihandle_antihandle_energies,
        lambda i, j: j <= i,
    )

    print("Computing off-target energies for plus-minus interactions")
    computations = len(handles) * len(antihandles) - len(handles)
    logger.info(f"Computing off-target energies for {computations} plus-minus interactions")
    parallel_energy_computation(handles, antihandles, handle_antihandle_energies, lambda i, j: j != i)

    return {
        "handle_handle_energies": handle_handle_energies,
        "antihandle_handle_energies": handle_antihandle_energies,
        "antihandle_antihandle_energies": antihandle_antihandle_energies,
    }


def crossreference_sequences(new_pair, pool, offtarget_limit, max_pair_violations=0):
    """
    Check whether a candidate pair is compatible with all pairs in a pool.

    Purpose
    -------
    During pass 2 of the hybrid search, each fresh candidate must be
    cross-referenced against the retained set before acceptance. This function
    checks all four strand combinations (handle-handle, handle-antihandle,
    antihandle-handle, antihandle-antihandle) between the candidate and every
    pool member. If any interaction energy falls below `offtarget_limit`, that
    pool member counts as a violation.

    The check short-circuits: it returns False as soon as violations exceed
    `max_pair_violations`, avoiding unnecessary NUPACK calls for candidates
    that clearly conflict with the retained set.

    :param new_pair: Candidate pair as (seq, rc_seq).
    :type new_pair: tuple[str, str]
    :param pool: Retained pairs to check against, each as (seq, rc_seq).
    :type pool: list[tuple[str, str]]
    :param offtarget_limit: Energy threshold below which an interaction is a
        conflict.
    :type offtarget_limit: float
    :param max_pair_violations: Maximum number of pool members the candidate
        may conflict with before rejection. Zero means any single conflict
        causes rejection.
    :type max_pair_violations: int
    :returns: (passed, nupack_calls) — whether the candidate is compatible and
        how many NUPACK calls were consumed.
    :rtype: tuple[bool, int]
    """
    if not pool:
        return True, 0

    seq, rc_seq = new_pair
    violations = 0
    nupack_calls = 0

    for pool_seq, pool_rc in pool:
        violated = False
        for a in (seq, rc_seq):
            for b in (pool_seq, pool_rc):
                nupack_calls += 1
                result = compute_nupack_energy(a, b, type=hf.ENERGY_TYPE)
                energy = result[0] if isinstance(result, tuple) else result
                if energy < offtarget_limit:
                    violated = True
                    break
            if violated:
                break

        if violated:
            violations += 1
            if violations > max_pair_violations:
                return False, nupack_calls

    return True, nupack_calls


def select_subset_in_energy_range(
    sequence_pairs,
    energy_min=-np.inf,
    energy_max=np.inf,
    self_energy_min=-np.inf,
    max_size=np.inf,
    avoid_indices=None,
    timeout_s=None,
    retained_pairs=None,
    allowed_violations=0,
    offtarget_limit=None,
    fresh_pair_search_budget=None,
    progress_every=None,
    progress_interval_s=120.0,
    stop_event=None,
    checkpoint_event=None,
    quiet_timeout=False,
    prior_state=None,
):
    """
    Sample sequence pairs that pass energy filters and optional cross-referencing.

    Purpose
    -------
    Candidate collection workhorse for both passes of `hybrid_search`. Draws
    random pairs from the source (finite list or infinite
    `SequencePairRegistry`), evaluates on-target energy and self-energy,
    optionally rejects candidates with strong same-strand homodimer binding,
    optionally cross-references against a retained pool, and accumulates
    accepted pairs until a stop condition fires.

    Supports hot-start via `prior_state`: pass the state dict from a previous
    call to resume collection where it left off (same tested set, counters,
    and accumulated pairs). Used by `hybrid_search` to support manual
    checkpoint peeks during pass 2 without losing collection state.

    For live registry-backed sampling, the function also applies an internal
    duplicate-streak exhaustion heuristic. If the sampler returns 1,000,000
    already-tested IDs in a row, collection stops and reports effective pool
    exhaustion.

    The budget check accounts for the downstream vertex cover cost using
    `estimate_offtarget_nupack_calls(len(subset))` as the reserved future
    matrix-evaluation cost.

    Stop conditions (returned as `stop_reason` string):
    - "nupack_limit" — `fresh_pair_search_budget` reached (incl. VC reserve)
    - "timeout" — `timeout_s` wall-clock seconds elapsed
    - "duplicate_streak_limit_reached=<N>" — sampler recycled seen IDs for
      `N` consecutive draws
    - "stop_event" — external threading.Event set
    - "checkpoint_request" — external checkpoint threading.Event set
    - "keyboard_interrupt" — KeyboardInterrupt caught
    - None — normal completion (`max_size` reached or pool exhausted)

    :param sequence_pairs: Source of candidate pairs. Accepts either a finite
        list of `(index, (seq, rc_seq))` tuples or a live object with a
        `sample_pair()` method.
    :type sequence_pairs: list or SequencePairRegistry

    :param energy_min: Lower bound for acceptable on-target energy.
    :type energy_min: float

    :param energy_max: Upper bound for acceptable on-target energy.
    :type energy_max: float

    :param self_energy_min: Minimum acceptable self-energy for both strands.
    :type self_energy_min: float

    :param max_size: Maximum number of pairs to collect.
    :type max_size: int or float

    :param avoid_indices: Set of pair IDs to skip. Ignored when `prior_state`
        is provided (the state already contains the full tested set).
    :type avoid_indices: set or None

    :param timeout_s: Wall-clock timeout in seconds. None disables.
    :type timeout_s: float or None

    :param retained_pairs: Pool of retained pairs for cross-referencing. When
        provided together with `offtarget_limit`, each candidate is checked
        against this pool before acceptance.
    :type retained_pairs: list[tuple[str, str]] or None

    :param allowed_violations: Maximum number of pool conflicts tolerated per
        candidate during cross-referencing.
    :type allowed_violations: int

    :param offtarget_limit: Energy threshold for off-target conflicts. When
        provided, it is used both for same-strand homodimer rejection and for
        cross-reference conflicts against `retained_pairs`.
    :type offtarget_limit: float or None

    :param fresh_pair_search_budget: Total NUPACK call budget for this
        collection pass (including estimated final VC cost). None disables.
    :type fresh_pair_search_budget: int or None

    :param progress_every: Print progress every N attempts.
    :type progress_every: int or None

    :param progress_interval_s: Minimum wall-clock interval between progress
        prints (default 120 s).
    :type progress_interval_s: float

    :param stop_event: External stop signal (threading.Event).
    :type stop_event: threading.Event or None

    :param checkpoint_event: External checkpoint signal (threading.Event).
        When set, collection returns its current state so the caller can run a
        diagnostic peek and then resume from the returned `prior_state`.
    :type checkpoint_event: threading.Event or None

    :param quiet_timeout: Suppress verbose timeout message.
    :type quiet_timeout: bool

    :param prior_state: State dict from a previous call to resume from.
        Contains subset, indices, tested_indices, attempts, nupack_calls,
        passed_ontarget_and_self, and duplicate-streak bookkeeping.
    :type prior_state: dict or None

    :returns: (subset, indices, stop_reason, nupack_calls, state)
        stop_reason is None for normal completion, or one of:
        "timeout", "nupack_limit", "duplicate_streak_limit_reached=<N>",
        "stop_event", "checkpoint_request", "keyboard_interrupt".
        state is a dict suitable for passing back as `prior_state`.
    :rtype: tuple[list, list, str|None, int, dict]
    """
    if retained_pairs is None:
        retained_pairs = []
    duplicate_streak_limit = 1_000_000

    if prior_state is not None:
        subset = list(prior_state["subset"])
        indices = list(prior_state["indices"])
        tested_indices = prior_state["tested_indices"]
        attempts = prior_state["attempts"]
        nupack_calls = prior_state["nupack_calls"]
        passed_energy_filter = prior_state["passed_ontarget_and_self"]
        passed_homodimer = prior_state.get("passed_homodimer", 0)
        duplicate_streak = prior_state.get("duplicate_streak", 0)
    else:
        if avoid_indices is None:
            avoid_indices = set()
        subset = []
        indices = []
        tested_indices = set(avoid_indices)
        attempts = 0
        nupack_calls = 0
        passed_energy_filter = 0
        passed_homodimer = 0
        duplicate_streak = 0

    start_t = time.time()
    last_progress_t = start_t

    def _build_state():
        return {
            "attempts": attempts,
            "passed_ontarget_and_self": passed_energy_filter,
            "passed_homodimer": passed_homodimer,
            "accepted_into_pool": len(subset),
            "tested_indices": tested_indices,
            "duplicate_streak": duplicate_streak,
            "nupack_calls": nupack_calls,
            "subset": subset,
            "indices": indices,
        }

    def _emit_progress():
        elapsed_s = time.time() - start_t
        print(
            f"Subset selection progress: accepted {len(subset)}/{max_size} fresh pairs "
            f"after {attempts} attempts and {nupack_calls} direct NUPACK calls "
            f"({elapsed_s / 60.0:.1f} min elapsed).",
            flush=True,
        )

    def _evaluate_candidate(seq, rc_seq):
        nonlocal nupack_calls, passed_energy_filter, passed_homodimer

        if (
            fresh_pair_search_budget is not None
            and nupack_calls + 1 + estimate_offtarget_nupack_calls(len(subset)) >= fresh_pair_search_budget
        ):
            return None, "nupack_limit"

        nupack_calls += 1
        energy, self_e_seq, self_e_rc_seq = compute_nupack_energy(seq, rc_seq, type=hf.ENERGY_TYPE)

        if not (
            energy_min <= energy <= energy_max
            and self_e_seq >= self_energy_min
            and self_e_rc_seq >= self_energy_min
        ):
            return False, None

        passed_energy_filter += 1

        if offtarget_limit is not None:
            if (
                fresh_pair_search_budget is not None
                and nupack_calls + 2 + estimate_offtarget_nupack_calls(len(subset)) >= fresh_pair_search_budget
            ):
                return None, "nupack_limit"

            nupack_calls += 1
            homo_seq_result = compute_nupack_energy(seq, seq, type=hf.ENERGY_TYPE)
            nupack_calls += 1
            homo_rc_result = compute_nupack_energy(rc_seq, rc_seq, type=hf.ENERGY_TYPE)

            homo_seq_energy = (
                homo_seq_result[0] if isinstance(homo_seq_result, tuple) else homo_seq_result
            )
            homo_rc_energy = (
                homo_rc_result[0] if isinstance(homo_rc_result, tuple) else homo_rc_result
            )
            if homo_seq_energy < offtarget_limit or homo_rc_energy < offtarget_limit:
                return False, None

            passed_homodimer += 1

            passed_crossref, crossref_nupack_calls = crossreference_sequences(
                (seq, rc_seq),
                retained_pairs,
                offtarget_limit,
                max_pair_violations=allowed_violations,
            )
            nupack_calls += crossref_nupack_calls
            if not passed_crossref:
                return False, None

        return True, None

    # Candidate drawing: explicit finite-pool vs live-sampler handling.
    if isinstance(sequence_pairs, list):
        total = len(sequence_pairs)

        def _draw():
            return random.choice(sequence_pairs)

        def _pool_exhausted():
            return len(tested_indices) >= total
    elif hasattr(sequence_pairs, "sample_pair"):
        def _draw():
            return sequence_pairs.sample_pair()

        def _pool_exhausted():
            return False
    else:
        raise TypeError(
            "sequence_pairs must be either a list of (index, (seq, rc_seq)) "
            "or an object with a sample_pair() method."
        )

    try:
        while len(indices) < max_size and not _pool_exhausted():
            if stop_event is not None and stop_event.is_set():
                print(f"Stop event: returning {len(subset)} collected pairs.", flush=True)
                return subset, indices, "stop_event", nupack_calls, _build_state()
            if checkpoint_event is not None and checkpoint_event.is_set():
                print(f"Checkpoint request: returning {len(subset)} collected pairs.", flush=True)
                return subset, indices, "checkpoint_request", nupack_calls, _build_state()
            if timeout_s is not None and (time.time() - start_t) >= timeout_s:
                if not quiet_timeout:
                    elapsed_s = time.time() - start_t
                    print(f"Only {len(subset)} of requested {max_size} found (timeout after {elapsed_s:.2f}s).")
                    logger.info(
                        f"Only {len(subset)} of requested {max_size} found for given "
                        f"parameters (timeout = {timeout_s}s)."
                    )
                return subset, indices, "timeout", nupack_calls, _build_state()

            pair_id, (seq, rc_seq) = _draw()
            if pair_id in tested_indices:
                duplicate_streak += 1
                if duplicate_streak >= duplicate_streak_limit:
                    print(
                        "Duplicate streak limit reached during subset selection. "
                        f"Stopping after {duplicate_streak} consecutive seen IDs.",
                        flush=True,
                    )
                    return (
                        subset,
                        indices,
                        f"duplicate_streak_limit_reached={duplicate_streak_limit}",
                        nupack_calls,
                        _build_state(),
                    )
                continue

            tested_indices.add(pair_id)
            duplicate_streak = 0
            attempts += 1
            if progress_every and attempts % progress_every == 0:
                print(f"Progress: {len(subset)}/{max_size} accepted after {attempts} attempts")
            if progress_interval_s is not None and (time.time() - last_progress_t) >= progress_interval_s:
                _emit_progress()
                last_progress_t = time.time()

            accepted, candidate_stop = _evaluate_candidate(seq, rc_seq)
            if candidate_stop is not None:
                elapsed_s = time.time() - start_t
                print(
                    f"Only {len(subset)} of requested {max_size} found "
                    f"(NUPACK call limit hit after {elapsed_s:.2f}s, "
                    f"NUPACK calls: {nupack_calls})."
                )
                logger.info(
                    f"Only {len(subset)} of requested {max_size} found for given "
                    f"parameters (fresh_pair_search_budget = {fresh_pair_search_budget})."
                )
                return subset, indices, "nupack_limit", nupack_calls, _build_state()
            if accepted:
                subset.append((seq, rc_seq))
                indices.append(pair_id)
    except KeyboardInterrupt:
        print(f"\nInterrupted: returning {len(subset)} collected pairs.", flush=True)
        return subset, indices, "keyboard_interrupt", nupack_calls, _build_state()

    print(
        f"Selected {len(subset)} sequence pairs with energies in range "
        f"[{energy_min}, {energy_max}] and self energy above {self_energy_min}"
    )
    logger.info(
        f"Selected {len(subset)} sequence pairs with on-target energies in "
        f"range [{energy_min}, {energy_max}] and secondary-structure energy "
        f"above {self_energy_min}."
    )
    return subset, indices, None, nupack_calls, _build_state()


def select_all_in_energy_range(sequence_pairs, energy_min=-np.inf, energy_max=np.inf, avoid_ids=None):
    print("Selecting sequences...")

    if avoid_ids is None:
        avoid_ids = set()

    subset = []
    selected_ids = []

    for pair_id, (seq, rc_seq) in sequence_pairs:
        if pair_id in avoid_ids:
            continue

        energy, _, _ = compute_nupack_energy(seq, rc_seq, type="total")
        if energy_min <= energy <= energy_max:
            subset.append((seq, rc_seq))
            selected_ids.append(pair_id)

    print(f"Scanned and selected {len(subset)} sequence pairs in range [{energy_min}, {energy_max}]")
    return subset, selected_ids


def compute_offtarget_fraction_below_limit(off_energies, off_limit):
    if isinstance(off_energies, dict):
        values = np.concatenate(
            [
                off_energies["handle_handle_energies"].flatten(),
                off_energies["antihandle_handle_energies"].flatten(),
                off_energies["antihandle_antihandle_energies"].flatten(),
            ]
        )
        values = values[values != 0]
    else:
        values = np.ravel(off_energies)

    if values.size == 0:
        return 0.0

    return float(np.mean(values < float(off_limit)))
