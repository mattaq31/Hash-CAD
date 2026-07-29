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
  - offline `hybrid_offline` mirrors the current live two-pass hybrid search
    and runs until the finite saved candidate pool is exhausted
  - write XLSX benchmark reports through the shared writer in
    `orthoseq_generator/search_reporting.py`

## Supported Entrypoints

The public script surface in `scripts/` is intentionally small:

- `build_dataset.py`
  - builds the canonical datasets under `data/len4_7_tttt5p_noGGGG/`

- `run_batch_benchmark.py`
  - discovers complete datasets under `data/len4_7_tttt5p_noGGGG/`
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

## Report Schema

Benchmark and live-search workbooks now share the same top-level report
layout:

- `found_pairs`
  - final reported pairs
- `run_metadata`
  - shared `input.*`, `search.*`, `nupack.*`, and `artifact.*` keys
  - benchmark-only dataset statistics remain under `dataset.*`

The shared workbook writer is still named
`write_hybrid_search_result_xlsx(...)` for historical reasons, but it is used
by non-hybrid benchmark paths as well.

## Validation Utilities

Ad hoc or legacy-style checks live in `scripts/validate/`.

These scripts are kept for debugging and manual validation. They are not the
supported top-level benchmark interface, and they may be slower or more
special-purpose than the main batch flow.

## Data Layout

The current canonical dataset parent is:

- `data/len4_7_tttt5p_noGGGG/`

Each complete dataset directory contains:

- `dataset.toml`
- `dataset.npz`
- `results/`

Batch-level artifacts written at the dataset-parent level include:

- `batch_params.toml`
- `benchmark_summary_<benchmark_name>.toml`
- `batch_benchmark_found_pair_count_*.svg`

At the moment, `data/len4_7_tttt5p_noGGGG/` is the canonical dataset parent.
If batch benchmark outputs have not been generated there yet, run
`run_batch_benchmark.py` before treating it as the canonical reporting output.

## O2 Workflow

The short-seq benchmark is run from a tracked repo checkout on O2 with the
dataset files uploaded separately.

### 1. Prepare the server checkout

From the O2 repo checkout:

```bash
cd $HOME/Hash-CAD/crisscross_kit
module load conda/miniforge3/24.11.3-0
conda activate cc
pip install -e .
```

This installs `crisscross-kit` in editable mode so the benchmark scripts use
the checked-out source tree.

### 2. Upload and unpack the dataset bundle

Upload `data.zip` into:

```text
crisscross_kit/orthoseq_generator/scripts/benchmarking/short_seq/
```

Then unpack it there:

```bash
cd $HOME/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/benchmarking/short_seq
unzip data.zip
```

The canonical dataset parent should then exist at:

```text
data/len4_7_tttt5p_noGGGG/
```

### 3. Submit the batch job

Submit from:

```bash
cd $HOME/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/benchmarking/short_seq/scripts
sbatch server_run_batch_benchmark_o2.sh
```

The server wrapper is intentionally local and ignored. It is not meant to be a
tracked benchmark artifact.

### 4. Monitor the run

```bash
squeue -u $USER
sacct -j <jobid> --format=JobID,JobName,Partition,State,Elapsed,ExitCode
tail -f slurm-shortseq_bench2-<jobid>.out
```

## Known O2 Details

- The Slurm wrapper should use `SLURM_SUBMIT_DIR` when changing directories.
  Under `sbatch`, `BASH_SOURCE[0]` points to Slurm's spool copy of the script,
  not the original repo path. A plain `cd "$(dirname "${BASH_SOURCE[0]}")"`
  will therefore break relative paths.
- Do not `git pull` into a checkout that active jobs are using.
- Uploaded zip files and Slurm log files are ignored under
  `scripts/benchmarking/.gitignore`.

## Notes

- A dataset is treated as complete only when both `dataset.toml` and
  `dataset.npz` exist.
- The benchmark scripts are intentionally simple and keep parameters local to
  the script body.
- Legacy `no4x` dataset names should not be treated as canonical for new work.
