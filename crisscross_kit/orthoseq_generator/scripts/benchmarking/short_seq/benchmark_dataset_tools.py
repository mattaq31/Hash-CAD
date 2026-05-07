"""
Dataset construction and lookup helpers for short-sequence benchmarks.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tomllib

import numpy as np

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.energy_computations import (
    compute_offtarget_energies,
    compute_ontarget_energies,
)
from orthoseq_generator.sequence_generation import create_sequence_pairs_pool


def _toml_string(value: str) -> str:
    """Return a TOML-safe quoted string literal."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_bool(value: bool) -> str:
    """Return the TOML literal for a Python boolean."""
    return "true" if value else "false"


def _write_dataset_toml(metadata_path: Path, metadata: dict) -> None:
    """
    Write the human-readable metadata sidecar for a saved benchmark dataset.

    Purpose
    -------
    Each benchmark dataset is stored as a compact `dataset.npz` bundle plus a
    TOML sidecar that explains the inputs, derived ranges, file layout, and ID
    conventions. This helper serializes that metadata contract in a stable
    format so later scripts can inspect the dataset without opening the binary
    arrays first.

    :param metadata_path: Output path for the dataset TOML sidecar.
    :type metadata_path: pathlib.Path

    :param metadata: Dataset metadata payload assembled by
                     `build_short_seq_dataset`.
    :type metadata: dict

    :returns: None
    :rtype: None
    """
    lines = [
        'dataset_version = "1"',
        f'created_at = {_toml_string(metadata["created_at"])}',
        "",
        "[inputs]",
        f"length = {metadata['length']}",
        f"range_sigma = {metadata['range_sigma']}",
        f"avoid_gggg = {_toml_bool(metadata['avoid_gggg'])}",
        f"fivep_ext = {_toml_string(metadata['fivep_ext'])}",
        f"threep_ext = {_toml_string(metadata['threep_ext'])}",
        f"random_seed = {metadata['random_seed']}",
        "",
        "[nupack]",
        f"material = {_toml_string(metadata['material'])}",
        f"celsius = {metadata['celsius']}",
        f"sodium = {metadata['sodium']}",
        f"magnesium = {metadata['magnesium']}",
        "",
        "[derived]",
        f"total_candidate_count = {metadata['total_candidate_count']}",
        f"matrix_candidate_count = {metadata['matrix_candidate_count']}",
        f"mean_ontarget_energy = {metadata['mean_ontarget_energy']}",
        f"std_ontarget_energy = {metadata['std_ontarget_energy']}",
        f"min_ontarget_energy = {metadata['min_ontarget_energy']}",
        f"max_ontarget_energy = {metadata['max_ontarget_energy']}",
        "",
        "[files]",
        'npz_filename = "dataset.npz"',
        "",
        "[arrays]",
        'all_global_pair_ids = "shape=(m,)"',
        'all_seqs = "shape=(m,)"',
        'all_rc_seqs = "shape=(m,)"',
        'all_on_target_energies = "shape=(m,)"',
        'all_self_energy_seqs = "shape=(m,)"',
        'all_self_energy_rc_seqs = "shape=(m,)"',
        'all_is_in_ontarget_window = "shape=(m,)"',
        'matrix_global_pair_ids = "shape=(n,)"',
        'handle_handle_energies = "shape=(n,n)"',
        'handle_antihandle_energies = "shape=(n,n)"',
        'antihandle_antihandle_energies = "shape=(n,n)"',
        "",
        "[indexing]",
        'canonical_id = "global_pair_id"',
        'matrix_axis = "Row/column i in all matrices corresponds to matrix_global_pair_ids[i]."',
        'handle_handle = "handle_handle_energies[i,j] = seq_i vs seq_j for the matrix-local pairs."',
        'handle_antihandle = "handle_antihandle_energies[i,j] = seq_i vs rc_seq_j for the matrix-local pairs and is not assumed symmetric."',
        'antihandle_antihandle = "antihandle_antihandle_energies[i,j] = rc_seq_i vs rc_seq_j for the matrix-local pairs."',
        'pairwise_conflict_rule = "For matrix-local pair indices i and j, check hh[i,j], ahah[i,j], hah[i,j], and hah[j,i]."',
        "",
    ]
    metadata_path.write_text("\n".join(lines), encoding="utf-8")


def build_short_seq_dataset(
    output_dir: str | Path,
    *,
    length: int,
    range_sigma: float = 1.0,
    avoid_gggg: bool = True,
    fivep_ext: str = "",
    threep_ext: str = "",
    random_seed: int = 42,
    material: str = "dna",
    celsius: float = 37,
    sodium: float = 0.05,
    magnesium: float = 0.025,
) -> Path:
    """
    Build the canonical saved dataset bundle for one short-sequence benchmark
    condition.

    Purpose
    -------
    The benchmarking workflow uses precomputed dataset artifacts rather than
    generating candidate pools on the fly during every run. This function
    creates that artifact: it enumerates the full candidate pool for one
    sequence-length and extension condition, computes the on-target and
    self-structure energies for all pairs, selects the matrix subset inside the
    benchmark on-target window, computes the cached off-target matrices for
    that subset, and writes the resulting `dataset.toml` / `dataset.npz`
    bundle.

    The saved dataset is the shared input contract for the batch runner, the
    single-dataset runner, and the plotting / validation helpers.

    :param output_dir: Directory where `dataset.toml` and `dataset.npz` should
                       be written.
    :type output_dir: str or pathlib.Path

    :param length: Core sequence length for the candidate pool.
    :type length: int

    :param range_sigma: Width of the accepted on-target window measured in
                        standard deviations below the mean on-target energy.
    :type range_sigma: float

    :param avoid_gggg: Whether to exclude candidates containing four identical
                       bases in a row in the core sequence.
    :type avoid_gggg: bool

    :param fivep_ext: Fixed 5' extension prepended to each generated sequence.
    :type fivep_ext: str

    :param threep_ext: Fixed 3' extension appended to each generated sequence.
    :type threep_ext: str

    :param random_seed: Seed recorded in the dataset metadata for provenance.
                        The underlying full-pool generation is deterministic
                        for a given condition, but the saved artifact records
                        the benchmark configuration explicitly.
    :type random_seed: int

    :param material: NUPACK material model used for all cached energies.
    :type material: str

    :param celsius: Temperature used for all cached energies.
    :type celsius: float

    :param sodium: Sodium concentration used for all cached energies.
    :type sodium: float

    :param magnesium: Magnesium concentration used for all cached energies.
    :type magnesium: float

    :returns: Output directory containing the completed dataset bundle.
    :rtype: pathlib.Path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hf.set_nupack_params(
        material=material,
        celsius=celsius,
        sodium=sodium,
        magnesium=magnesium,
    )

    sequence_pairs_list = create_sequence_pairs_pool(
        length=length,
        fivep_ext=fivep_ext,
        threep_ext=threep_ext,
        avoid_gggg=avoid_gggg,
    )
    global_pair_ids = [pair_id for pair_id, _ in sequence_pairs_list]
    all_pairs = [pair for _, pair in sequence_pairs_list]

    on_target_energies, self_energy_seqs, self_energy_rc_seqs = compute_ontarget_energies(all_pairs)
    mean_ontarget_energy = float(np.mean(on_target_energies))
    std_ontarget_energy = float(np.std(on_target_energies))
    min_ontarget_energy = float(mean_ontarget_energy - (float(range_sigma) * std_ontarget_energy))
    max_ontarget_energy = float(mean_ontarget_energy)

    in_window_mask = []
    matrix_global_pair_ids = []
    matrix_pairs = []
    for pair_id, pair, on_energy in zip(global_pair_ids, all_pairs, on_target_energies):
        is_in_window = min_ontarget_energy <= float(on_energy) <= max_ontarget_energy
        in_window_mask.append(bool(is_in_window))
        if is_in_window:
            matrix_global_pair_ids.append(pair_id)
            matrix_pairs.append(pair)

    if not matrix_pairs:
        raise ValueError("No sequence pairs survived the on-target filter.")

    offtarget_energies = compute_offtarget_energies(matrix_pairs)
    np.savez_compressed(
        output_dir / "dataset.npz",
        all_global_pair_ids=np.array(global_pair_ids, dtype=int),
        all_seqs=np.array([seq for seq, _ in all_pairs]),
        all_rc_seqs=np.array([rc_seq for _, rc_seq in all_pairs]),
        all_on_target_energies=np.array(on_target_energies, dtype=float),
        all_self_energy_seqs=np.array(self_energy_seqs, dtype=float),
        all_self_energy_rc_seqs=np.array(self_energy_rc_seqs, dtype=float),
        all_is_in_ontarget_window=np.array(in_window_mask, dtype=bool),
        matrix_global_pair_ids=np.array(matrix_global_pair_ids, dtype=int),
        handle_handle_energies=offtarget_energies["handle_handle_energies"],
        handle_antihandle_energies=offtarget_energies["antihandle_handle_energies"],
        antihandle_antihandle_energies=offtarget_energies["antihandle_antihandle_energies"],
    )

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "length": int(length),
        "range_sigma": float(range_sigma),
        "avoid_gggg": bool(avoid_gggg),
        "fivep_ext": str(fivep_ext),
        "threep_ext": str(threep_ext),
        "random_seed": int(random_seed),
        "material": material,
        "celsius": float(celsius),
        "sodium": float(sodium),
        "magnesium": float(magnesium),
        "total_candidate_count": len(all_pairs),
        "matrix_candidate_count": len(matrix_pairs),
        "mean_ontarget_energy": mean_ontarget_energy,
        "std_ontarget_energy": std_ontarget_energy,
        "min_ontarget_energy": min_ontarget_energy,
        "max_ontarget_energy": max_ontarget_energy,
    }
    _write_dataset_toml(output_dir / "dataset.toml", metadata)
    return output_dir


def load_dataset(dataset_dir: str | Path) -> dict:
    """
    Load a saved benchmark dataset bundle into the in-memory dictionary format
    used by the benchmark modules.

    Purpose
    -------
    The rest of the benchmark subtree expects one shared dataset shape that
    includes both the array payloads from `dataset.npz` and the human-readable
    metadata from `dataset.toml`. This helper rebuilds that combined structure
    and also injects the resolved dataset paths for downstream reporting.

    :param dataset_dir: Directory containing `dataset.toml` and `dataset.npz`.
    :type dataset_dir: str or pathlib.Path

    :returns: Dataset bundle with arrays, metadata, and resolved file paths.
    :rtype: dict
    """
    dataset_dir = Path(dataset_dir)
    with (dataset_dir / "dataset.toml").open("rb") as f:
        metadata = tomllib.load(f)
    with np.load(dataset_dir / "dataset.npz", allow_pickle=False) as data:
        bundle = {key: data[key] for key in data.files}
    bundle["dataset_dir"] = str(dataset_dir)
    bundle["dataset_toml"] = str(dataset_dir / "dataset.toml")
    bundle["dataset_npz"] = str(dataset_dir / "dataset.npz")
    bundle["metadata"] = metadata
    return bundle


def estimate_dataset_nupack_budget(dataset: dict) -> int:
    """
    Reconstruct the conceptual total NUPACK cost represented by a saved
    dataset.

    Purpose
    -------
    Benchmark reports distinguish between the direct calls consumed during a
    search run and the larger virtual cost of creating the cached dataset in
    the first place. This helper reconstructs that dataset-level budget from
    the metadata counts so benchmark reports can compare offline and live runs
    on a shared scale.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :returns: Virtual NUPACK-call budget for the dataset construction step.
    :rtype: int
    """
    derived = dataset["metadata"]["derived"]
    total_candidate_count = int(derived["total_candidate_count"])
    matrix_candidate_count = int(derived["matrix_candidate_count"])
    return total_candidate_count + (2 * matrix_candidate_count * matrix_candidate_count)


def build_global_to_matrix_idx(matrix_global_pair_ids) -> dict:
    """
    Build the lookup from canonical global pair ID to matrix-local row/column
    index.

    Purpose
    -------
    Many benchmark operations need to move between the full candidate pool and
    the cached matrix subset. This helper provides the matrix-local side of
    that mapping for the saved off-target arrays.

    :param matrix_global_pair_ids: Global IDs aligned with the cached matrix
                                   rows and columns.
    :type matrix_global_pair_ids: iterable

    :returns: Mapping from global pair ID to matrix-local index.
    :rtype: dict
    """
    return {int(global_id): idx for idx, global_id in enumerate(matrix_global_pair_ids)}


def build_all_global_to_all_idx(all_global_pair_ids) -> dict:
    """
    Build the lookup from canonical global pair ID to full-pool array index.

    Purpose
    -------
    The saved dataset keeps the full candidate pool in flat arrays and a
    smaller matrix subset in the cached off-target matrices. This helper
    provides the lookup into the full-pool arrays.

    :param all_global_pair_ids: Global IDs aligned with the full-pool arrays.
    :type all_global_pair_ids: iterable

    :returns: Mapping from global pair ID to full-pool array index.
    :rtype: dict
    """
    return {int(global_id): idx for idx, global_id in enumerate(all_global_pair_ids)}


def get_pair_by_global_id(dataset: dict, global_id: int) -> tuple[str, str]:
    """
    Resolve one canonical pair ID back to its sequence pair.

    Purpose
    -------
    Some benchmark routines operate in terms of global IDs for bookkeeping and
    only need the actual sequences at the reporting or subset-construction
    boundary. This helper performs that lookup against the full saved pool.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param global_id: Canonical global pair ID.
    :type global_id: int

    :returns: Sequence pair `(seq, rc_seq)` for the requested ID.
    :rtype: tuple[str, str]
    """
    all_idx_by_global = build_all_global_to_all_idx(dataset["all_global_pair_ids"])
    all_idx = all_idx_by_global[int(global_id)]
    return str(dataset["all_seqs"][all_idx]), str(dataset["all_rc_seqs"][all_idx])


def get_selected_rows(dataset: dict, selected_global_ids) -> list[dict]:
    """
    Build canonical report rows for a selected set of global pair IDs.

    Purpose
    -------
    Benchmark algorithms usually keep only global IDs while searching. The XLSX
    writer, however, expects a sheet-oriented representation that includes
    sequence strings, cached energy values, and both global and matrix-local
    identifiers. This helper expands a selected ID set into that common row
    format.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param selected_global_ids: Global IDs to include in the selected-set
                                output.
    :type selected_global_ids: iterable

    :returns: Canonical selected-row entries for reporting.
    :rtype: list[dict]
    """
    all_idx_by_global = build_all_global_to_all_idx(dataset["all_global_pair_ids"])
    matrix_idx_by_global = build_global_to_matrix_idx(dataset["matrix_global_pair_ids"])
    rows = []
    for global_id in sorted(int(gid) for gid in selected_global_ids):
        all_idx = all_idx_by_global[global_id]
        rows.append(
            {
                "global_pair_id": global_id,
                "matrix_idx": matrix_idx_by_global.get(global_id),
                "seq": str(dataset["all_seqs"][all_idx]),
                "rc_seq": str(dataset["all_rc_seqs"][all_idx]),
                "on_target_energy_cached": float(dataset["all_on_target_energies"][all_idx]),
                "self_energy_seq_cached": float(dataset["all_self_energy_seqs"][all_idx]),
                "self_energy_rc_seq_cached": float(dataset["all_self_energy_rc_seqs"][all_idx]),
                "is_in_ontarget_window": bool(dataset["all_is_in_ontarget_window"][all_idx]),
            }
        )
    return rows


def build_sub_offtarget_dict(dataset: dict, selected_global_ids) -> dict:
    """
    Extract the cached off-target matrices for one selected subset of global
    pair IDs.

    Purpose
    -------
    The offline benchmark algorithms reuse the saved full-matrix data instead
    of recomputing off-target energies. This helper slices the dataset's cached
    matrices down to one working subset while preserving the shared dictionary
    shape expected by the graph-building utilities.

    :param dataset: Loaded benchmark dataset bundle.
    :type dataset: dict

    :param selected_global_ids: Global IDs defining the desired subset.
    :type selected_global_ids: iterable

    :returns: Cached off-target matrix dictionary for the requested subset.
    :rtype: dict
    """
    matrix_idx_by_global = build_global_to_matrix_idx(dataset["matrix_global_pair_ids"])
    local_indices = np.array([matrix_idx_by_global[int(global_id)] for global_id in selected_global_ids], dtype=int)
    return {
        "handle_handle_energies": dataset["handle_handle_energies"][np.ix_(local_indices, local_indices)],
        "antihandle_handle_energies": dataset["handle_antihandle_energies"][np.ix_(local_indices, local_indices)],
        "antihandle_antihandle_energies": dataset["antihandle_antihandle_energies"][np.ix_(local_indices, local_indices)],
    }
