<!-- Editable Zenodo page description, maintained separately from the README packaged inside the archive. -->

# OrthoSeq Benchmark Data

This archive contains the benchmark data associated with the manuscript “OrthoSeq: A Design Workflow for Thermodynamically Orthogonal DNA Sequence-Pair Libraries.” The most directly reusable files are in `extracted_libraries/`, which contains ready-to-use Excel workbooks with the largest orthogonal sequence-pair libraries found for each reported benchmark condition. The archive also includes the full benchmark outputs used to derive those libraries and the seqwalk, nuad, and polycube comparisons.

## Archive scope

The benchmark data are organized into two regimes:

- `short_seq/` contains benchmarks for core binding-domain lengths 4, 5, 6, and 7 nt. Finite frozen candidate datasets were generated in advance, and all algorithms were evaluated on the same saved dataset bundles.
- `long_seq/` contains benchmarks for core binding-domain lengths 8, 9, 10, 12, 14, 16, 18, 20, and 25 nt. Benchmark conditions were generated from preparation TOML files, and naive and hybrid searches were run live under a fixed budget of 10 million NUPACK calls.

Both regimes include conditions with and without a 5′ TTTT extension. The main-manuscript long-sequence benchmark uses the 37 °C datasets. A 25 °C repeat is reported in the Supporting Information.

## Archive contents

- `extracted_libraries/`: ready-to-use Excel workbooks containing the largest selected sequence libraries for each reported condition.
- `full_benchmark_results/short_seq/`: frozen short-sequence datasets, cached thermodynamic matrices, benchmark summaries, and complete result workbooks, including the GMIN and weaker-first naive comparison.
- `full_benchmark_results/long_seq/`: generated benchmark condition files and complete live-search outputs, including the 37 °C sigma-0.5 batches.
- `full_benchmark_results/long_seq/gmin_gmax_comparison/`: comparisons of graph-selection heuristics on saved initial graphs, with a mapping to the original benchmark reports.
- `seqwalk_comparison/`: the three workbooks used for the Figure 5 comparison between thermodynamic search and seqwalk-derived libraries.
- `nuad_comparison/`: four nuad comparison cases, matching OrthoSeq reports, native nuad files, and the additional 20-mer naive-search report.
- `polycube_comparison/`: five workbooks containing the published polycube sequences, our energy evaluations, and the corresponding OrthoSeq library.
- `README.md`: the detailed archive layout, dataset-array definitions, indexing conventions, workbook schema, metadata-key reference, naming conventions, and relevant source-code locations.

## Selection of extracted libraries

For each reported condition, the extracted workbook was selected from the benchmark run that produced the largest final orthogonal sequence-pair library, measured by the number of rows in `found_pairs`. These are the files to use first when selecting sequences to inspect or copy into another workflow. Each reduced workbook contains only the `run_metadata` and `found_pairs` sheets.

Short-sequence libraries are grouped by temperature, flank condition, conflict probability, and core binding-domain length. Selection includes both the original runs and the GMIN and weaker-first naive runs.

Long-sequence libraries are grouped by temperature, flank condition, and core binding-domain length. Selection compares all available sigma-1.0 and sigma-0.5 runs for each group. The selected workbook records its on-target window in `run_metadata`.

## Full benchmark workbooks

Full benchmark workbooks typically contain the following sheets:

- `run_metadata`
- `found_pairs`
- `selected_hh`
- `selected_hah`
- `selected_ahah`
- `search_progress`
- `validation`

Hybrid long-sequence workbooks additionally contain `seed_pass_pairs`, `seed_hh`, `seed_hah`, and `seed_ahah`.

## Short-sequence datasets

Each short-sequence dataset directory contains a human-readable `dataset.toml`, a compressed `dataset.npz`, and benchmark workbooks under `results/`. The NumPy archive stores the full candidate pool, canonical pair identifiers, sequences and intended partners, on-target and self-folding energies, the on-target-filter mask, and cached off-target energy matrices for the filtered matrix subset.

Matrix row or column `i` corresponds to `matrix_global_pair_ids[i]`. Two sequence pairs are treated as incompatible when any relevant off-target interaction falls below the selected off-target free-energy cutoff. The accompanying `dataset.toml` records the indexing conventions, dataset inputs, NUPACK conditions, and derived statistics in plain text.

The GMIN and weaker-first naive runs use the same frozen datasets as the original benchmark. Their reports are included under `results/benchmark_x_review/`, alongside the original `results/benchmark_x/` reports. Five additional summary TOMLs cover seeds 1–5; each candidate dataset is included only once.

## Long-sequence datasets

The `configs/generated/` folders contain the parameter files used to define the long-sequence runs, including a batch summary, one condition TOML and job wrapper per run, and `submit_all.sh`. These files are inputs rather than results.

Each run output contains one full XLSX workbook, one on-target/off-target PDF, and one self-folding PDF. The XLSX workbook is the primary machine-readable result artifact.

The 37 °C sigma-0.5 batches cover core lengths 8, 12, 16, and 20 nt, with and without a 5′ TTTT extension. Their on-target window is [mean − 0.5 SD, mean], compared with [mean − SD, mean] for the sigma-1.0 batches.

Some 37 °C long-sequence runs request `search.initial_fresh_pair_count = 2500`. In practice, the fixed 10-million-call budget was exhausted during the initial graph-aware search after approximately 2235 sequence pairs. Such a run appears in the extracted libraries only if it produced the largest final `found_pairs` count for its condition.

## Long-sequence heuristic comparison

The `full_benchmark_results/long_seq/gmin_gmax_comparison/` folder contains 18 workbooks comparing GMIN/GMAX variants on saved initial graphs. Each workbook contains 360 run records covering three initial pool sizes, 12 heuristic variants, and 10 seeds.

The accompanying `input_reports.tsv` maps each comparison workbook and initial pool size to its original benchmark report. Its paths are relative to `benchmark_data/`. The archive README explains how retained pair IDs map to the saved sequences and energy matrices.

## seqwalk comparison

The `seqwalk_comparison/` folder contains:

- `figure5_seqwalk_max_orthogonality_len16_n72_seed42.xlsx`: the seqwalk-only arm used for Figure 5A.
- `figure5_search_only_hybrid_len16_noflank_init450.xlsx`: the benchmark-derived hybrid-search arm used for Figure 5B.
- `figure5_hybrid_len16_noflank_seqwalk_k6_seed42.xlsx`: the seqwalk-derived candidate pool followed by thermodynamic hybrid-search filtering, used for Figure 5C.

The Figure 5B workbook is duplicated in this folder so that all three comparison arms can be inspected together.

## nuad comparison

The `nuad_comparison/results/` folder contains four cases: a 6-mer case with 41 pairs, two 12-mer cases with 120 and 129 pairs using different on-target windows, and a 20-mer case with 897 pairs at 1 M sodium and zero magnesium.

Each case includes `nuad.xlsx`, the matching OrthoSeq report as `orthoseq.xlsx`, and native nuad designs, sequence lists, reports, random states, and logs under `raw_nuad/`. The nuad workbooks contain the generated libraries, independently verified energies, and individual constraint violations.

The 20-mer case additionally includes `naive.xlsx`, containing 876 valid pairs. Under a nominal budget of 10 million association evaluations, hybrid search produced 897 valid pairs, while nuad retained 897 pairs with 2,203 individual constraint violations. The shared design conditions and executed evaluation counts are documented in the workbooks and archive README.

## Polycube comparison

The `polycube_comparison/data/` folder contains five workbooks: the published polycube sequence library, our association-energy and complex-energy evaluations of that library, the OrthoSeq search report, and a complex-energy evaluation of the OrthoSeq library.

Both libraries use 9-nt cores with 5′ T12 extensions. Association energies (`G_AB − G_A − G_B`) support the binding-energy comparison; complex free energies (`G_AB`) are used to calculate specificity gaps.

## Naming conventions and terminology

Earlier versions of OrthoSeq used shorter algorithm labels, such as `vertex_cover` and `hybrid_search`. The archive retains these labels in existing reports and also includes more explicit names that identify the heuristic and variant. The definitions below explain both naming formats:

| Saved label | Meaning in the manuscript |
| --- | --- |
| `vertex_cover` | Graph-aware search using GMAX with rule-based tie-breaking and iterative improvement. |
| `vertex_cover_GMIN` | Graph-aware search using GMIN with rule-based tie-breaking and iterative improvement. |
| `hybrid_offline`, `hybrid_search` | Hybrid search using precomputed energies and energies calculated during the search, respectively. Both use GMAX with rule-based tie-breaking. |
| `naive`, `naive_search`, `naive_rand*` | Naive search with random candidate ordering. |
| `naive_ordered`, `naive_rank*` | Naive search with weaker-first candidate ordering based on on-target binding energy. |

Labels such as `vertex_cover_GMIN_rule_offline` encode the choices explicitly. In graph-search labels, `GMAX` and `GMIN` identify maximum-degree deletion and minimum-degree selection, while `rand`, `rank`, and `rule` identify random, on-target-energy-based, and rule-based tie-breaking. The `_bare` suffix indicates no iterative improvement, and `_offline` indicates use of precomputed energies. In the long-sequence heuristic comparison, labels such as `gmax_rule` and `gmax_rule_iterative` distinguish bare and iteratively improved variants. Asterisks in the table indicate variable suffixes.

Some long-sequence reports retain a hybrid-workflow label even when the budget was exhausted during the initial graph-search stage. The approximately 2235-pair initial-graph conditions are reported as graph-aware search in the manuscript.

Parameter names also differ:

- `offtarget_limit`: off-target association free-energy limit
- `initial_fresh_pair_count`: requested initial graph-aware search subset size
- `vc_max_iterations`: maximum number of iterative-improvement steps
- `prune_fraction`: perturbation fraction

Workbook metadata keys use the prefixes `input.*`, `search.*`, `nupack.*`, `dataset.*`, and `artifact.*`. The `artifact.*` values may contain absolute paths from the machine on which the benchmark was run. These paths are retained only as provenance records and are not required to interpret the archive.

## Relation to the manuscript

- The short-sequence data support the full-conflict-graph benchmark in Figure 4A.
- The 37 °C sigma-1.0 long-sequence data support the fixed-budget benchmark in Figure 4B.
- The 25 °C repeat and 37 °C sigma-0.5 batches support the temperature and on-target-window analyses in the Supporting Information.
- The additional short-sequence runs and long-sequence GMIN/GMAX comparison support the graph-search heuristic and candidate-ranking analyses in the Supporting Information.
- The `seqwalk_comparison/` workbooks support the Figure 5 comparison.
- The `nuad_comparison/` files support the 6-mer, 12-mer, and 20-mer comparisons discussed in the main text and detailed in the Supporting Information.
- The `polycube_comparison/` workbooks support the comparison with the published polycube sticky-end library in the Supporting Information.

## Funding and compute resources

This work was supported in part by:

- the U.S. Department of Energy, Office of Science, Basic Energy Sciences, Biomolecular Materials Program, under Award No. DE-SC0024136;
- the German Research Foundation (Deutsche Forschungsgemeinschaft, DFG) Walter Benjamin Programme, project 553862611;
- the Dana-Farber Cancer Institute Claudia Adams Barr Program for Cancer Research; and
- the Korea–US Collaborative Research Fund (KUCRF), grant RS-2024-00468463.

The O2 High Performance Compute Cluster, supported by the Research Computing Group at Harvard Medical School, was used to accelerate development of the evolutionary algorithm and the final large-scale parameter sweeps.
