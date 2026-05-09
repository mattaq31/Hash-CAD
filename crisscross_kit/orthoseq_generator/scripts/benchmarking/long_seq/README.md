# Long-Seq Benchmark Workflow

This folder contains the live long-sequence benchmark workflow.

## Files

- `configs/templates/prep_config.example.toml`
  Batch input for the preparation step.
- `scripts/prepare_conditions.py`
  Samples live pairs, derives the on-target window and physical cutoffs, and
  writes generated condition TOMLs plus matching `sbatch` scripts.
- `scripts/run_long_seq_naive_search.py`
  Runs one naive live benchmark condition from one generated TOML.
- `scripts/run_long_seq_hybrid_search.py`
  Runs one hybrid live benchmark condition from one generated TOML.

## Preparation

Run locally from the repo root:

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/prepare_conditions.py \
  --config crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/templates/prep_config.example.toml
```

This writes a generated batch folder under:

```text
crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated/
```

Each family folder contains:

- `condition_fb*.toml`
- matching `naive_*.sh` / `hybrid_*.sh`

The batch root also contains:

- `batch_summary.toml`
- `submit_all.sh`

## Local Test

Run one generated condition directly:

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/run_long_seq_naive_search.py \
  --config path/to/condition_fb0p05.toml
```

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/run_long_seq_hybrid_search.py \
  --config path/to/condition_fb0p05.toml
```

## Server Use

Upload the generated batch folder to the server, then either:

- submit one job:

```bash
sbatch path/to/naive_fb0p05.sh
```

- or submit the whole batch:

```bash
bash path/to/submit_all.sh
```

Outputs are written under `data/`.
