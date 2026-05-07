# Short-Sequence Benchmarking

This subtree contains the saved-dataset benchmark workflow for short sequence
pairs.

The supported top-level workflow is:

1. build datasets
2. run batch benchmarks across those datasets
3. plot the saved benchmark outputs

## Core Modules

- `benchmark_dataset_tools.py`
  - build dataset bundles
  - load saved datasets
  - reconstruct dataset-level NUPACK calls needed to build the dataset
  - expose the saved ID and matrix lookup helpers used by the benchmark code

- `benchmark_analysis.py`
  - compute graph conflict density from saved matrices
  - find off-target cutoffs for target conflict densities

- `benchmark_algorithms.py`
  - run the benchmarked search variants against a saved dataset
  - write XLSX benchmark reports

## Supported Entrypoints

The public script surface in `scripts/` is intentionally small:

- `build_dataset.py`
  - builds the canonical datasets under `data/len4_7_tttt5p/`

- `run_batch_benchmark.py`
  - discovers complete datasets under `data/len4_7_tttt5p/`
  - runs `naive`, `vertex_cover`, and `hybrid_offline`
  - writes per-dataset XLSX reports under each dataset's `results/<benchmark_name>/`
  - writes one batch summary TOML at the dataset-parent level

- `plot_batch_benchmark.py`
  - reads the saved XLSX reports
  - groups results by extension condition
  - writes the batch plots to the dataset-parent directory

There is also one focused utility:

- `run_single_dataset_benchmark.py`
  - runs the same benchmark flow for one saved dataset
  - useful for spot checks and one-off comparisons
  - not the main reporting path

## Validation Utilities

Ad hoc or legacy-style checks live in `scripts/validate/`.

These scripts are kept for debugging and manual validation. They are not the
supported top-level benchmark interface, and they may be slower or more
special-purpose than the main batch flow.

## Data Layout

The current canonical dataset parent is:

- `data/len4_7_tttt5p/`

Each complete dataset directory contains:

- `dataset.toml`
- `dataset.npz`
- `results/`

Batch-level artifacts written at the dataset-parent level include:

- `batch_params.toml`
- `benchmark_summary_<benchmark_name>.toml`
- `batch_benchmark_selected_set_size_*.svg`

## Notes

- A dataset is treated as complete only when both `dataset.toml` and
  `dataset.npz` exist.
- The benchmark scripts are intentionally simple and keep parameters local to
  the script body.
- Legacy `no4x` dataset names should not be treated as canonical for new work.
