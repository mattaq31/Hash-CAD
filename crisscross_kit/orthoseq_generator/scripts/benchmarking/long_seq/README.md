# Long-Seq Benchmark Workflow

This folder contains the live long-seq benchmark workflow.

The current canonical benchmark campaign is the pair of `batch_x...` runs:

- no 5' extension
- `TTTT` 5' extension

Everything else in `data/non_canonical/` and `scripts/non_canonical/` is older
or exploratory work and is not part of the current benchmark baseline.

## Canonical Layout

```text
long_seq/
  configs/
    templates/
    generated/
  data/
    batch_x_TTTT_sigma1p0_seed41/
    batch_x______sigma1p0_seed41/
    non_canonical/
  plots/
  scripts/
    prepare_conditions.py
    run_long_seq_naive_search.py
    run_long_seq_hybrid_search.py
    plot_single_limit_batch.py
    auxiliary_analysis/
    non_canonical/
```

Canonical benchmark inputs and outputs are centered around:

- `data/batch_x_TTTT_sigma1p0_seed41/`
- `data/batch_x______sigma1p0_seed41/`
- `plots/`

Use the top-level `data/` folders for saved benchmark workbooks and derived
machine-readable analysis outputs. This includes batch-local auxiliary-analysis
outputs under `data/<batch_name>/auxiliary_analysis/`. Use `plots/` for final
SVG figures from both the main canonical batch plots and the auxiliary
analysis. `scripts/non_canonical/` contains older or superseded workflows.

## Canonical Scripts

- `scripts/prepare_conditions.py`
  - generates one benchmark batch from a template TOML
  - writes generated conditions and Slurm wrappers under `configs/generated/`

- `scripts/run_long_seq_naive_search.py`
  - runs one generated naive condition TOML

- `scripts/run_long_seq_hybrid_search.py`
  - runs one generated hybrid condition TOML

- `scripts/plot_single_limit_batch.py`
  - plots the canonical single-limit batch outputs
  - writes SVGs to `plots/` by default

## Auxiliary Analysis

The scripts under `scripts/auxiliary_analysis/` are still part of the current
canonical long-seq analysis, but they are not the main benchmark pipeline.
They operate on the canonical `batch_x...` data after the main runs have
finished.

Their purpose is to poke the graph algorithm and the resulting benchmark graphs
a bit more closely, for example to:

- inspect how prune fraction changes the final orthogonal-pair count
- compare seed / collection progress between naive and graph-based runs
- show the roughly logarithmic scaling in the progress curves
- inspect conflict-probability distributions for selected sets

The current `plot_init900_outside_crossref.py` script is set up to write both
canonical len12 figures in one run, using the shared plot settings for the two
`batch_x...` datasets.

So the intended order is:

1. run the canonical batch
2. make the main canonical batch plots
3. optionally run the auxiliary analysis scripts for deeper inspection

## Prepare a Batch Locally

From the repo root:

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/prepare_conditions.py \
  --config crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/templates/<prep_config>.toml
```

This writes a generated batch under:

```text
crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated/
```

Each generated batch contains:

- `batch_summary.toml`
- one condition TOML per benchmark run
- one `naive_*.sh` or `hybrid_*.sh` wrapper per run
- `submit_all.sh`

The generated condition TOMLs also embed the benchmark output root under
`data/<batch_name>_sigma..._seed.../`.

## Run One Condition Locally

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/run_long_seq_naive_search.py \
  --config path/to/condition_naive_fb0p01_budget10000000.toml
```

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/run_long_seq_hybrid_search.py \
  --config path/to/condition_fb0p01_budget10000000_init900.toml
```

The runner writes:

- one XLSX workbook
- one on/off-target PDF
- one self-energy PDF

into the batch data directory selected by `output.dir` in the generated TOML.

## Plot the Canonical Batch

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/plot_single_limit_batch.py
```

With no arguments this plots the two canonical `batch_x...` folders and writes:

- `plots/long_seq_single_limit_batch_5p_none.svg`
- `plots/long_seq_single_limit_batch_5p_TTTT.svg`

You can also pass explicit batches:

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/plot_single_limit_batch.py \
  --data-root path/to/batch_a \
  --summary path/to/batch_a_summary.toml \
  --data-root path/to/batch_b \
  --summary path/to/batch_b_summary.toml
```

## O2 Workflow

The supported O2 workflow is:

1. generate the batch locally
2. zip the generated batch folder
3. upload the zip into `configs/generated/` on O2
4. unzip it there
5. run `bash submit_all.sh`

Example:

```bash
cd $HOME/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated
unzip <batch_name>.zip
cd <batch_name>
bash submit_all.sh
```

Monitor with:

```bash
squeue -u $USER
sacct -j <jobid> --format=JobID,JobName,Partition,State,Elapsed,ExitCode
tail -f slurm-<jobid>.out
```

## O2 Notes

- Generated server scripts resolve the repo root at runtime.
- For long-seq hybrid jobs on O2, set:

```bash
export ORTHOSEQ_MP_START=spawn
```

Without `spawn`, hybrid off-target matrix computation can hang during worker
startup on O2.

- Do not `git pull` into a checkout that active jobs are using.
- Uploaded zip files, `__MACOSX/`, and Slurm logs are ignored under
  `scripts/benchmarking/.gitignore`.
