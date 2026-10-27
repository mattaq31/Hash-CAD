# nuad comparison

Four fixed-size feasibility comparisons with saved OrthoSeq libraries. The completed searches are retained;
plotting uses their independently verified, standard repository Excel reports. No further searches are required
to reproduce the figures.

## Files and execution

```text
nuad_functions.py          nuad constraints, budget control, and repository verification/reporting
comparison_functions.py    standard report readers and the comparison figure
run/run_6mer.py             41 pairs, 6 nt, reconstructed dataset budget
run/run_12mer_wide.py       120 pairs, 12 nt, sigma-1.0 reference window
run/run_12mer_narrow.py     129 pairs, 12 nt, sigma-0.5 reference window
run/run_20mer.py            897 pairs, 20 nt, 1 M sodium and zero magnesium
run/plot_comparisons.py     regenerate the four figures with their embedded tables
results/<case>/nuad.xlsx    canonical benchmark data and metadata
results/<case>/raw_nuad/    original nuad reports, designs, RNG checkpoints, and search logs
plots/<case>_comparison.pdf final PDF figures
```

Run `run/plot_comparisons.py` directly in PyCharm, or from this directory:

```bash
/opt/miniconda3/envs/orthoseq-nuad/bin/python run/plot_comparisons.py
```

Plotting reads Excel reports and makes no NUPACK calculations. The reference OrthoSeq paths are stored in
`source.reference_report` in each workbook. References remain in the existing benchmark directories.

To repeat a search, run the corresponding `run/run_*.py` file in PyCharm. Its main block contains the reference
path, random seed, association budget, and output directory. Length, target pair count, energy limits, salts,
temperature, and motifs are loaded from that reference report. New searches create timestamped directories
and never overwrite the retained cases. To plot a new run, change the report paths in `run/plot_comparisons.py`.

## Environment

The retained runs used `/opt/miniconda3/envs/orthoseq-nuad/bin/python`, Python 3.12.13, nuad 0.6 from commit
`4890b126b12c9894745742cc10eb8d62599bfa2a`, and NUPACK 4.0.2.0. The environment was cloned from the existing
`crisscross-kit` environment and nuad was installed by the user. The existing licensed NUPACK installation was
reused. NUPACK is obtained separately from its distributor and is not supplied with nuad.

Use this interpreter for the `crisscross_kit` module in PyCharm. The run scripts add the existing kit and comparison
directories to Python's import path; no additional installation is needed in the configured environment.
Other required packages, already present, include NumPy, pandas, Matplotlib, and the Excel writer/reader engines.
No package installation or environment changes are performed by these scripts.

## Designs and constraints

Each pair contains a single variable core domain, X, and its automatically reverse-complementary partner, Y.
Nuad initializes the sequences from its `DomainPool`; there are no manually assigned starting sequences.
All four cases are extension-free and exclude `GGGG` and `CCCC` motifs. Both partners are checked during
final verification. The model is NUPACK `dna04.2` at 37 °C. The first three cases use 50 mM sodium and 25 mM
magnesium; the 20-mer case uses 1 M sodium and zero magnesium.

The public nuad API receives three separate constraints, all with the default weight of 1:

1. Each strand's monomer ensemble free energy must be at least the self-folding limit.
2. Each intended X/Y association energy must lie inside the reference on-target window.
3. Every unintended two-strand association energy must be at least the off-target limit.

Unintended interactions include all X/X and Y/Y combinations, X/Y between different pairs, and homodimers.
There are `2*N**2` distinct unintended complexes for N pairs, including `2*N` homodimers. Each complex is checked
once. The intended pairs are excluded from the off-target constraint.

Association energy is the ensemble quantity `G_XY - G_X - G_Y`, with the uncorrected homodimer convention used by
the reference benchmarks. Nuad's built-in association wrapper applies an additional standard-state correction;
these public custom constraints instead use the repository's `compute_nupack_energy(..., type="total")`.
The standalone monomer callback makes one direct NUPACK monomer calculation because the repository association
helper returns monomer energies together with a dimer calculation. This avoids extra association work for that
separate constraint.

Nuad's optimizer, mutation mechanism, acceptance decisions, default result caching, and scoring are unchanged.
Its installed default score transfer function cubes the positive energy excess. The score is therefore neither
an energy nor a violation count. Rounded `0.00` values in its native report do not establish zero violations.

## Cases and retained outcomes

Energy limits below are in kcal/mol. The self-folding limit is `-0.9919471230992267` in the first three cases
and `-1.40` in the 20-mer case. All four nuad searches used seed 41 and stopped at their association budgets,
without an iteration limit.

| Case | Pairs | On-target window | Off-target minimum | Association budget | Individual self / on / off violations |
|---|---:|---|---:|---:|---|
| 6mer | 41 | [-8.891639296600905, -7.784218654119501] | -6.583498094575131 | 788,298 | 0 / 3 / 11 |
| 12mer_wide | 120 | [-16.631761109666144, -14.926666779533683] | -8.160422784450315 | 10,000,000 | 8 / 15 / 25 |
| 12mer_narrow | 129 | [-15.779213944599913, -14.926666779533683] | -8.160422784450315 | 10,000,000 | 15 / 19 / 51 |
| 20mer_Na1M_Mg0M | 897 | [-25.25, -24.00] | -11.40 | 10,000,000 | 652 / 465 / 1086 |

The 20-mer result is retained in `results/20mer_Na1M_Mg0M_20261025_115004/`. Alongside `nuad.xlsx`,
`naive.xlsx` contains the independently verified 876-pair naive-search control, with zero violations, seed 41,
and the same conditions and nominal 10-million-evaluation budget as the 897-pair hybrid reference.
The naive launcher is `../../../run_naive_search.py`. Exact executed counts are saved in the workbooks.

Each saved OrthoSeq reference has zero violations under its respective criteria. The 6-mer reference is the
density-0.1 vertex-cover result with seed 2. The wide 12-mer reference is the hybrid run with initial pool 250 and
seed 41. The narrow 12-mer reference is the hybrid run with initial pool 450 and seed 41. Exact paths and original
nuad run identifiers are retained in the workbooks.

The narrower 12-mer window excludes the stronger-binding half of the original window while retaining its upper
bound. It is not a narrower interval around the same center. The prescribed library size also changes from
120 to 129 pairs, so the two cases are separate feasibility comparisons.

## Computational accounting and termination

One association-energy evaluation counts as one budget unit, whether it checks an intended pair, unintended
heterodimer, or homodimer. It corresponds to one repository helper call with one `complex_analysis` batch.
That batch contains a dimer and its two monomers, or a homodimer and its single distinct monomer. This is the
benchmark's association-evaluation unit, not a count of individual partition-function calculations.

Standalone monomer checks are recorded separately in `nuad.separate_self_folding_calls`. Monomer energies already
computed within association evaluations are not counted again in that field. Final verification is excluded
from all search counters. Nuad can reuse unchanged constraint results and reject a proposed mutation before
checking every constraint. Only evaluations that actually execute a callback increment our counters. No caching
is added by the benchmark. Constraint execution and final verification are serial, and NUPACK uses one thread.

The long-sequence budget is the saved OrthoSeq search budget of 10,000,000 association evaluations. The 6-mer budget
is the saved dataset's reconstructed full-precomputation cost: `2,040 + 2 * 627**2 = 788,298`. It combines candidate
checks and the complete graph for the 627 candidates passing the on-target window. It is not a measured counter
for the final 41-pair OrthoSeq selection. Record this distinction when reporting computational efficiency.

The budget callback stops before the next association evaluation would exceed the cap. The best improvement is
kept in memory and restored on this stop because the current proposed mutation may be unfinished. Nuad normally
returns when its constraints are satisfied. Independent repository validation determines whether the reported
design passes. The workbook is written even when violations remain.

Progress prints the latest available nuad table and counts about every ten seconds. The full table is captured
in `raw_nuad/search.log` and exported to `search_progress`. Scores in that sheet retain nuad's displayed precision.
For the historical runs, `nuad.optimization_iterations` is the number of logged iteration rows, including the
initial row if nuad printed it. Per-iteration association counts were not logged and are not reconstructed.

## Standard Excel reports and validation

The pipeline uses `build_selected_sequence_data()`, `verify_selected_pairs()`, `validate_selected_pairs()`, and
`write_hybrid_search_result_xlsx()` from the existing repository. The writer's name is historical; it serves
multiple algorithms and records these reports with `algorithm_name="nuad"`.

The standard sheets are `run_metadata`, `found_pairs`, `selected_hh`, `selected_hah`, `selected_ahah`,
`search_progress`, and `validation`. `found_pairs` contains sequence pairs and independently verified on-target
and self-folding energies. HH and AA store lower triangles including homodimers. HA stores all cross-pair
orientations; its intended-pair diagonal is unused. The existing repository readers interpret these matrices.

`constraint_violations` adds the offending strand names, energies, and positive excesses. The standard repository
validator groups off-target conflicts by pair combinations and groups self-folding checks by complementary pair.
The additional `individual_*_violations` rows count offending strands or individual complexes. Figures report
these individual counts, matching nuad's constraint granularity. Complementarity, core lengths, and motifs are
checked separately. No constraints are relaxed and no offending sequences are removed from the reported designs.

During cleanup, all three saved best designs were reverified through the repository workflow. Sequences and
every violation identity were checked against the original independent validation, followed by an Excel
read-back check. The original search budgets and statistics were preserved. Repository energy formatting is
used consistently for both libraries. Standard report energies are the source for all current figures.

## Native records and provenance

`raw_nuad/` keeps nuad's own `design_best.json`, `sequences_best.txt`, `report_best.txt`, `rng_best.json`, and logs.
`design_reported.json` preserves the exact design used for the final Excel report, in nuad's native design format.
These JSON files are checkpoints, not the benchmark's configuration or result interface.

`results/original_records.zip` is one provenance snapshot of the pre-cleanup scripts, original custom final
records, and previous PDFs. Its scripts were captured at cleanup time; it is not a version-control snapshot
proving the exact source state at the start of each historical run. Historical settings and final sequences are
preserved with their original records. Obsolete smoke tests and aborted searches are not retained as reported data.

The first three completed searches used direct raw NUPACK callbacks before this cleanup. The cleaned callbacks,
also used for the 20-mer run, reuse the repository helper. Post-run checks confirm the retained designs have
the same constraint outcomes.
The archive allows inspection of the original implementation; a bit-for-bit replay of the historical trajectory
after refactoring is not claimed.

## Interpretation

This is a four-case, single-nuad-seed feasibility comparison at prescribed N. The first three cases have similar
energy distributions with residual nuad threshold violations. The 20-mer case retains 2,203 individual nuad
violations, whereas the 897-pair hybrid and 876-pair naive libraries satisfy all constraints. These runs do not
establish general
algorithmic superiority, experimental performance differences, or nuad's inability to meet the constraints with
other seeds, settings, or budgets. Wall times are saved for provenance but are not a matched runtime benchmark.
There is no separate summary workbook: the four figures already contain the achieved-value and violation tables.
