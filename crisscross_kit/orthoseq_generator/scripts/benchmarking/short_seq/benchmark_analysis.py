"""
Graph metrics and cutoff search for short-sequence benchmarks.
"""

from __future__ import annotations

import numpy as np

from benchmark_dataset_tools import load_dataset
from orthoseq_generator.vertex_cover_algorithms import build_edges


def build_conflict_data(dataset: dict, offtarget_limit: float):
    """
    Build dense boolean conflict masks from the cached off-target matrices.

    Purpose
    -------
    Some benchmark baselines work more naturally with dense boolean masks than
    with explicit edge lists. This helper symmetrizes the cached same-strand
    matrices, combines all relevant interaction types into one pair-conflict
    mask, and separately marks self-conflicting vertices.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param offtarget_limit: Energy threshold below which an interaction counts
                            as a conflict.
    :type offtarget_limit: float

    :returns: Tuple of `(pair_conflict, self_violation)` boolean arrays.
    :rtype: tuple
    """
    hh = dataset["handle_handle_energies"]
    hah = dataset["handle_antihandle_energies"]
    ahah = dataset["antihandle_antihandle_energies"]

    hh_full = hh + hh.T - np.diag(np.diag(hh))
    ahah_full = ahah + ahah.T - np.diag(np.diag(ahah))
    pair_conflict = (
        (hh_full < offtarget_limit)
        | (ahah_full < offtarget_limit)
        | (hah < offtarget_limit)
        | (hah.T < offtarget_limit)
    )
    self_violation = (np.diag(hh_full) < offtarget_limit) | (np.diag(ahah_full) < offtarget_limit)
    return pair_conflict, self_violation


def compute_graph_conflict_density(dataset: dict, offtarget_limit: float) -> dict:
    """
    Compute the incompatibility-graph density induced by one off-target cutoff.

    Purpose
    -------
    The batch benchmark chooses cutoffs by target conflict density rather than
    by hard-coded energy values. This helper builds the benchmark graph from a
    dataset's cached matrices, counts self-edges and pairwise edges, and
    reports the resulting density using the benchmark convention that includes
    self-edges in the denominator.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param offtarget_limit: Energy threshold below which an interaction counts
                            as a conflict edge.
    :type offtarget_limit: float

    :returns: Summary of graph size and density for the requested cutoff.
    :rtype: dict
    """
    offtarget_dict = {
        "handle_handle_energies": dataset["handle_handle_energies"],
        "antihandle_handle_energies": dataset["handle_antihandle_energies"],
        "antihandle_antihandle_energies": dataset["antihandle_antihandle_energies"],
    }
    edges = build_edges(offtarget_dict, list(dataset["matrix_global_pair_ids"]), float(offtarget_limit))
    edge_count = len(edges)
    n = int(len(dataset["matrix_global_pair_ids"]))
    total_possible_edges = n + (n * (n - 1) // 2)
    density = float(edge_count / total_possible_edges) if total_possible_edges > 0 else 0.0
    self_edge_count = sum(1 for i, j in edges if i == j)
    return {
        "offtarget_limit": float(offtarget_limit),
        "matrix_candidate_count": n,
        "edge_count": edge_count,
        "self_edge_count": self_edge_count,
        "pair_edge_count": edge_count - self_edge_count,
        "total_possible_edges": total_possible_edges,
        "graph_conflict_density": density,
    }


def extract_relevant_energy_values(dataset: dict) -> np.ndarray:
    """
    Extract the distinct cached energy values that can change the benchmark
    conflict graph.

    Purpose
    -------
    When searching for a cutoff that matches a target graph density, only
    energy values that actually appear in the saved matrices can change the
    graph structure. This helper gathers those relevant thresholds from the
    same-strand triangular entries and the full cross-strand off-diagonal
    entries, then returns them as a sorted unique array.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :returns: Sorted unique candidate cutoffs drawn from the cached matrices.
    :rtype: numpy.ndarray
    """
    hh = dataset["handle_handle_energies"]
    hah = dataset["handle_antihandle_energies"]
    ahah = dataset["antihandle_antihandle_energies"]
    hh_values = hh[np.tril_indices(hh.shape[0], k=0)]
    ahah_values = ahah[np.tril_indices(ahah.shape[0], k=0)]
    hah_values = hah[~np.eye(hah.shape[0], dtype=bool)]
    return np.unique(np.sort(np.concatenate((hh_values, hah_values, ahah_values)).astype(float)))


def find_offtarget_limit_for_target_density(dataset: dict, target_density: float) -> dict:
    """
    Find the cached off-target cutoff that best matches one target conflict
    density.

    Purpose
    -------
    Batch benchmarks are parameterized by desired graph density so different
    datasets can be compared at similar conflict levels. This helper performs a
    binary search over the relevant cached energy values and returns the cutoff
    whose induced graph density is closest to the requested target.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param target_density: Desired benchmark graph conflict density.
    :type target_density: float

    :returns: Best-matching cutoff summary for the requested density.
    :rtype: dict
    """
    candidate_cutoffs = extract_relevant_energy_values(dataset)
    if candidate_cutoffs.size == 0:
        raise ValueError("No candidate cutoff values found in dataset.")
    best_summary = None
    low = 0
    high = int(candidate_cutoffs.size - 1)
    while low <= high:
        mid = (low + high) // 2
        cutoff = float(candidate_cutoffs[mid])
        summary = compute_graph_conflict_density(dataset, cutoff)
        density = float(summary["graph_conflict_density"])
        error = abs(density - float(target_density))
        if (
            best_summary is None
            or error < best_summary["absolute_error"]
            or (error == best_summary["absolute_error"] and cutoff < best_summary["selected_offtarget_limit"])
        ):
            best_summary = {
                "target_conflict_density": float(target_density),
                "selected_offtarget_limit": cutoff,
                "achieved_conflict_density": density,
                "absolute_error": error,
                "edge_count": summary["edge_count"],
                "self_edge_count": summary["self_edge_count"],
                "pair_edge_count": summary["pair_edge_count"],
                "matrix_candidate_count": summary["matrix_candidate_count"],
                "total_possible_edges": summary["total_possible_edges"],
            }
        if density < float(target_density):
            low = mid + 1
        else:
            high = mid - 1
    return best_summary


def find_offtarget_limits_for_target_densities(dataset: dict, target_densities: list[float]) -> list[dict]:
    """
    Resolve multiple target conflict densities to their best cached cutoffs.

    Purpose
    -------
    The batch and single-dataset runners usually benchmark several density
    targets at once. This helper applies
    `find_offtarget_limit_for_target_density` to each requested density and
    returns the ordered list of summaries.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param target_densities: Target benchmark graph densities to match.
    :type target_densities: list[float]

    :returns: Cutoff summaries aligned with the requested densities.
    :rtype: list[dict]
    """
    return [find_offtarget_limit_for_target_density(dataset, target_density) for target_density in target_densities]
