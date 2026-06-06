# Orthogonal Sequence Generator (OrthoSeq)

This README is for people reading or changing the `orthoseq_generator` code. It is not the main user guide.

For the user-facing workflow and interpretation, see [`docs/docs/orthoseq/index.md`](../../docs/docs/orthoseq/index.md). That page explains how to use the tool. This page explains how the package is put together, what the important modules do, and where the rough edges are.

The package also sits next to the paper *Graph-based design of DNA sequence-pair libraries with orthogonal binding specificity*. The paper and the user docs mostly describe the selection problem as finding a large **independent set** in a conflict graph. In the code, we use the removal-side and **vertex cover** perspective more often. That difference in wording is important when reading the code.

## Graph search: paper framing versus code framing

In both the paper and the code, the graph model is the same:

- each sequence pair is a vertex
- an off-target conflict creates an edge
- an orthogonal library is an independent set

The difference is in how the search is described. In the code, we use the removal-side and vertex-cover perspective more often:

- build the conflict graph
- find a small vertex cover heuristically
- remove those vertices
- treat the survivors as the orthogonal set

So when reading the code:

- `retained_pair_ids` is the current independent set
- `removed_vertices` or `vertex_cover` is the set being discarded

This is not a disagreement with the paper. It is the same graph problem written from the opposite side because the heuristic implementation is organized around removing bad vertices.

## Scope of the package

`orthoseq_generator` is a NUPACK-based search package for finding sets of DNA sequence pairs that:

- bind within a chosen on-target energy range
- do not bind too strongly to unintended partners
- do not form too much secondary structure on their own

The package has three main layers:

1. sequence pair generation and NUPACK evaluation
2. graph-based or naive search over sequence pairs
3. reporting and a Streamlit app around the search

It does not try to be a full thermodynamics framework. It is a focused search tool with a GUI, a few command-line scripts, and a report format that the rest of the codebase can replay.

## Repository and module structure

At the top level, the package is organized like this:

```text
orthoseq_generator/
├── helper_functions.py
├── sequence_generation.py
├── energy_computations.py
├── energy_plots.py
├── vertex_cover_algorithms.py
├── search_algorithm.py
├── naive_search_algorithm.py
├── search_reporting.py
├── search_report_reader.py
├── sequence_computations.py
├── numeric_functions.py
├── streamlit_app/
└── scripts/
```

The important modules are:

- `helper_functions.py`
  - global NUPACK parameter state via `set_nupack_params()`
  - global energy mode via `set_energy_type()`
  - default `results/` folder handling via `get_default_results_folder()`
  - plain text pair save/load helpers

- `sequence_generation.py`
  - reverse complement helper `revcom()`
  - canonical pair ordering via `sorted_key()`
  - live sequence pair generation source `SequencePairRegistry`
  - full sequence pair pool builders `create_sequence_pairs_pool()` and `create_seqwalk_sequence_pairs_pool()`
  - the SeqWalk-based path is still closer to prototyping support than to the main workflow
  - simple random subset helper `select_subset()`

- `energy_computations.py`
  - low-level NUPACK wrapper `compute_nupack_energy()`
  - parallel on-target and off-target matrix computation
  - sequence-pair filtering and live sampling in `select_subset_in_energy_range()`
  - direct compatibility testing in `crossreference_sequences()`

- `vertex_cover_algorithms.py`
  - converts off-target matrices into graph edges with `build_edges()`
  - greedy cover heuristic `greedy_vertex_cover_heuristic()`
  - iterative improvement loop `iterative_vertex_cover_refinement()`

- `search_algorithm.py`
  - main hybrid search entry point `hybrid_search()`
  - `_run_seed_pass()` and `_run_collection_pass()` for the two hybrid stages
  - manual checkpoint support
  - progress-row construction
  - in paper terms: initial graph-search subset step, collection step, and final graph search

- `naive_search_algorithm.py`
  - live greedy baseline `naive_search()`

- `search_reporting.py`
  - canonical XLSX writer `write_hybrid_search_result_xlsx()`
  - direct NUPACK verification with `verify_selected_pairs()`
  - validation summary with `validate_selected_pairs()`

- `search_report_reader.py`
  - workbook read helpers such as `load_metadata()`, `load_found_pairs()`, `load_seed_pairs()`, and `load_offtarget_matrices()`
  - `load_metadata()` is the main entry point for replaying saved conditions

- `sequence_computations.py`
  - compatibility shim
  - re-exports functions from `sequence_generation.py`, `energy_computations.py`, and `energy_plots.py`
  - many scripts and app files still import through this older name

- `energy_plots.py`
  - Matplotlib histogram writers used mainly by scripts and result replay

- `numeric_functions.py`
  - analytic and numeric independent-set estimators
  - not part of the core search path

Other directories:

- `streamlit_app/`: the UI
- `scripts/`: command-line entry points, benchmarks, legacy code, and utility scripts

## Streamlit app structure

The app code lives in `streamlit_app/`.

Main pieces:

- `cli.py`
  - console entry point that launches Streamlit against `orthoseq_app.py`

- `orthoseq_app.py`
  - page layout
  - sidebar inputs for sequence layout and NUPACK settings
  - tab routing
  - log console setup

- `state_manager.py`
  - all long-lived Streamlit session keys
  - default thresholds
  - thread queues and flags

- `logging_utils.py`
  - queue-backed logger wiring so background work can stream status messages into the UI

- `plotly_utils.py`
  - interactive histogram builders for on/off-target and self-energy plots

- `tabs/tab_selection_helper.py`
  - thermodynamic helper plots for fraction bound and fraction unpaired

- `tabs/tab_exploratory.py`
  - pilot analysis tab
  - samples a subset, computes on-target, off-target, and self energies, and shows the first set of histograms

- `tabs/tab_refinement.py`
  - off-target limit selection tab
  - samples within the chosen on-target window and estimates conflict probability

- `tabs/tab_search.py`
  - live hybrid search tab
  - starts the search in a worker thread
  - handles stop requests, manual checkpoints, final verification, and XLSX export

- `tabs/tab_load_results.py`
  - workbook replay tab
  - reads a saved XLSX report, restores the recorded NUPACK settings, recomputes energies, and recreates plots

The app mostly orchestrates. The real search logic remains in the package modules above, especially `search_algorithm.py`, `energy_computations.py`, and `search_reporting.py`.

## Search pipeline structure

The main search path is the hybrid search in `search_algorithm.py`.

### 1. Sequence source

The usual live sequence pair generation source is `SequencePairRegistry` in `sequence_generation.py`.

It is responsible for:

- generating random core sequences
- applying fixed 5' and 3' extensions
- filtering unwanted substrings
- sorting sequence pairs into one canonical order so each pair appears only once
- assigning a stable integer ID to each unique sequence pair inside one registry instance

Those registry IDs are used throughout the search code as the graph vertex labels.

### 2. Candidate filtering

The main filtering function is `select_subset_in_energy_range()` in `energy_computations.py`.

For each sampled sequence pair, it can apply:

- on-target energy range filtering
- secondary-structure filtering on both strands
- same-strand homodimer rejection against the off-target limit
- optional cross-reference checks against an already retained pool

This function is the main workhorse for both hybrid passes.

### 3. Seed pass (`_run_seed_pass()`, initial graph-search step in the paper)

The first hybrid stage is `_run_seed_pass()` in `search_algorithm.py`.

It:

1. collects a fixed-size sequence-pair pool
2. computes the full off-target matrix for that pool
3. builds the conflict graph with `build_edges()`
4. runs the vertex-cover heuristic
5. keeps the surviving sequence pairs as the initial orthogonal set

In the workbook, `seed_pass_pairs` means all sequence pairs in that initial graph-search subset, not only the surviving orthogonal ones.

### 4. Collection pass (`_run_collection_pass()`, collection step plus final graph search in the paper)

The second hybrid stage is `_run_collection_pass()`.

It:

1. keeps sampling fresh sequence pairs
2. cross-references each sequence pair against the retained seed set
3. only admits sequence pairs that are already compatible with the seed set
4. runs one more graph search on the collected fresh pool
5. unions those survivors with the retained seed survivors

This is the main scaling trick in the package. The second graph search only resolves conflicts among the fresh sequence pairs, not between fresh and retained sequence pairs, because compatibility with the retained set was already enforced during collection.

### 5. Naive baseline

`naive_search()` in `naive_search_algorithm.py` is the simpler baseline.

It does not build a conflict graph. It just accepts sequence pairs one by one if they pass:

- on-target and self-energy filters
- homodimer checks
- direct cross-reference against already accepted pairs

This is closer to the constructive independent-set framing from the paper.

## Reporting pipeline

The report system is centered on two modules:

- `search_reporting.py` writes the canonical workbook
- `search_report_reader.py` reads it

### Writer side

The shared writer is `write_hybrid_search_result_xlsx()`.

Despite the name, it is the canonical writer for more than the hybrid search. Naive search uses it too.

The workbook normally contains:

- `run_metadata`
- `found_pairs`
- `selected_hh`
- `selected_hah`
- `selected_ahah`
- `search_progress`
- `validation`

Hybrid runs can also include:

- `seed_pass_pairs`
- `seed_hh`
- `seed_hah`
- `seed_ahah`

The writer assumes that the final set has already been re-verified by direct NUPACK calls. That verification happens in `verify_selected_pairs()`, not implicitly inside the writer.

### Reader side

`search_report_reader.py` is the light-weight reader that other code should use instead of reimplementing workbook parsing.

Main helpers:

- `load_metadata()`
- `load_found_pairs()`
- `load_seed_pairs()` for the full `seed_pass_pairs` sheet from the initial graph-search subset
- `load_search_progress()`
- `load_offtarget_matrices()`

### Replaying saved runs

From the implementation side, the workbook metadata is the main reference for replaying a run.

That matters because:

- the saved sequence list alone is not enough to restore thermodynamic conditions
- pair IDs are only meaningful inside the registry instance that created them
- the replay path needs recorded NUPACK settings, search thresholds, and search parameters

The load-results tab follows this rule. It reads the workbook metadata, restores the NUPACK settings from that metadata, and recomputes energies from the saved sequences.

## Key contracts between modules

These are the main assumptions that hold the package together.

### Sequence pair representation

Most modules pass sequence pairs around as:

```python
(seq, rc_seq)
```

This is the standard tuple contract used by the search code, reporting, and plotting.

### Registry ID contract

`hybrid_search()` expects a live sequence-pair source that provides:

- `sample_pair() -> (pair_id, pair)`
- `get_pair_by_id(pair_id) -> pair`

The pair IDs are treated as stable vertex labels for the life of that registry instance. They should not be mixed across different registries.

### Matrix alignment

The off-target matrices returned by `compute_offtarget_energies()` are interpreted in the order of the `subset` passed in. `build_edges()` relies on the matching `indices` list to map matrix positions back to registry IDs.

There is also an important matrix-value contract: a `0` in these matrices means that the interaction was not computed for that matrix position, not that the interaction energy is actually zero. This comes from how the triangular and cross-family matrices are filled. Downstream code already treats those zeros as structural placeholders rather than real energies.

### Search-time versus report-time energies

Search-time filtering uses direct NUPACK calls and graph heuristics. Final reports are expected to use `verify_selected_pairs()` again on the selected set. The workbook is meant to reflect the verified final energies, not only the search-time bookkeeping.

### Global thermodynamic settings

Low-level energy code reads global state from `helper_functions.py`. Callers are expected to call `set_nupack_params()` and `set_energy_type()` before running searches, plots, or report verification.

## Global state and sharp edges

There are a few implementation details that are worth knowing before changing the code.

### Global NUPACK state

`helper_functions.py` keeps `NUPACK_PARAMS` and `ENERGY_TYPE` as module-level globals.

That means:

- low-level energy code is not pure
- callers must sync the globals before running a search
- worker processes copy this state through `_init_worker()`
- report replay temporarily mutates global state and then restores it

This is convenient in scripts and the Streamlit app, but it is not a clean library boundary.

### `results/` is cwd-relative

`get_default_results_folder()` builds `results/` under `os.getcwd()`.

So output location depends on where the process was launched, not on the package location.

That is fine for ad hoc script use, but it is easy to forget when:

- running the same script from different folders
- launching the app from an IDE
- comparing saved outputs across runs

Also, not every artifact path is fully normalized through that helper. Some scripts still write PDFs by simple relative filename.

### Naming drift

There are a few names that reflect history more than clarity.

- `sequence_computations.py` is now mostly a compatibility re-export layer.
- `write_hybrid_search_result_xlsx()` is the shared writer for hybrid and naive runs.
- `pre_analize_sequences.py` and `pre_analize_sequences_in_range.py` keep the older misspelling.
- the code often says `seq` and `rc_seq`, but `SequencePairRegistry` canonicalizes pair order with `sorted_key()`. So the first tuple element is simply the first element of the canonicalized sequence pair tuple.

## Energy modes

The low-level energy mode is controlled by `set_energy_type()` in `helper_functions.py`.

Supported values are:

- `minimum`
  - uses NUPACK MFE output for the complex
  - this is a single-structure minimum-energy view
  - it is not the same thing as an ensemble association free energy

- `total`
  - uses partition-function free energies
  - computes association-style energy as `G_AB - G_A - G_B`
  - this is the main mode used by the current app and search scripts

- `totalu`
  - also uses partition-function free energies
  - returns `G_AB` for the complex without subtracting monomer free energies
  - this is mostly useful for older or specialized workflows

One implementation detail matters here: in the current code, `total` and `totalu` clamp weak or positive values to `-1.0`. The idea is that once the interaction is that weak, the exact value does not matter for the sequence-pair selection logic.

## Scripts overview

The `scripts/` directory is mixed. Some files are current entry points, some are benchmark code, and some are old utility material.

Main current scripts:

- `scripts/pre_analize_sequences.py`
  - rough pilot analysis
  - samples a subset and plots on-target, off-target, and self-energy distributions

- `scripts/pre_analize_sequences_in_range.py`
  - second analysis step after choosing an on-target window
  - samples inside that window and helps choose the off-target limit

- `scripts/run_sequence_search.py`
  - standalone hybrid search example
  - runs the main search, verifies the result, and writes the canonical XLSX workbook

- `scripts/run_naive_search.py`
  - standalone naive baseline example
  - writes the same report format for comparison

- `scripts/load_sequences_from_txt_and_plot.py`
  - replay from a plain text pair list

- `scripts/load_sequences_from_xlsx_and_plot.py`
  - replay from the canonical workbook
  - this is the script-level counterpart of the load-results tab

Supporting directories:

- `scripts/benchmarking/`
  - benchmark and figure-generation code
  - useful if you are working on the paper comparisons rather than the app

- `scripts/legacy/`
  - older workflow that precomputes full interaction data up front
  - only practical for small sequence spaces

- `scripts/auxilary_scripts/`
  - helper and scratch material
  - useful for one-off analysis, but not a clean public surface
