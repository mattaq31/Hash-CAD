# Orthogonal Sequence Generator

## Problem It Solves

This tool helps you find sets of **orthogonally binding DNA sequence pairs**. The main focus is on selecting sequences based on **thermodynamic binding energy**, not sequence diversity (as commonly used in barcoding).

Orthogonality here means:  
- Each sequence binds strongly to its intended partner (**on-target**)  
- Sequences do **not** bind significantly to any unintended partner (**off-target**)  

Unlike other orthogonal sequence generators that use **De Bruijn graphs** or focus on **Hamming distance** for barcode generation, this tool uses **NUPACK** to compute actual hybridization energies. The sequence selection is based **solely on thermodynamic interactions**.

To maximize the number of orthogonal sequences found under given constraints, we employ:  
- **Advanced graph-theoretic algorithms** (iterative vertex-cover heuristic)  
- A **two-pass hybrid search** strategy that separates exploration from exploitation  

The algorithm works best for sequences up to **13 or 14 nucleotides** long (plus optional fixed 5' and 3' extensions, defined by the user).

---

## Basic Use

Installation instructions can be found in the main `README.md` file located in the main [`crisscross_kit`](https://github.com/mattaq31/Hash-CAD) folder. You can download example [`scripts`](https://github.com/mattaq31/Hash-CAD/tree/main/crisscross_kit/orthoseq_generator/scripts) from GitHub that demonstrate how to use the tool.

Once `crisscross_kit` is  installed, you can copy the scripts into any directory you like and add that directory to your `PATH` environment variable.

There are four scripts that are typically executed in sequence:


---

### 1. `preanalyze_sequences.py`  
- Creates a complete list of all possible sequence pairs of a given length (plus optional flanking sequences).  
- Randomly selects a subset and computes both **on-target** (intra-pair) and **off-target** (inter-pair) energies.  
- Plots energy histograms to help you decide:  
  - Which **on-target energy range** you want.  
  - Gives you a first impression of **off-target energies**.  
- You should use **Script 2** to refine your choice of off-target energy cutoff.

---

### 2. `analyze_on_target_range.py`  
- Same as **Script 1**, but the random subset is selected **within a specific on-target energy range**.  
- This lets you fine-tune your **off-target binding energy cutoff** based on the specific sequences you are interested in.  
- Idea: Pick your **on-target energy** → analyze the typical **off-target energies** → select a reasonable cutoff.

---

### 3. `run_sequence_search.py`  
- **Main entry point** for running the orthogonal sequence search from code.
- Runs the **actual sequence search** based on the parameters you determined using Scripts 1 and 2.  
- Uses the two-pass hybrid search algorithm to select an orthogonal set:
  - **Pass 1 (Seed):** Collects candidate pairs filtered by on-target energy, self-energy, and same-strand homodimer threshold, then runs vertex cover to resolve remaining conflicts.
  - **Pass 2 (Collection):** Collects additional candidates cross-referenced against the seed survivors, with the same on-target, self-energy, and homodimer filters applied before admission, then runs vertex cover on fresh candidates only.
- Saves a verified XLSX report with the found pairs, energy matrices, and search metadata.
- Also saves energy distribution plots.  
- You can press **Ctrl+C** at any time to trigger a keyboard interrupt; the best sequences found so far will still be saved.  

### 3b. `run_naive_search.py`  
- Implements a **naive greedy baseline** for comparison with the hybrid algorithm.
- Samples candidate pairs on the fly and greedily accepts each pair only if it passes on-target, self-energy, same-strand homodimer, and cross-reference checks against all previously accepted pairs.
- Does not use vertex cover or graph-based optimization — acceptance is purely sequential.
- Produces the same XLSX report format as the hybrid search, so results are directly comparable.
- Useful for benchmarking: under the same NUPACK budget and constraints, how many pairs does the greedy approach find vs. the hybrid?
---

### 4. `analyze_saved_sequences.py` *(optional)*  
- Loads a previously saved sequence list from the **results** folder and recomputes/plots on-target and off-target energies.  
- Useful if you want to re-plot without rerunning the full selection (**Script 3 already plots by default**).

### 5. `legacy` Directory

- Contains an older, self-contained version of the scripts that **does not** use evolutionary optimization.  
- This legacy workflow still finds good orthogonal sets but **requires precomputing all** pairwise interactions up front—only practical for sequence lengths ≤ 7.  
- The `legacy/` folder includes its own `results/` and `pre_compute_energies/` subfolders. 
- Further usage details and parameter explanations are included in comments at the top of each legacy script. Additional notes appear in the end of this README.

---

## Typical File Structure

Executing the scripts will make some folders and files appear in the folder you execute the scripts from.  
A **results** folder will appear automatically with the found orthogonal sequence pairs saved as `.xlsx` reports.  

The file structure will look like this:

```text
scripts/
    results/
        ortho_sequences.xlsx
    the_scripts.py
    some_plots.pdf
```

## Energy Computations

To compute binding energies, we use **NUPACK 4.0** thermodynamic calculations.  
This is computationally expensive, especially when computing all cross-interactions between sequence pairs.

To speed up the computations, we use **multiprocessing** to parallelize energy calculations across multiple CPU cores. The number of workers is determined automatically from available CPUs (or SLURM allocation on clusters).

---

### NUPACK Conditions

The NUPACK thermodynamic parameters are set via `hf.set_nupack_params()`:  
- Material (e.g. `'dna'`)  
- Temperature in Celsius  
- Sodium concentration in M  
- Magnesium concentration in M  

These are configured in each script and in the Streamlit app before the search runs.

## Algorithm Basic Idea

The core of the algorithm is a heuristic that attempts to find a minimum vertex cover—a known NP-hard problem—so the solution it finds may not be optimal.

1. **Modeling off-target interactions as a graph**  
   - Each sequence pair is a vertex.  
   - An edge connects two vertices if their off-target binding energy exceeds the chosen threshold (i.e., they “interact” too strongly).  

2. **Orthogonal set ⇒ Independent set**  
   Finding a set of sequence pairs with no unwanted interactions is equivalent to removing vertices until no edges remain.  
   Removing as few vertices as possible (to leave as large a pool of orthogonal sequences as possible) is exactly the **minimum vertex cover** problem.

3. **Why a heuristic?**  
   Since minimum vertex cover is NP-hard, we use a greedy heuristic with iterative perturbation to find a small cover (and thus a large independent set) in reasonable time.

### Two-Pass Hybrid Search

The main search algorithm (`hybrid_search` in `search_algorithm.py`) works in two passes:

**Pass 1 (Seed):**
- Collect `initial_fresh_pair_count` candidate pairs filtered by on-target energy, self-energy, and same-strand homodimer threshold.
- Compute the full pairwise off-target energy matrix (O(n^2) NUPACK calls).
- Build the conflict graph and run the iterative vertex-cover heuristic.
- Survivors become the retained set.

**Pass 2 (Collection):**
- Collect additional candidate pairs, each filtered by the same on-target, self-energy, and homodimer gates and then cross-referenced against the retained set (zero violations required).
- Because every accepted candidate is already compatible with all retained pairs, the final vertex cover only resolves conflicts among fresh candidates (O(fresh^2) instead of O((fresh+retained)^2)).
- Union survivors into the retained set.

The search terminates when the NUPACK call budget is exhausted, the user interrupts (Ctrl+C or stop button), or live sampling becomes effectively exhausted under the duplicate-streak heuristic.

**Optional progress reporting:** When `progress_report_interval_min` is set, pass 2 collection is chunked into timed intervals. At each boundary a peek vertex cover estimates the current total without committing results.

### Core Functions

- **`iterative_vertex_cover_refinement(V, E, …)`**  
  The vertex-cover heuristic. Repeatedly removes the highest-degree vertex to greedily cover edges. Wraps this in an iterative perturbation loop: each iteration removes a fraction of vertices (`prune_fraction`) from the current cover, re-covers uncovered edges, cleans the repaired full cover against the full graph, and checks if the independent set improved.

- **`hybrid_search(sequence_pairs, …)`**  
  The main search entry point. Orchestrates the two-pass strategy described above. Called by the CLI script, Streamlit app, and benchmark runners. Expects a live sequence source such as `SequencePairRegistry` that provides `sample_pair()` and `get_pair_by_id()`.

- **`select_subset_in_energy_range(sequence_pairs, …)`**  
  The candidate collection workhorse. Draws random pairs, evaluates on-target/self-energy filters, rejects strong same-strand homodimers, optionally cross-references against a retained pool, and accumulates accepted pairs until a stop condition fires. Returns a `stop_reason` string (`"timeout"`, `"nupack_limit"`, `"stop_event"`, `"keyboard_interrupt"`, `"duplicate_streak_limit_reached=<value>"`, or `None` for normal completion) instead of a boolean. Supports hot-start via `prior_state`: the returned state dict can be passed back to resume collection with the same tested set and counters. The budget check is VC-aware and reserves `estimate_offtarget_nupack_calls(N) = 2 * N^2` calls for the downstream vertex cover.

- **`crossreference_sequences(new_pair, pool, …)`**  
  Checks whether a single candidate pair is compatible with all pairs in a pool by evaluating all four strand combinations. Short-circuits on first violation.

### Console Output

The algorithm prints structured status messages during execution:

```text
=== Pass 1: Initial sampling ===
Sampling 450 candidate pairs (energy + self-energy filter)...
Selected 450 candidate pairs [853 NUPACK calls]
Running vertex cover on 450 pairs...
Computing off-target energies for plus-plus interactions
Calculating with 12 cores...
100%|████████████████████████| 101475/101475 [00:06<00:00, 4822.91it/s]
Independent set: 120 pairs retained | NUPACK calls: 405853 | elapsed=45.2s
=== Pass 2: Cross-referenced collection ===
Collecting candidate pairs cross-referenced against 120 retained (NUPACK budget: 4594147)...
Collected 340 candidate pairs [1200000 NUPACK calls]
Running vertex cover on 340 candidate pairs...
Independent set: 95 additional pairs found | Total retained: 215 | NUPACK calls: 1836421 | elapsed=320.5s
```

When progress reporting is enabled:

```text
--- Progress report triggered (20 min interval reached) ---
Running peek vertex cover on 94 collected candidate pairs...
Candidate pairs collected so far: 94 | Retained from seed: 120 | New from collection (after peek VC): 29 | Estimated total: 149 | NUPACK calls: 7482 | elapsed=1200.5s
--- Continuing collection ---
```

### Search Progress Reporting

The verified XLSX report contains a `search_progress` sheet. For the live
hybrid search, the main progress columns are:

- `pass`
- `pairs_collected`
- `pairs_after_vc`
- `total_retained`
- `nupack_calls_executed`
- `stopped_early`
- `attempts`
- `passed_ontarget_and_self`
- `passed_homodimer`
- `accepted_into_pool`

For the live naive search, the same vocabulary is used as far as it applies.
Naive rows are emitted per accepted pair (plus a final summary row), so
`pairs_after_vc` is left blank because there is no vertex-cover stage.

### Shared Report Readers

The shared writer in `search_reporting.py` now has a matching light-weight
reader module: `orthoseq_generator.search_report_reader`.

Use it from plotting or analysis scripts when you want stable access to the
standard workbook contents without rewriting local pandas boilerplate.

Main helpers:

- `load_metadata(report_path)` -> `dict`
- `load_found_pairs(report_path)` -> `DataFrame`
- `load_seed_pairs(report_path)` -> `DataFrame | None`
- `load_search_progress(report_path)` -> `DataFrame | None`
- `load_offtarget_matrices(report_path, family="selected" | "seed")` -> `dict[str, DataFrame]`

Design rules:

- metadata is lightly parsed (`N.A.` -> `None`, booleans and numerics restored)
- sheets and matrices stay as ordinary pandas `DataFrame`s
- off-target matrices remain 2D with their original axis labels
- matrix-axis labels can be parsed separately with `parse_pair_label(...)` or
  `parse_axis_labels(...)` when needed

`search_progress` is intentionally returned raw because its column set varies
by algorithm.


## Legacy Scripts Basic Use

The `legacy/` directory includes two self-contained scripts for finding orthogonal 7-mer sequence pairs or smaller without evolutionary optimization.

1. **`precompute_energies.py`**  
   - Generates all 7-mer sequence pairs (with a 'TT' 5′ flank), filtering out any with four identical bases in a row.  
   - Selects all pairs whose on-target energies lie within a specified range.  
   - Computes off-target interaction energies for the selected subset.  
   - Saves the subset, their indices, and off-target energies to for example `subset_data_7mers96to101.pkl`. This is a separate saving routine and does not end up in the pre_compute_energies directory but in the legacy folder itself.

2. **`legacy_sequence_search.py`**  
   - Loads the pickled subset and off-target energies from for example `subset_data_7mers96to101.pkl`.  
   - Builds the off-target interaction graph using a user-defined cutoff.  
   - Runs the iterative vertex-cover heuristic to find the minimal cover.  
   - Derives the independent set (orthogonal sequences) and saves them to for example `independent_sequences.txt` in `results`.

**Output & Folders**  
- The lecacy scripts are self-contained and have their own pre_compute_library
- The `results` folder is created automatically in the legacy directory and contains the found orthogonal sequences in for example`independent_sequences.txt`.  
- The `pre_computed_energies` folder is created automatically and contains the cached `.pkl` energy files.  
- The off-target energies (here `subset_data_7mers96to101.pkl`) are saved in the same folder as the script.
