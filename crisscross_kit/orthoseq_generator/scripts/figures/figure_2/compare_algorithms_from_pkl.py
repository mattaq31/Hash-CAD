"""
Purpose:
    Compare vertex-cover selection vs naive greedy selection on PKL data
    for a list of explicit off-target limits.
"""

import os
import glob
import pickle
import random
import math
import numpy as np
import pandas as pd
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import vertex_cover_algorithms as vca


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


_COMPARE_CTX = {}


def _init_compare_worker(ctx):
    # Avoid sending large numpy arrays through initargs when possible.
    if "pkl_path" in ctx and ("ids" not in ctx or "off_energies" not in ctx):
        with open(ctx["pkl_path"], "rb") as f:
            data = pickle.load(f)

        subset = data.get("subset_pairs")
        ids = data.get("subset_ids")
        off_energies = data.get("off_energies")
        length = data.get("length")
        range_sigma = data.get("range_sigma")
        min_on = data.get("min_on")
        max_on = data.get("max_on")

        if subset is None or ids is None or off_energies is None:
            raise ValueError(f"Missing required keys in {ctx['pkl_path']}")

        ctx = {
            **ctx,
            "ids": ids,
            "id_to_seq": dict(zip(ids, subset)),
            "off_energies": off_energies,
            "n_vertices": len(ids),
            "sequence_length": length,
            "range_sigma": range_sigma,
            "min_on": min_on,
            "max_on": max_on,
        }

    _COMPARE_CTX.update(ctx)


def _run_compare_single_seed(run_seed, offtarget_limits, conflict_probs):
    ids = _COMPARE_CTX["ids"]
    id_to_seq = _COMPARE_CTX["id_to_seq"]
    off_energies = _COMPARE_CTX["off_energies"]
    n_vertices = _COMPARE_CTX["n_vertices"]
    length = _COMPARE_CTX["sequence_length"]
    range_sigma = _COMPARE_CTX["range_sigma"]
    min_on = _COMPARE_CTX["min_on"]
    max_on = _COMPARE_CTX["max_on"]
    num_vertices_to_remove = _COMPARE_CTX["num_vertices_to_remove"]
    max_iterations = _COMPARE_CTX["max_iterations"]
    limit = _COMPARE_CTX["limit"]
    multistart = _COMPARE_CTX["multistart"]
    population_size = _COMPARE_CTX["population_size"]
    show_progress = _COMPARE_CTX["show_progress"]
    pkl_path = _COMPARE_CTX["pkl_path"]
    run_idx_by_seed = _COMPARE_CTX["run_idx_by_seed"]

    rows = []
    for cutoff in offtarget_limits:
        conflict_prob = float(conflict_probs[float(cutoff)])
        naive_sequences = _run_naive(ids, id_to_seq, off_energies, cutoff, random_seed=run_seed)
        print(f"alg=naive size={len(naive_sequences)} run={run_idx_by_seed[run_seed]} cutoff={float(cutoff)}")
        rows.append({
            "pkl_path": pkl_path,
            "run_type": "naive",
            "run_idx": run_idx_by_seed[run_seed],
            "num_vertices": n_vertices,
            "offtarget_limit": float(cutoff),
            "conflict_probability": conflict_prob,
            "independent_set_size": len(naive_sequences),
            "independent_set_sequences": naive_sequences,
            "set_size_trajectories": None,
            "sequence_length": length,
            "range_sigma": range_sigma,
            "min_on": min_on,
            "max_on": max_on,
        })

        vc_sequences, vc_trajectories = _run_vertex_cover(
            ids,
            id_to_seq,
            off_energies,
            cutoff,
            random_seed=run_seed,
            num_vertices_to_remove=num_vertices_to_remove,
            max_iterations=max_iterations,
            limit=limit,
            multistart=multistart,
            population_size=population_size,
            show_progress=show_progress,
        )
        print(f"alg=vertex_cover size={len(vc_sequences)} run={run_idx_by_seed[run_seed]} cutoff={float(cutoff)}")
        rows.append({
            "pkl_path": pkl_path,
            "run_type": "vertex_cover",
            "run_idx": run_idx_by_seed[run_seed],
            "num_vertices": n_vertices,
            "offtarget_limit": float(cutoff),
            "conflict_probability": conflict_prob,
            "independent_set_size": len(vc_sequences),
            "independent_set_sequences": vc_sequences,
            "set_size_trajectories": vc_trajectories,
            "sequence_length": length,
            "range_sigma": range_sigma,
            "min_on": min_on,
            "max_on": max_on,
        })

    return rows


def _snap_cutoff_to_step(base_cutoff, step):
    """
    Snap the starting cutoff to the first multiple of step that is >= base_cutoff.
    This keeps cutoffs aligned across runs while staying above the base cutoff.
    """
    if step <= 0:
        raise ValueError("step must be positive")
    base = float(base_cutoff)
    step = float(step)
    return math.ceil(base / step) * step


def _build_offtarget_limits(off_energies, base_cutoff, step=0.1, target_pc=0.5, max_steps=2000):
    # Start at the snapped cutoff and step upward until we hit target conflict probability.
    if off_energies is None:
        return []

    offtarget_limits = []
    start_cutoff = _snap_cutoff_to_step(base_cutoff, step)
    for i in range(max_steps):
        cutoff = start_cutoff + (i * float(step))
        pc = float(vca.compute_pair_conflict_probability(off_energies, cutoff))
        offtarget_limits.append(cutoff)
        if pc >= target_pc:
            break

    return offtarget_limits


def _build_conflict_data(off_energies, cutoff):
    """
    Builds pairwise conflict matrix and self-violation mask from off-target energies.

    Logic matches naive_search.py:
    - Self-violation: reject a candidate if its handle-handle or antihandle-antihandle
      self interaction is below the cutoff.
    - Pairwise conflict: reject a candidate if any interaction with an already-selected
      sequence is below the cutoff across the three interaction types.
    """
    hh = off_energies["handle_handle_energies"]
    hah = off_energies["antihandle_handle_energies"]
    ahah = off_energies["antihandle_antihandle_energies"]

    # Symmetrize lower-triangular matrices.
    hh_full = hh + hh.T - np.diag(np.diag(hh))
    ahah_full = ahah + ahah.T - np.diag(np.diag(ahah))

    # Pairwise conflict if any interaction is below cutoff.
    pair_conflict = (hh_full < cutoff) | (ahah_full < cutoff) | (hah < cutoff) | (hah.T < cutoff)

    # Self-violation if either homodimer energy is below cutoff.
    self_violation = (np.diag(hh_full) < cutoff) | (np.diag(ahah_full) < cutoff)

    return pair_conflict, self_violation


def _run_naive(ids, id_to_seq, off_energies, cutoff, random_seed=41):
    # Randomized greedy ordering (reproducible by seed).
    random.seed(random_seed)
    pair_conflict, self_violation = _build_conflict_data(off_energies, float(cutoff))

    n = len(ids)
    order = list(range(n))
    random.shuffle(order)

    selected = []
    selected_mask = np.zeros(n, dtype=bool)

    for idx in order:
        # Enforce self-interaction cutoff (same as naive_search.py)
        if self_violation[idx]:
            continue

        # Enforce pairwise off-target cutoff
        if np.any(pair_conflict[idx, selected_mask]):
            continue

        selected.append(idx)
        selected_mask[idx] = True

    return [id_to_seq[ids[i]] for i in selected]


def _run_vertex_cover(ids, id_to_seq, off_energies, cutoff, random_seed=41,
                      num_vertices_to_remove=None, max_iterations=200, limit=70,
                      multistart=1, population_size=300, show_progress=True):
    # Vertex-cover search with stochastic components.
    random.seed(random_seed)
    edges = vca.build_edges(off_energies, ids, float(cutoff))
    vertices = set(ids)
    n_remove = num_vertices_to_remove
    if n_remove is None or n_remove == 0:
        n_remove = max(1, int(round(0.2 * len(vertices))))

    vertex_cover, trajectories = vca.iterative_vertex_cover_multi(
        vertices,
        edges,
        avoid_V=None,
        num_vertices_to_remove=n_remove,
        max_iterations=max_iterations,
        limit=limit,
        multistart=multistart,
        population_size=population_size,
        show_progress=show_progress,
    )

    independent = vertices - vertex_cover
    return [id_to_seq[i] for i in independent], trajectories


def run_compare(
    pkl_path,
    offtarget_limits=None,
    random_seed=41,
    num_runs=10,
    num_vertices_to_remove=None,
    max_iterations=100,
    limit=np.inf,
    multistart=1,
    population_size=900,
    show_progress=False,
    offtarget_step=0.1,
    target_conflict_prob=0.5,
    max_steps=2000,
    output_dir=None,
    parallel=True,
):
    # Load precomputed energies.
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    subset = data.get("subset_pairs")
    ids = data.get("subset_ids")
    off_energies = data.get("off_energies")
    length = data.get("length")
    range_sigma = data.get("range_sigma")
    min_on = data.get("min_on")
    max_on = data.get("max_on")

    if subset is None or ids is None or off_energies is None:
        raise ValueError(f"Missing required keys in {pkl_path}")

    id_to_seq = dict(zip(ids, subset))
    base = os.path.splitext(os.path.basename(pkl_path))[0]
    # Build off-target limits dynamically if not provided.
    base_cutoff = max_on
    if offtarget_limits is None or len(offtarget_limits) == 0:
        if base_cutoff is None:
            raise ValueError(f"Missing max_on in {pkl_path} for dynamic offtarget limits")
        offtarget_limits = _build_offtarget_limits(
            off_energies,
            base_cutoff=base_cutoff,
            step=offtarget_step,
            target_pc=target_conflict_prob,
            max_steps=max_steps,
        )

    # Result rows for the DataFrame.
    n_vertices = len(ids)
    rows = []

    conflict_probs = {
        float(cutoff): float(vca.compute_pair_conflict_probability(off_energies, float(cutoff)))
        for cutoff in offtarget_limits
    }

    run_seeds = [int(random_seed) + run_idx for run_idx in range(num_runs)]
    run_idx_by_seed = {seed: idx for idx, seed in enumerate(run_seeds)}

    if parallel and os.environ.get("ORTHOSEQ_NO_MP", "").strip().lower() not in ("1", "true", "yes"):
        # Pass only lightweight config through initargs; worker loads PKL locally.
        ctx = {
            "num_vertices_to_remove": num_vertices_to_remove,
            "max_iterations": max_iterations,
            "limit": limit,
            "multistart": multistart,
            "population_size": population_size,
            "show_progress": show_progress,
            "pkl_path": pkl_path,
            "run_idx_by_seed": run_idx_by_seed,
        }
        max_workers = _max_workers()
        mp_ctx = _mp_context_from_env()
        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_compare_worker,
            initargs=(ctx,),
            mp_context=mp_ctx,
        ) as executor:
            futures = []
            for seed in run_seeds:
                futures.append(executor.submit(_run_compare_single_seed, seed, offtarget_limits, conflict_probs))
            for future in as_completed(futures):
                rows.extend(future.result())
    else:
        _COMPARE_CTX.update({
            "ids": ids,
            "id_to_seq": id_to_seq,
            "off_energies": off_energies,
            "n_vertices": n_vertices,
            "sequence_length": length,
            "range_sigma": range_sigma,
            "min_on": min_on,
            "max_on": max_on,
            "num_vertices_to_remove": num_vertices_to_remove,
            "max_iterations": max_iterations,
            "limit": limit,
            "multistart": multistart,
            "population_size": population_size,
            "show_progress": show_progress,
            "pkl_path": pkl_path,
            "run_idx_by_seed": run_idx_by_seed,
        })
        for run_seed in run_seeds:
            rows.extend(_run_compare_single_seed(run_seed, offtarget_limits, conflict_probs))

    rows.sort(key=lambda r: (r["offtarget_limit"], r["run_idx"], r["run_type"]))

    # Save results to PKL/CSV for plotting.
    df = pd.DataFrame(rows)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_pkl = os.path.join(output_dir, f"{base}_compare_results.pkl")
        out_csv = os.path.join(output_dir, f"{base}_compare_results.csv")
    else:
        out_pkl = f"{base}_compare_results.pkl"
        out_csv = f"{base}_compare_results.csv"
    df.to_pickle(out_pkl)
    df.to_csv(out_csv, index=False)
    print(f"Saved: {out_pkl}")
    print(f"Saved: {out_csv}")
    return df


if __name__ == "__main__":
    # Minimal defaults for manual runs.
    OUTPUT_DIR = "results"
    #PKL_PATHS = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_subset.pkl")))
    PKL_PATHS = [os.path.join(OUTPUT_DIR,"short_seq_6mer_sigma0p5_subset.pkl")]
    for pkl_path in PKL_PATHS:
        run_compare(
            pkl_path,
            num_runs=2,
            offtarget_step=0.3,
            target_conflict_prob=0.5,
            limit=np.inf,
            show_progress=False,
            output_dir=OUTPUT_DIR,
        )
