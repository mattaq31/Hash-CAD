"""
Purpose:
    Compute pair conflict probabilities from a PKL file using off-target energies.
    Optionally derive cutoffs for target conflict probabilities.
"""

import pickle
import numpy as np

from orthoseq_generator import vertex_cover_algorithms as vca


def _flatten_off_energies(off_energies):
    # Flatten all off-target energy matrices into one vector.
    if isinstance(off_energies, dict):
        values = np.concatenate([
            off_energies["handle_handle_energies"].flatten(),
            off_energies["antihandle_handle_energies"].flatten(),
            off_energies["antihandle_antihandle_energies"].flatten(),
        ])
        values = values[values != 0]
        return values
    return np.ravel(off_energies)


def find_offtarget_limit_for_conflict(off_energies, target_pc, tol=0.005):
    # Binary search over unique energy values to hit the target probability.
    values = _flatten_off_energies(off_energies)
    if values.size == 0:
        return None, None

    unique_vals = np.unique(values)
    unique_vals.sort()

    low = 0
    high = len(unique_vals) - 1
    best_cutoff = None
    best_pc = None
    best_diff = float("inf")

    while low <= high:
        mid = (low + high) // 2
        cutoff = float(unique_vals[mid])
        pc = vca.compute_pair_conflict_probability(off_energies, cutoff)
        diff = abs(pc - target_pc)
        if diff < best_diff:
            best_diff = diff
            best_cutoff = cutoff
            best_pc = pc
            if diff <= tol:
                break
        if pc < target_pc:
            low = mid + 1
        else:
            high = mid - 1

    return best_cutoff, best_pc


def run_analyze(pkl_path, offtarget_limits=None, target_conflict_probs=None):
    # Load PKL and optionally report either explicit or target-based cutoffs.
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    off_energies = data.get("off_energies")
    if off_energies is None:
        raise ValueError(f"Missing off_energies in {pkl_path}")

    if offtarget_limits:
        for cutoff in offtarget_limits:
            pc = vca.compute_pair_conflict_probability(off_energies, float(cutoff))
            print(f"cutoff={cutoff:.3f} -> conflict_probability={pc:.4f}")

    if target_conflict_probs:
        for target_pc in target_conflict_probs:
            cutoff, pc = find_offtarget_limit_for_conflict(off_energies, float(target_pc))
            print(f"target Pc={target_pc:.3f} -> cutoff={cutoff} (Pc={pc})")


if __name__ == "__main__":
    PKL_PATH = ""
    OFFTARGET_LIMITS = []
    TARGET_CONFLICT_PROBS = []

    run_analyze(
        PKL_PATH,
        offtarget_limits=OFFTARGET_LIMITS,
        target_conflict_probs=TARGET_CONFLICT_PROBS,
    )
