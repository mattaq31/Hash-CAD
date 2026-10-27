# OrthoSeq Benchmark Data

This archive contains the benchmark data associated with the OrthoSeq
manuscript, "OrthoSeq: A Design Workflow for Thermodynamically Orthogonal DNA Sequence-Pair Libraries."

The most directly reusable files are in `extracted_libraries/`. These are
ready-to-use Excel workbooks containing the largest orthogonal sequence-pair
libraries found for each reported benchmark condition. The archive also
contains the full benchmark outputs used to derive those libraries and the
workbooks used for the seqwalk, nuad, and polycube comparisons.

## Archive Scope

If you want sequences to copy into a design workflow, start with
`extracted_libraries/`. The full benchmark outputs are included for provenance
and detailed analysis.

The benchmark data are organized into two benchmark regimes.

- `short_seq/` contains the short-sequence benchmark for core binding-domain
  lengths 4, 5, 6, and 7 nt. In this regime, finite frozen candidate datasets
  were generated in advance and all benchmark algorithms were run on the same
  saved dataset bundles.
- `long_seq/` contains the long-sequence benchmark for core binding-domain
  lengths 8, 9, 10, 12, 14, 16, 18, 20, and 25 nt. In this regime, benchmark
  conditions were generated from preparation TOML files and the naive and
  hybrid searches were run live under a fixed NUPACK-call budget.

The extracted sequence libraries are reduced workbooks derived from the full
benchmark outputs. For each reported condition, the extracted workbook comes
from the run that produced the largest final orthogonal sequence-pair library,
measured by the number of rows in `found_pairs`.


## Archive Layout

The archive is organized as follows:

```text
benchmark_data/
  README.md
  extracted_libraries/
    short_seq/
      37C/
        TTTT_flank/
        no_flank/
    long_seq/
      25C/
        TTTT_flank/
        no_flank/
      37C/
        TTTT_flank/
        no_flank/
  full_benchmark_results/
    short_seq/
      data/
        len4_7_tttt5p_noGGGG/
          benchmark_summary_benchmark_x.toml
          benchmark_summary_benchmark_x_review_seed1.toml
          benchmark_summary_benchmark_x_review_seed2.toml
          benchmark_summary_benchmark_x_review_seed3.toml
          benchmark_summary_benchmark_x_review_seed4.toml
          benchmark_summary_benchmark_x_review_seed5.toml
          len4/
          len4_tttt5p/
          len5/
          len5_tttt5p/
          len6/
          len6_tttt5p/
          len7/
          len7_tttt5p/
    long_seq/
      configs/
        generated/
          batch_x_TTTT_sigma1p0_seed41/
          batch_x______sigma1p0_seed41/
          batch_x25TTTT_sigma1p0_seed41/
          batch_x25_____sigma1p0_seed41/
          batch_x_TTTT_sigma0p5_seed41/
          batch_x______sigma0p5_seed41/
      data/
        batch_x_TTTT_sigma1p0_seed41/
        batch_x______sigma1p0_seed41/
        batch_x25TTTT_sigma1p0_seed41/
        batch_x25_____sigma1p0_seed41/
        batch_x_TTTT_sigma0p5_seed41/
        batch_x______sigma0p5_seed41/
      gmin_gmax_comparison/
        input_reports.tsv
        results/
          gmin_gmax_37C/
  seqwalk_comparison/
    figure5_seqwalk_max_orthogonality_len16_n72_seed42.xlsx
    figure5_hybrid_len16_noflank_seqwalk_k6_seed42.xlsx
    figure5_search_only_hybrid_len16_noflank_init450.xlsx
  nuad_comparison/
    results/
      6mer/
        nuad.xlsx
        orthoseq.xlsx
        raw_nuad/
      12mer_wide/
        nuad.xlsx
        orthoseq.xlsx
        raw_nuad/
      12mer_narrow/
        nuad.xlsx
        orthoseq.xlsx
        raw_nuad/
      20mer_Na1M_Mg0M/
        nuad.xlsx
        orthoseq.xlsx
        naive.xlsx
        raw_nuad/
  polycube_comparison/
    data/
      published_polycube_sequences.xlsx
      polycube_association_energies.xlsx
      polycube_complex_energies.xlsx
      orthoseq_polycube_search.xlsx
      orthoseq_polycube_complex_energies.xlsx
```


## Short-Sequence Benchmark Data

### Overview

The short-sequence benchmark covers core binding-domain lengths 4-7 nt, with
and without a 5' TTTT extension. In this regime the full conflict graph could
be constructed, so naive search, graph-aware search, and hybrid search were
all compared on the same frozen candidate pools.

The GMIN and weaker-first naive comparison uses the same datasets. Its new
reports are saved under `results/benchmark_x_review/` alongside the original
`results/benchmark_x/` reports. Each candidate dataset is included once.

### Dataset Bundles

Each short-sequence dataset directory contains:

- `dataset.toml`: human-readable metadata describing the frozen dataset
- `dataset.npz`: compressed NumPy arrays containing the candidate pool and the
  cached off-target energy matrices
- `results/<benchmark_name>/`: benchmark workbooks generated from that dataset

Each `dataset.npz` file contains:

- `all_global_pair_ids`: canonical integer IDs for all sequence pairs in the
  full candidate pool
- `all_seqs`: forward strand sequence for each full-pool candidate
- `all_rc_seqs`: intended binding partner for each full-pool candidate
- `all_on_target_energies`: on-target association free energy for each full
  candidate pair
- `all_self_energy_seqs`: self-folding free energy of the forward strand for
  each full candidate pair
- `all_self_energy_rc_seqs`: self-folding free energy of the reverse-complement
  strand for each full candidate pair
- `all_is_in_ontarget_window`: Boolean mask indicating whether the candidate
  passed the on-target energy window used to define the matrix subset
- `matrix_global_pair_ids`: canonical IDs of the subset of candidates that
  passed the on-target filter and therefore appear in the cached off-target
  matrices
- `handle_handle_energies`: matrix of forward-strand versus forward-strand
  off-target energies for the matrix subset
- `handle_antihandle_energies`: matrix of forward-strand versus reverse-complement
  off-target energies for the matrix subset
- `antihandle_antihandle_energies`: matrix of reverse-complement versus
  reverse-complement off-target energies for the matrix subset

The indexing convention is:

- row or column `i` in the cached matrices corresponds to
  `matrix_global_pair_ids[i]`
- `handle_handle_energies[i,j]` is the interaction between `seq_i` and `seq_j`
- `handle_antihandle_energies[i,j]` is the interaction between `seq_i` and
  `rc_seq_j`
- `antihandle_antihandle_energies[i,j]` is the interaction between `rc_seq_i`
  and `rc_seq_j`

Two sequence pairs are treated as incompatible when any relevant off-target
interaction falls below the chosen off-target energy cutoff. In the short-seq
benchmark code this conflict rule is evaluated using the four values
`hh[i,j]`, `ahah[i,j]`, `hah[i,j]`, and `hah[j,i]`.

The corresponding `dataset.toml` file records the same indexing conventions in
plain text and also stores the dataset inputs, NUPACK conditions, and derived
statistics used to build the frozen benchmark dataset.

### Batch Summary

The file `benchmark_summary_benchmark_x.toml` summarizes the benchmark sweep
across all short-sequence datasets. It records, for each run, the dataset
name, algorithm, random seed, target conflict density, selected off-target
cutoff, and the number of sequence pairs found.

The five `benchmark_summary_benchmark_x_review_seed*.toml` files summarize
the GMIN and weaker-first naive runs for seeds 1-5.


## Long-Sequence Benchmark Data

### Overview

The long-sequence benchmark covers core binding-domain lengths 8, 9, 10, 12,
14, 16, 18, 20, and 25 nt, with and without a 5' TTTT extension. In this
regime full conflict-graph construction was no longer practical, so naive and
hybrid search were compared under a fixed budget of 10 million NUPACK calls.

The main manuscript benchmark uses the 37 C datasets. The 25 C benchmark is a
lower-temperature repeat reported in the Supporting Information.

The 37 C sigma-0.5 batches cover lengths 8, 12, 16, and 20 nt, with and
without a 5' TTTT extension. Their on-target window is [mean - 0.5 SD, mean],
compared with [mean - SD, mean] in the sigma-1.0 batches.

Some 37 C long-sequence runs request `search.initial_fresh_pair_count = 2500`.
In practice, the fixed 10-million-NUPACK-call budget was exhausted during the
initial graph-aware search after approximately 2235 sequence pairs. These runs
are included in extracted libraries only when they produce the largest final
`found_pairs` count for that condition.

### Generated Benchmark Conditions

The folder `configs/generated/` contains the parameter files used to define
the long-sequence benchmark runs.

Each generated batch folder contains:

- `batch_summary.toml`: summary of the benchmark family and all derived
  conditions
- one condition TOML per run
- one job wrapper script per run
- `submit_all.sh`

These generated TOMLs document how the benchmark runs were set up. They are
inputs, not results.

### Run Output Folders

Each long-sequence batch under `data/` contains one subfolder per sequence
length and flank condition. Each run writes:

- one full XLSX workbook
- one on-target/off-target PDF
- one self-folding PDF

The XLSX workbook is the primary machine-readable result artifact.


## Long-Sequence Heuristic Comparison

`full_benchmark_results/long_seq/gmin_gmax_comparison/` contains 18 workbooks,
one per length and extension condition. Each contains 360 run records for
initial pools of 250, 450, and 900 pairs, 12 GMIN/GMAX variants, and 10 seeds.
The variants combine random, rank, or rule tie-breaking with bare or iterative
selection on the same saved initial graphs.

`input_reports.tsv` links each comparison workbook and initial pool size to
its original benchmark report. Both path columns are relative to `benchmark_data/`.
The retained pair IDs refer to `global_pair_id` in the input report's
`seed_pass_pairs` sheet; the corresponding energies are saved in `seed_hh`,
`seed_hah`, and `seed_ahah`. Each comparison workbook also contains summary
statistics and its configuration.


## Ready-to-Use Extracted Sequence Libraries

The `extracted_libraries/` portion of the archive contains ready-to-use Excel
workbooks. These are the reduced sequence libraries intended for direct
inspection and copying.

For each reported condition, the workbook was selected from the benchmark run
that produced the largest final orthogonal sequence-pair library, measured by
the number of rows in `found_pairs`. Each reduced workbook contains only:

- `run_metadata`
- `found_pairs`

For short-sequence benchmarks, extracted libraries are grouped by:

- temperature
- flank condition
- conflict probability
- core binding-domain length

Short-sequence selection compares the original runs with the new GMIN and
weaker-first naive runs.

For long-sequence benchmarks, extracted libraries are grouped by:

- temperature
- flank condition
- core binding-domain length

For each long-sequence temperature, flank condition, and length, selection
compares all available sigma-1.0 and sigma-0.5 runs. The selected workbook's
`run_metadata` records its on-target window in `search.min_ontarget` and
`search.max_ontarget`.


## seqwalk Comparison

The folder `seqwalk_comparison/` contains the three datasets used for the
Figure 5 comparison between thermodynamic search and seqwalk-derived sequence
libraries.

It contains:

- `figure5_seqwalk_max_orthogonality_len16_n72_seed42.xlsx`
  - the seqwalk-only comparison arm used for Figure 5A
  - 16-nt barcodes generated with seqwalk in max-orthogonality mode
- `figure5_search_only_hybrid_len16_noflank_init450.xlsx`
  - the benchmark-derived comparison arm used for Figure 5B
  - a copy of the canonical long-sequence benchmark workbook for the 16-nt,
    no-flank, hybrid-search condition with initial subset size 450
- `figure5_hybrid_len16_noflank_seqwalk_k6_seed42.xlsx`
  - the seqwalk + thermodynamic postfilter comparison arm used for Figure 5C
  - a seqwalk-derived 16-nt candidate pool filtered with the hybrid-search
    workflow under the thermodynamic criteria described in the manuscript

The Figure 5B workbook is duplicated here for convenience so that all three
comparison arms can be inspected from a single folder.


## nuad Comparison

`nuad_comparison/results/` contains four cases: 6-mer with 41 pairs,
12-mer with 120 pairs using the original on-target window, and 12-mer with
129 pairs using the narrower window, plus 20-mer with 897 pairs at 1 M sodium
and zero magnesium. Each case contains `nuad.xlsx`, the
matching OrthoSeq benchmark report copied as `orthoseq.xlsx`, and native nuad
designs, sequences, reports, random states, and logs in `raw_nuad/`.
The nuad workbooks preserve the complete libraries, verified energies,
validation results, and individual constraint violations.

The 20-mer case also contains `naive.xlsx`, a verified 876-pair naive-search
library. Hybrid search produced 897 valid pairs; nuad retained 897 pairs with
2,203 individual constraint violations. All three use a nominal search budget
of 10 million association evaluations, 37 °C, no extensions, GGGG/CCCC exclusions,
an on-target window of [-25.25, -24.00] kcal/mol, an off-target minimum of -11.40
kcal/mol, and a self-folding minimum of -1.40 kcal/mol. Seed and executed
evaluation counts are recorded in each workbook.


## Polycube Comparison

`polycube_comparison/data/` contains five workbooks:

- `published_polycube_sequences.xlsx`: 96 published sequence pairs and extraction
  provenance from Diep et al. (DOI: 10.26434/chemrxiv-2025-qbk3f).
- `polycube_association_energies.xlsx` and `polycube_complex_energies.xlsx`:
  our energy evaluations of the published library.
- `orthoseq_polycube_search.xlsx`: the complete 100-pair OrthoSeq search report,
  including association energies.
- `orthoseq_polycube_complex_energies.xlsx`: our complex-energy evaluation of
  the same OrthoSeq library.

Both libraries use 9-nt cores with 5' T12 extensions.
Association energies (`G_AB - G_A - G_B`) support the binding-energy comparison;
complex free energies (`G_AB`) are used to calculate specificity gaps.


## Workbook Schema

### Full Benchmark Workbooks

Full benchmark workbooks typically contain the following sheets:

- `run_metadata`
- `found_pairs`
- `selected_hh`
- `selected_hah`
- `selected_ahah`
- `search_progress`
- `validation`

Hybrid long-sequence workbooks additionally contain:

- `seed_pass_pairs`
- `seed_hh`
- `seed_hah`
- `seed_ahah`

### Reduced Extracted Workbooks

Reduced extracted workbooks contain only:

- `run_metadata`
- `found_pairs`


## Metadata and Terminology

Earlier versions of OrthoSeq used shorter algorithm labels, such as `vertex_cover` and `hybrid_search`.
The archive retains these labels in existing reports and also includes more explicit names that identify
the heuristic and variant. The definitions below explain both naming formats:

| Saved label | Meaning in the manuscript |
| --- | --- |
| `vertex_cover` | Graph-aware search using GMAX with rule-based tie-breaking and iterative improvement. |
| `vertex_cover_GMIN` | Graph-aware search using GMIN with rule-based tie-breaking and iterative improvement. |
| `hybrid_offline`, `hybrid_search` | Hybrid search using precomputed energies and energies calculated during the search, respectively. Both use GMAX with rule-based tie-breaking. |
| `naive`, `naive_search`, `naive_rand*` | Naive search with random candidate ordering. |
| `naive_ordered`, `naive_rank*` | Naive search with weaker-first candidate ordering based on on-target binding energy. |

Labels such as `vertex_cover_GMIN_rule_offline` encode the choices explicitly.
In graph-search labels, `GMAX` and `GMIN` identify maximum-degree deletion and minimum-degree selection, while
`rand`, `rank`, and `rule` identify random, on-target-energy-based, and rule-based tie-breaking. The `_bare` suffix
indicates no iterative improvement, and `_offline` indicates use of precomputed energies. In the long-sequence
heuristic comparison, labels such as `gmax_rule` and `gmax_rule_iterative` distinguish bare and iteratively
improved variants. Asterisks in the table indicate variable suffixes.

Some long-sequence reports retain a hybrid-workflow label even when the budget was exhausted during the initial
graph-search stage. The approximately 2235-pair initial-graph conditions are reported as graph-aware search in
the manuscript.

Parameter names also differ:

- `offtarget_limit`: off-target association free-energy limit
- `initial_fresh_pair_count`: requested initial graph-aware search subset size
- `vc_max_iterations`: maximum number of iterative-improvement steps
- `prune_fraction`: perturbation fraction

The workbook metadata keys are grouped by prefix:

- `input.*`: sequence-design inputs such as core binding-domain length, 5' and
  3' flanks, motif exclusions, and whether the run started from a frozen
  benchmark dataset or a live on-the-fly registry
- `search.*`: search thresholds and algorithm settings, including the
  off-target cutoff, on-target window, self-folding cutoff, random seed,
  executed NUPACK calls, NUPACK-call budget, graph-search parameters, and
  search duration
- `nupack.*`: thermodynamic model parameters used for energy computation,
  including material, temperature, sodium concentration, and magnesium
  concentration
- `dataset.*`: properties of the frozen short-sequence dataset, including the
  sigma rule used to define the on-target window, the number of total
  candidates, the number of candidates in the cached matrix subset, and the
  on-target energy statistics of the frozen pool
- `artifact.*`: provenance paths pointing to the original dataset or config
  files used when the report was written

The most useful metadata fields for reading the benchmark outputs are:

- `algorithm_name`: implementation-facing algorithm label used by the code
- `benchmark_name`: benchmark family label written into the report
- `found_pair_count`: number of final selected sequence pairs in the workbook
- `verified_with_direct_nupack`: indicates that the final reported energies
  were recomputed directly for the selected set rather than copied only from
  cached search-time data
- `search.offtarget_limit`: off-target energy cutoff used to define conflicts
- `search.min_ontarget` and `search.max_ontarget`: accepted on-target energy
  window
- `search.self_energy_limit`: minimum allowed self-folding free energy
- `search.total_nupack_calls`: number of NUPACK calls actually consumed during
  the reported run
- `search.total_nupack_budget`: NUPACK-call budget assigned to the run
- `search.initial_fresh_pair_count`: hybrid-search seed-set size used in the
  first graph-aware phase
- `search.prune_fraction`: fraction of vertices removed during each graph-aware
  refinement perturbation step
- `search.vc_max_iterations`: maximum number of graph-aware refinement
  iterations
- `stopped_reason`: reason the search terminated, for example exhaustion of
  the pool or exhaustion of the NUPACK-call budget
- `dataset.virtual_nupack_budget`: reconstructed conceptual NUPACK cost of
  building the frozen short-sequence dataset, used to compare offline and live
  benchmark workflows on a common scale

The `artifact.*` paths may contain absolute paths from the machine on which
the benchmark was originally run. They are kept as provenance records. They
are not needed to interpret the archive contents.


## Relevant Source Files

The benchmark format is defined by the code in the repository. The most
relevant files for interpreting the archive are:

- `scripts/benchmarking/short_seq/benchmark_dataset_tools.py`: defines the
  frozen short-sequence dataset format, including the meaning of the
  `dataset.npz` arrays and the `dataset.toml` indexing conventions
- `scripts/benchmarking/short_seq/benchmark_analysis.py`: defines how
  off-target matrices are converted into conflict graphs and how conflict
  density is computed
- `scripts/benchmarking/short_seq/benchmark_algorithms.py`: defines how
  short-sequence benchmark reports are assembled from frozen datasets and how
  dataset-level metadata are propagated into the workbook reports
- `search_reporting.py`: defines the canonical Excel workbook schema and the
  shared `run_metadata` key set used across benchmark and live-search outputs
- `scripts/benchmarking/long_seq/scripts/prepare_conditions.py`: defines the
  generated long-sequence condition TOMLs and batch summaries
- `scripts/benchmarking/long_seq/scripts/run_long_seq_naive_search.py` and
  `scripts/benchmarking/long_seq/scripts/run_long_seq_hybrid_search.py`:
  define how the live long-sequence benchmark outputs are written


## Naming Conventions

### Short-Sequence Datasets

Short-sequence dataset folders such as `len6_tttt5p` indicate:

- `len6`: core binding-domain length of 6 nucleotides
- `tttt5p`: presence of a 5' `TTTT` extension

### Long-Sequence Batches

Long-sequence batch names such as `batch_x_TTTT_sigma1p0_seed41` indicate:

- benchmark family name
- flank condition
- sigma rule used to define the on-target window
- random seed used during preparation

### Extracted Library Filenames

Examples:

- `len6_37C_TTTT_confprob_0p2.xlsx`
- `len16_25C_noflank.xlsx`

These names encode the sequence length, temperature, flank condition, and, for
short-sequence libraries, the target conflict-probability level.


## Relation to the Manuscript

This archive supports the benchmark figures and the reported extracted
libraries in the manuscript and Supporting Information.

- The short-sequence data support the full-conflict-graph benchmark in Figure 4A.
- The 37 C sigma-1.0 long-sequence data support the fixed-budget benchmark in Figure 4B.
- The 25 C repeat and 37 C sigma-0.5 batches support the temperature and on-target-window analyses
  in the Supporting Information.
- The additional short-sequence runs and long-sequence GMIN/GMAX comparison support the graph-search
  heuristic and candidate-ranking analyses in the Supporting Information.
- The `seqwalk_comparison/` folder contains the three workbooks used for the
  Figure 5 comparison with seqwalk.
- The `nuad_comparison/` files support the 6-mer, 12-mer, and 20-mer comparisons discussed in the main text
  and detailed in the Supporting Information.
- The `polycube_comparison/` workbooks support the comparison with the published polycube sticky-end library
  in the Supporting Information.


## Notes

- The full benchmark results preserve the complete reporting schema used by
  the codebase.
- The extracted libraries are reduced convenience files for direct use in the
  Supporting Information and for quick inspection of the final selected
  sequence pairs.

## Funding and Compute Resources

This dataset is associated with work supported in part by:

- the German Research Foundation (Deutsche Forschungsgemeinschaft, DFG)
  Walter Benjamin Programme, project `553862611`
- the Dana-Farber Cancer Institute Claudia Adams Barr Program for Cancer
  Research
- the Korea-US Collaborative Research Fund (KUCRF), grant
  `RS-2024-00468463`

The O2 High Performance Compute Cluster, supported by the Research Computing
Group at Harvard Medical School, was used to accelerate development of the
evolutionary algorithm and the final large-scale parameter sweeps.
