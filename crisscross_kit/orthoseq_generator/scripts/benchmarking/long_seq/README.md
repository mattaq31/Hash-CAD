# Long-Seq Benchmark Workflow

This folder contains the live long-sequence benchmark workflow.

## Files

- `configs/templates/`
  Example batch inputs for the preparation step.
- `scripts/prepare_conditions.py`
  Generates calibrated benchmark conditions and matching `sbatch` scripts.
- `scripts/run_long_seq_naive_search.py`
  Runs one naive live benchmark condition from one generated TOML.
- `scripts/run_long_seq_hybrid_search.py`
  Runs one hybrid live benchmark condition from one generated TOML.

## Preparation

Run locally from the repo root:

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/prepare_conditions.py \
  --config crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/templates/<prep_config>.toml
```

This writes a generated batch folder under:

```text
crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated/
```

Each family folder contains:

- `condition_fb*_budget*_init*.toml`
- matching `naive_*.sh` / `hybrid_*.sh`

The batch root also contains:

- `batch_summary.toml`
- `submit_all.sh`

The generated condition TOMLs are shared by both algorithms, so `naive` and
`hybrid` are run under the same physical thresholds and compute budget.

## O2 Workflow

The supported O2 workflow is:

1. generate the batch locally
2. zip the generated batch folder
3. upload the zip into the server repo under `configs/generated/`
4. unzip on O2
5. submit with `bash submit_all.sh`

### 1. Generate locally

From the repo root:

```bash
python3 crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/prepare_conditions.py \
  --config crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/templates/<prep_config>.toml
```

This writes a batch folder under:

```text
crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated/
```

### 2. Upload the generated batch

Zip the generated batch folder locally and upload the zip into:

```text
$HOME/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated/
```

### 3. Unzip on O2

On O2:

```bash
cd $HOME/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated
unzip <batch_name>.zip
```

After unpacking, the batch folder should contain:

- `submit_all.sh`
- `batch_summary.toml`
- one family folder per generated condition group

### 4. Submit the jobs

Submit the whole batch:

```bash
cd $HOME/Hash-CAD/crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/configs/generated/<batch_name>
bash submit_all.sh
```

Or submit one generated script directly:

```bash
sbatch len20_5p_TTTT_3p_none_sigma1p0_seed41/hybrid_fb0p05.sh
```

### 5. Monitor the jobs

```bash
squeue -u $USER
sacct -j <jobid> --format=JobID,JobName,Partition,State,Elapsed,ExitCode
tail -f slurm-<jobid>.out
```

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

## O2 Technical Details

- Generated server scripts resolve the repo root at runtime. They do not rely
  on the current shell directory.
- Long-seq hybrid jobs on O2 should set:

```bash
export ORTHOSEQ_MP_START=spawn
```

This is an important server-side detail. Without `spawn`, the hybrid
off-target matrix computation can hang during worker startup on O2.

- Current practical server settings for the benchmark campaign are:
  - shared server env in `[server]`
  - naive resources in `[server_naive]`
  - hybrid resources in `[server_hybrid]`
  - `partition = "medium"`
  - `total_nupack_budgets = [5_000_000]` (swept as list)

- The example prep config is the canonical place to change these defaults.
- Do not `git pull` into a checkout that active jobs are using.
- Uploaded zip files, `__MACOSX/`, and Slurm log files are ignored under
  `scripts/benchmarking/.gitignore`.

## Outputs

Generated condition TOMLs now embed a benchmark-specific output directory under
`data/<batch_name>_sigma..._seed.../`. For example, a prep config with:

```toml
[prep]
name = "long_batch_v"
range_sigma = 1.0
```

and `random_seed = 41` will write results under:

```text
data/long_batch_v_sigma1p0_seed41/
```

with the usual `len*/5p_*` family subfolders beneath that root.

## Benchmark Objective

The benchmark compares the `naive` and `hybrid` search algorithms under the
same thermodynamic constraints and the same NUPACK compute budget.

The primary metric is the number of orthogonal sequence pairs found before the
budget is exhausted. The purpose is to see whether, and under which parameter
settings, the hybrid method outperforms the naive greedy baseline.

## How the Scripts Tie Together

The workflow has two stages:

1. preparation of benchmark conditions
2. execution of those conditions with two different search algorithms

The main files are:

- `configs/templates/prep_config.t.toml`
- `scripts/prepare_conditions.py`
- `scripts/run_long_seq_naive_search.py`
- `scripts/run_long_seq_hybrid_search.py`

## Shared Benchmark Inputs

The batch config you choose from `configs/templates/` defines:

- sequence families to benchmark
- NUPACK chemistry settings
- calibration settings for the on-target window
- physically interpreted off-target and self-structure targets
- total compute budgets (list, swept combinatorially)
- algorithm-specific runtime parameters (including `initial_fresh_pair_counts` as a swept list)
- O2 submission settings
- optional algorithm-specific server resource overrides

The exact values in that file are examples and may change over time.

The preparation script generates conditions as a full combinatorial sweep over
`offtarget_target_bound_fractions`, `total_nupack_budgets`, and
`initial_fresh_pair_counts`. Each combination produces its own condition TOML
and matching server scripts.

One detail that matters for interpretation is that
`offtarget_target_bound_fractions` is expressed as a fraction, not a percent.
For example, values `0.01` and `0.05` would mean 1% and 5% bound off-target
complex at the configured strand concentration.

## Candidate Sequence Generation

Candidate pairs are produced by `SequencePairRegistry` in
`orthoseq_generator/sequence_generation.py`.

For a given family, it:

- samples a random DNA core of fixed length
- builds the reverse complement
- adds the configured 5' and 3' flanks
- rejects candidates containing forbidden substrings
- assigns each unique pair a stable integer ID

This registry is used both during condition preparation and during the live
search runs.

## Preparation Details

`scripts/prepare_conditions.py` generates the benchmark conditions. It does not
run the search itself.

For each `(length, 5' extension, 3' extension)` family, it:

1. builds a live `SequencePairRegistry`
2. samples many unique valid pairs
3. computes on-target energies for those samples
4. estimates the on-target energy distribution
5. derives physical energy thresholds
6. writes one condition TOML per off-target setting
7. writes one `sbatch` wrapper for `naive` and one for `hybrid`
8. writes a `batch_summary.toml` and `submit_all.sh`

### On-Target Window

The on-target window is intentionally one-sided.

For each family:

- `max_ontarget = sampled_mean`
- `min_ontarget = sampled_mean - range_sigma * sampled_std`

So a candidate is accepted only if its on-target energy lies between the mean
and a lower bound defined by the chosen sigma rule.

### Off-Target Cutoff

The off-target cutoff is derived from a physical binding model.

The prep script numerically inverts a two-strand equilibrium relation to turn a
target bound fraction at the configured concentration and temperature into an
association free-energy cutoff. That derived cutoff is written as
`offtarget_limit` into each condition TOML.

This is what makes the benchmark experimentally meaningful: the off-target
constraint is expressed in terms of physically interpretable binding behavior,
not only as an abstract energy threshold.

### Self-Energy Cutoff

The self-structure limit is derived from a target unpaired fraction.

With `self_target_unpaired_fraction = 0.2`, the prep script computes the
free-energy threshold corresponding to requiring at least 20% unpaired
population and writes that value as `self_energy_limit`.

## Generated Condition Files

Each generated condition TOML contains:

- shared run parameters
- shared NUPACK settings
- the derived `min_ontarget` / `max_ontarget`
- the derived `offtarget_limit`
- the derived `self_energy_limit`
- the total NUPACK budget
- the naive runtime settings
- the hybrid runtime settings

Both runners consume the same condition file. This is important because it
means the algorithms are compared under matched physics and matched budget.

## Server Resource Blocks

The prep config supports three server blocks:

- `[server]`
  Shared environment settings and default Slurm fields used by both wrappers.
- `[server_naive]`
  Optional overrides for the generated naive `sbatch` scripts.
- `[server_hybrid]`
  Optional overrides for the generated hybrid `sbatch` scripts.

The generator merges them as:

- naive wrapper: `{**server, **server_naive}`
- hybrid wrapper: `{**server, **server_hybrid}`

This means you can keep shared fields such as `module_load`, `conda_env`,
`partition`, `email`, and `mp_start` in `[server]`, then set different `cpus`,
`memory`, and `time` values per algorithm. Older configs with only `[server]`
still work.

## Naive Runtime Controls

The long-seq naive runner reads these fields from the `[naive]` block:

- `progress_every`
  Attempt-based progress cadence. The existing `Naive progress: ...` line is
  considered every `progress_every` attempts.
- `min_progress_interval_s`
  Minimum wall-clock interval between those progress lines. This throttles log
  spam during duplicate-heavy phases without changing the progress-line text.
- `duplicate_streak_limit`
  Benchmark-only stop condition for live naive search. The runner counts
  consecutive sampled `pair_id`s that were already present in its local
  `tested_pair_ids` set. The counter resets whenever a new unique `pair_id` is
  found. If the streak reaches `duplicate_streak_limit`, the run stops and the
  stop reason is recorded in the report metadata as
  `duplicate_streak_limit_reached=<value>`.

This stop rule is local to the naive benchmark loop. It does not change the
underlying `SequencePairRegistry` behavior.

## Algorithm Roles

The benchmark compares two search strategies under the same generated
condition:

- `naive`: a greedy baseline that accepts valid sequence pairs incrementally
- `hybrid`: a two-pass strategy. Pass 1 collects a seed pool filtered by
  on-target and self-energy, then runs vertex cover to resolve conflicts.
  Pass 2 collects additional candidates cross-referenced against the seed
  survivors (zero allowed violations guarantees compatibility), then runs
  vertex cover on fresh candidates only and unions survivors into the
  retained set.

The important benchmark property is that both runners consume the same
generated condition TOML, so they are compared under matched thresholds,
chemistry, and compute budget.

### Hybrid Runtime Controls

The hybrid runner reads these fields from the `[hybrid]` block:

- `initial_fresh_pair_counts` (list, swept)
  Number of candidate pairs collected in pass 1 before the first vertex-cover
  run. Each value in the list produces a separate condition.
- `prune_fraction`
  Fraction of vertices perturbed per vertex-cover refinement iteration.
- `vc_max_iterations`
  Maximum iterations for each vertex-cover refinement run.
- `progress_report_interval_min` (optional)
  When set, pass 2 collection is chunked into timed intervals. At each
  boundary a peek vertex cover estimates the current total without committing.
  Integer minutes, minimum 30 s enforced. Omit to disable.

## Reporting

After either runner finishes, it:

- writes an XLSX report
- writes the standard plots
- writes the outputs under `data/`

The XLSX report contains a `search_progress` sheet with per-pass statistics:

| Column | Meaning |
|--------|---------|
| `pass` | `"seed"` or `"collection"` |
| `pairs_collected` | Candidates that passed all filters |
| `pairs_after_vc` | Survivors after vertex cover |
| `total_retained` | Cumulative orthogonal set size |
| `nupack_calls_executed` | NUPACK calls for this pass only (collection + VC) |
| `stopped_early` | Whether a stop condition fired before natural completion |
| `attempts` | Total candidates evaluated (including rejected) |
| `passed_ontarget_and_self` | Candidates that passed energy + self-energy filters |
| `accepted` | Candidates that also passed cross-referencing (= `pairs_collected`) |

## What the Benchmark Is Measuring

The benchmark is asking:

Given the same physical acceptance criteria and the same compute budget, which
algorithm finds more valid orthogonal sequence pairs?

That comparison is repeated across the configured parameter sweep to identify
where the hybrid strategy begins to outperform the naive baseline.
