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
                result = compute_nupack_energy(a, b, type="total")
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
    max_nupack_calls=None,
    progress_every=None,
    progress_interval_s=120.0,
):
    if avoid_indices is None:
        avoid_indices = set()

    if retained_pairs is None:
        retained_pairs = []

    subset = []
    indices = []
    tested_indices = set(avoid_indices)
    attempts = 0
    nupack_calls = 0

    start_t = time.time()
    last_progress_t = start_t

    def _emit_progress():
        elapsed_s = time.time() - start_t
        print(
            f"Subset selection progress: accepted {len(subset)}/{max_size} fresh pairs "
            f"after {attempts} attempts and {nupack_calls} direct NUPACK calls "
            f"({elapsed_s / 60.0:.1f} min elapsed).",
            flush=True,
        )

    def _evaluate_candidate(seq, rc_seq):
        nonlocal nupack_calls

        if max_nupack_calls is not None and nupack_calls >= max_nupack_calls:
            return None, "nupack_limit"

        nupack_calls += 1
        energy, self_e_seq, self_e_rc_seq = compute_nupack_energy(seq, rc_seq, type="total")

        if not (
            energy_min <= energy <= energy_max
            and self_e_seq >= self_energy_min
            and self_e_rc_seq >= self_energy_min
        ):
            return False, None

        if offtarget_limit is not None:
            passed_crossref, crossref_nupack_calls = crossreference_sequences(
                (seq, rc_seq),
                retained_pairs,
                offtarget_limit,
                max_pair_violations=allowed_violations,
            )
            nupack_calls += crossref_nupack_calls
            if not passed_crossref:
                return False, None

        if max_nupack_calls is not None and nupack_calls >= max_nupack_calls:
            return None, "nupack_limit"

        return True, None

    if isinstance(sequence_pairs, list):
        total = len(sequence_pairs)

        while len(indices) < max_size and len(tested_indices) < total:
            if timeout_s is not None and (time.time() - start_t) >= timeout_s:
                elapsed_s = time.time() - start_t
                print(f"Only {len(subset)} of requested {max_size} found (timeout after {elapsed_s:.2f}s).")
                logger.info(
                    f"Only {len(subset)} of requested {max_size} found for given "
                    f"parameters (timeout = {timeout_s}s)."
                )
                return subset, indices, True, nupack_calls

            index, (seq, rc_seq) = random.choice(sequence_pairs)
            if index in tested_indices:
                continue

            tested_indices.add(index)
            attempts += 1
            if progress_every and attempts % progress_every == 0:
                print(f"Progress: {len(subset)}/{max_size} accepted after {attempts} attempts")
            if progress_interval_s is not None and (time.time() - last_progress_t) >= progress_interval_s:
                _emit_progress()
                last_progress_t = time.time()

            accepted, stop_reason = _evaluate_candidate(seq, rc_seq)
            if stop_reason is not None:
                elapsed_s = time.time() - start_t
                print(
                    f"Only {len(subset)} of requested {max_size} found "
                    f"(NUPACK call limit hit after {elapsed_s:.2f}s, "
                    f"NUPACK calls: {nupack_calls})."
                )
                logger.info(
                    f"Only {len(subset)} of requested {max_size} found for given "
                    f"parameters (max_nupack_calls = {max_nupack_calls})."
                )
                return subset, indices, True, nupack_calls
            if accepted:
                subset.append((seq, rc_seq))
                indices.append(index)

        print(
            f"Selected {len(subset)} sequence pairs with energies in range "
            f"[{energy_min}, {energy_max}] and self energy above {self_energy_min}"
        )
        logger.info(
            f"Selected {len(subset)} sequence pairs with on-target energies in "
            f"range [{energy_min}, {energy_max}] and secondary-structure energy "
            f"above {self_energy_min}."
        )
        return subset, indices, False, nupack_calls

    if not hasattr(sequence_pairs, "sample_pair"):
        raise TypeError(
            "sequence_pairs must be either a list of (index, (seq, rc_seq)) "
            "or an object with a sample_pair() method."
        )

    while len(indices) < max_size:
        if timeout_s is not None and (time.time() - start_t) >= timeout_s:
            elapsed_s = time.time() - start_t
            print(f"Only {len(subset)} of requested {max_size} found (timeout after {elapsed_s:.2f}s).")
            logger.info(
                f"Only {len(subset)} of requested {max_size} found for given "
                f"parameters (timeout = {timeout_s}s)."
            )
            return subset, indices, True, nupack_calls

        pair_id, (seq, rc_seq) = sequence_pairs.sample_pair()
        if pair_id in tested_indices:
            continue

        tested_indices.add(pair_id)
        attempts += 1
        if progress_every and attempts % progress_every == 0:
            print(f"Progress: {len(subset)}/{max_size} accepted after {attempts} attempts")
        if progress_interval_s is not None and (time.time() - last_progress_t) >= progress_interval_s:
            _emit_progress()
            last_progress_t = time.time()

        accepted, stop_reason = _evaluate_candidate(seq, rc_seq)
        if stop_reason is not None:
            elapsed_s = time.time() - start_t
            print(
                f"Only {len(subset)} of requested {max_size} found "
                f"(NUPACK call limit hit after {elapsed_s:.2f}s, "
                f"NUPACK calls: {nupack_calls})."
            )
            logger.info(
                f"Only {len(subset)} of requested {max_size} found for given "
                f"parameters (max_nupack_calls = {max_nupack_calls})."
            )
            return subset, indices, True, nupack_calls
        if accepted:
            subset.append((seq, rc_seq))
            indices.append(pair_id)

    print(
        f"Selected {len(subset)} sequence pairs with energies in range "
        f"[{energy_min}, {energy_max}] and self energy above {self_energy_min}"
    )
    logger.info(
        f"Selected {len(subset)} sequence pairs with on-target energies in "
        f"range [{energy_min}, {energy_max}] and secondary-structure energy "
        f"above {self_energy_min}."
    )
    return subset, indices, False, nupack_calls


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
