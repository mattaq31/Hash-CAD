# Orthogonal Sequence Generator (OrthoSeq)
## Problem It Solves
OrthoSeq is a tool for identifying sets of **orthogonally binding nucleic-acid sequence pairs**. In this context, a sequence pair consists of a strand and its intended binding partner. The goal is to construct large sets of such pairs that bind strongly on target while avoiding appreciable off-target binding.

OrthoSeq uses **NUPACK** to evaluate thermodynamic interaction energies. Sequence pairs are selected such that:
- each sequence pair has an **on-target** interaction within a user-defined energy range
- off-target interactions with all other sequence pairs remain below a user-defined **off-target** limit
- each individual strand has sufficiently weak secondary-structure formation according to a user-defined **secondary-structure** energy limit

The sequence layout can be defined by choosing the core binding-domain length together with optional 5' and 3' extensions. Thermodynamic model parameters can also be set, including nucleic acid type, temperature, sodium concentration, and magnesium concentration.

The sequence search is integrated into a Streamlit-based graphical user interface. The app supports parameter selection, exploratory analysis, off-target limit selection, and direct sequence search from the same interface.


---
## Installation

OrthoSeq is recommended to run inside a **Miniconda** environment.

The main installation complication is **NUPACK**:
- NUPACK is required for the thermodynamic calculations
- NUPACK is not installed via pip in the normal way
- because of NUPACK, this workflow currently only works for **macOS and Linux**

### Recommended Setup

1. Install **Miniconda** if you do not have it already.

2. Create and activate a fresh environment:

```bash
conda create -n orthoseq python=3.11
conda activate orthoseq
```

3. Upgrade `pip` inside that environment:

```bash
pip install -U pip
```

4. Install **NUPACK** first.

Go to the official NUPACK page, accept the license, download the current release, and unzip it.

Official guide:
- [NUPACK 4 Getting Started](https://docs.nupack.org/start/)

Then install it from the downloaded package directory inside your conda environment:

```bash
pip install -U nupack -f ~/Downloads/nupack-VERSION/package
```
Here, `nupack-VERSION` means the name of the downloaded and unzipped NUPACK folder.

5. Install `crisscross_kit` with the Streamlit extra:
```bash
pip install "crisscross-kit[streamlit]"
```
This installs the package together with the Streamlit web app dependencies.

6. Start the app:
To start the app while preventing system sleep during long searches, run one of the following in your conda environment:

macOS:
```bash
caffeinate -i orthoseq_app
```

Ubuntu or other systemd-based Linux systems:
```bash
systemd-inhibit --what=idle:sleep orthoseq_app
```

These commands prevent automatic system sleep during long runs.

This opens the Streamlit interface in your browser.

---
## Using the App
Basic workflow:

### 1. Set the global sequence and thermodynamic parameters

Use the global settings panel on the left side of the app.

Here you can define the sequence layout:
- core sequence length
- optional 5' and 3' extensions by entering a base string such as `TTAG`
- unwanted substrings such as `TTTT`

There is an illustration at the top of the panel showing the resulting binding layout.

Sequences containing unwanted substrings are excluded from the search. The unwanted-substring filter can be applied either to the core sequence only or to the full sequence including the user-defined extensions. Be careful not to choose unwanted substrings that are already part of your fixed extensions, or no valid sequences may remain.

Further down in the panel, you can set the thermodynamic parameters:
- nucleic acid type: DNA or RNA
- temperature
- sodium concentration
- magnesium concentration

If you select RNA, the sodium and magnesium concentrations are ignored because the NUPACK RNA model is defined only for 1 M sodium.

At the bottom of the same panel, there is also an optional **SeqWalk** section. If **Use SeqWalk Cores** is enabled, candidate core sequences are drawn from a SeqWalk-generated code set instead of being generated as unrestricted random cores. In this mode, you can choose:
- the SeqWalk `k` parameter
- whether SeqWalk should enforce `RCfree`

The sidebar also shows the raw number of SeqWalk cores generated for the current settings. This count is the direct SeqWalk output before OrthoSeq applies its own thermodynamic filtering during sampling.

### Selection Helper

The **Selection Helper** tab is optional, but useful for interpreting thermodynamic values experimentally.

It provides reference plots for:
- fraction bound of two strands vs. binding energy
- fraction of strands that remain fully unpaired vs. secondary-structure energy

You can set the strand concentration for the first plot. The plots depend on the temperature selected in the left panel.

### 2. Run a pilot analysis to choose the on-target range and secondary-structure limit

Start by getting an overview of the binding energies for the selected sequence layout.

In the **Pilot Analysis** tab, choose a sample size and click **Run Pilot Analysis**. The app selects a random set of sequence pairs according to the layout and thermodynamic settings from the left panel. It then computes:
- on-target binding energies
- off-target binding energies
- secondary-structure energies

The results are shown in two plots.

The first plot shows on-target and off-target energy histograms. You can enter minimum and maximum on-target energies in the input fields. The selected range is displayed as vertical lines on the plot. If you are happy with the range, transfer it to the next tab using **Use This Range**.

The second plot shows the secondary-structure energy distribution. You can enter a minimum secondary-structure energy limit, which is also shown as a vertical line. If you are happy with the value, transfer it using **Use This Value**.

### 3. Choose the off-target binding limit

In the **Off-Target Limit** tab, the on-target range and secondary-structure limit transferred from the pilot analysis are shown again. You can choose a sample size and click **Run Off-Target Analysis**.

The app then selects a random set of sequence pairs that satisfy the previously chosen conditions and computes the on-target and off-target energies again with NUPACK.

You can then choose the off-target energy limit by entering a value in the input field. The selected value is shown as a vertical red line in the plot. The plot also shows the conflict probability, which is the probability that two sequence pairs from the currently selected pool violate the chosen off-target limit.

The off-target limit is chosen in a separate step because the selected on-target energy range affects the off-target energy distribution. Sequences with stronger on-target binding also tend to show stronger off-target binding.

You can use the **Selection Helper** tab again to interpret the off-target energies. Once you are happy with the off-target limit, transfer it to the next tab using **Use This Value**.

### 4. Run the orthogonal sequence-pair search

In the **Orthogonal Sequence-Pair Search** tab, the transferred parameter values are shown again for reference. Start the search with **Run Search**.

While the search is running, progress messages are shown in the logging window above the workflow tabs.

The **Search Parameters** panel contains the main search controls:
- **Initial Graph Search Subset Size**
- **Graph Search Iterations**
- **Perturbation Fraction**

In most cases, the default values are a good starting point.

Two interactive controls are available while the search is running:
- **Checkpoint Now** computes an intermediate estimate from the currently collected sequence-pair pool and then continues the search.
- **Stop Searching** stops further sequence-pair collection and finalizes the current sequence-pair pool before returning the best orthogonal sequence pairs found so far.

After the search finishes, the app verifies the final sequence pairs directly with NUPACK, displays the final plots, and writes a timestamped XLSX report into the local `results/` folder. The same report can also be downloaded from the app as `ortho_sequences.xlsx`.

### 5. Load an existing search report

The **Load Results** tab lets you upload a previously saved XLSX search report and recreate the plots without rerunning the full search.

The tab reads the sequence pairs and recorded metadata from the workbook, including:
- NUPACK material, temperature, sodium concentration, and magnesium concentration
- on-target energy range
- off-target energy limit
- secondary-structure energy limit
- random seed
- graph-search parameters when present

The app then recomputes the on-target, off-target, and secondary-structure energies using the recorded NUPACK parameters and shows the resulting plots directly in the interface. It also writes two timestamped PDF artifacts into the local `results/` folder:
- on-target vs. off-target energy histogram
- secondary-structure energy histogram



---




## Advanced Use via Scripts (Partly Outdated)

The main top-level scripts in [`scripts`](https://github.com/mattaq31/Hash-CAD/tree/main/crisscross_kit/orthoseq_generator/scripts) mirror the app workflow and are useful when you want to run the same steps from the command line.

Unless noted otherwise, these scripts write their output into a local `results/` folder created in the directory from which the script is executed.

### CLI workflow

#### `pre_analize_sequences.py`
- Command-line mirror of **Pilot Analysis**.
- Samples sequence pairs for the current layout and thermodynamic model.
- Computes on-target, off-target, and secondary-structure energies.
- Use it to choose a reasonable on-target energy range and secondary-structure limit.

#### `pre_analize_sequences_in_range.py`
- Command-line mirror of **Off-Target Limit** selection.
- Samples sequence pairs within a chosen on-target energy range.
- Recomputes off-target energies for that filtered pool.
- Use it to choose a reasonable off-target energy limit after fixing the on-target range.

#### `run_sequence_search.py`
- Command-line mirror of **Orthogonal Sequence-Pair Search**.
- Runs the hybrid search with the chosen thermodynamic limits.
- Writes the selected sequence pairs and related output artifacts into the local `results/` folder.
- This is the main non-app entry point for generating orthogonal sequence pairs.

#### `run_naive_search.py`
- Baseline command-line search using the naive sequential acceptance strategy.
- Useful for comparison against the hybrid search.

### Utility scripts

#### `load_sequences_from_txt_and_plot.py`
- Loads sequence pairs from a plain-text file.
- Recomputes on-target, off-target, and secondary-structure energies.
- Writes on/off-target and self-energy histogram PDFs.

#### `load_sequences_from_xlsx_and_plot.py`
- Loads sequence pairs from a saved XLSX search report.
- Uses the recorded NUPACK parameters from the workbook metadata.
- Recomputes on-target, off-target, and secondary-structure energies.
- Writes on/off-target and self-energy histogram PDFs.

### Auxiliary and legacy material

- `auxilary_scripts/` contains older helper material and figure-generation utilities that are not part of the main supported workflow.
- `legacy/` contains an older search workflow that precomputes all pairwise interactions up front. This is only practical for small sequence spaces.
- `benchmarking/` contains benchmark scripts used for algorithm comparisons and paper figures.

---

## Typical File Structure

The scripts and app write output into a local `results/` folder created in the directory from which they are executed.

Typical outputs include:
- saved sequence-pair lists
- XLSX search reports
- PDF energy histograms

```text
working_directory/
    results/
        ortho_sequences_ui_2026-05-30_12-00-00.xlsx
        ortho_sequences.xlsx
        my_sequences.txt
        some_report_on_off_target_2026-05-30_12-00-00.pdf
        some_report_self_energy_2026-05-30_12-00-00.pdf
```

## Energy Computations

To compute binding energies, we use **NUPACK 4.0** thermodynamic calculations.  
This is computationally expensive, especially when computing all cross-interactions between sequence pairs.

The current implementation uses **multiprocessing** to parallelize NUPACK calculations across multiple CPU cores. Runtime therefore depends strongly on both the number of sequence pairs being evaluated and the number of off-target interactions that must be checked.


## Algorithm Basic Idea

OrthoSeq formulates orthogonal sequence-pair selection as a graph problem.

1. **Prefilter the pool**  
   Sequence pairs are first filtered by on-target energy and secondary-structure energy.

2. **Define conflicts by off-target binding**  
   Two sequence pairs are considered incompatible if any of their off-target interactions exceeds the chosen off-target limit.

3. **Find a large orthogonal set**  
   The remaining problem is to identify a large subset of mutually compatible sequence pairs, corresponding to an independent set in the conflict graph.

4. **Use a hybrid search strategy**  
   The main search first builds an initial orthogonal set from a moderate-size pool, then collects additional sequence pairs that are already compatible with that initial orthogonal set, and finally runs a graph search on the collected sequence-pair pool.

### Core Functions

- **`hybrid_search(sequence_source, …)`**  
  Main hybrid search driver used by the app and by the main command-line search script.

- **`verify_selected_pairs(...)`**  
  Recomputes on-target, self, and off-target energies for a final selected set before writing the XLSX report.

- **`load_found_pairs(...)` and `load_metadata(...)`**  
  Canonical readers for loading sequence pairs and metadata back from a saved XLSX search report.

### Print statements

The hybrid search prints a few status lines that are useful for understanding which phase of the search is currently running.

---

```text
=== Initial graph search ===
```
The search has entered the initial graph-search phase.

---

```text
Selecting 450 sequence pairs for the initial graph search...
```
The search is drawing sequence pairs for the initial graph-search pool. Each pair must satisfy the on-target and secondary-structure filters before it is accepted.

---

```text
Running graph search on 191 sequence pairs...
```
The initial pool is fixed and the graph search is now identifying an initial orthogonal set.

---

```text
=== Candidate collection ===
Collecting sequence pairs against 27 initial orthogonal sequence pairs (NUPACK budget: 4926148)...
```
The search has entered the collection phase. New sequence pairs must satisfy the same thermodynamic filters and must also be compatible with the initial orthogonal set.

---

```text
Candidate sequence-pair collection progress: accepted 94 sequence pairs after 848 attempts and 12990 direct NUPACK calls (2.0 min elapsed).
```
This is a periodic progress update from the collection phase.

---

```text
--- Manual checkpoint triggered ---
Running graph search on 94 collected sequence pairs...
```
The search is estimating the current total without finalizing the run.

---

```text
Stop detected during collection. Finalizing current sequence-pair pool.
Running final graph search on 31 sequence pairs...
```
The search has stopped collecting new sequence pairs and is finalizing the current sequence-pair pool.

---

```text
Calculating with 12 cores...
```
Parallel NUPACK computation has started.

```text
Computing off-target energies for 31375 handle-antihandle interactions.
```
One of the off-target interaction batches is being evaluated.

```text
100%|████████████████████████████████████████████████████████████████████| 31375/31375 [00:06<00:00, 4822.91it/s]
```
Progress bar for one of the batched NUPACK computations.

## XLSX Report Structure

The XLSX workbook written by the app and by the main search/reporting scripts is the canonical saved search artifact. It is also the format used by the **Load Results** tab and by `load_sequences_from_xlsx_and_plot.py`.

### How to interpret the workbook

- `found_pairs` is the final answer.
- `run_metadata` explains under which thermodynamic and search conditions that answer was produced.
- `search_progress` explains how the answer was reached.
- `validation` indicates whether the final verified set satisfies the requested limits cleanly.
- the matrix sheets expose the full verified off-target interaction structure of the selected set.

### Main sheets

#### `run_metadata`
This sheet stores the run configuration as key-value pairs. Important keys include:

- `input.length`: core binding-domain length
- `input.fivep_ext`: fixed 5' extension
- `input.threep_ext`: fixed 3' extension
- `input.unwanted_substrings`: excluded substrings used during sequence generation
- `input.apply_unwanted_to`: whether the excluded substrings were applied to the core only or to the full sequence
- `input.used_seqwalk`: whether the candidate cores came from a SeqWalk-generated code set
- `input.seqwalk_k`: the SeqWalk `k` setting when SeqWalk mode was used
- `input.seqwalk_rcfree`: whether SeqWalk was run with reverse-complement freedom enabled
- `input.seqwalk_core_count`: the raw number of SeqWalk cores generated for the recorded settings
- `search.min_ontarget` and `search.max_ontarget`: requested on-target energy range
- `search.offtarget_limit`: requested off-target energy limit
- `search.self_energy_limit`: requested secondary-structure energy limit
- `search.initial_fresh_pair_count`: internal metadata key for the initial graph-search subset size
- `search.prune_fraction`: internal metadata key for the perturbation fraction used by the graph search
- `search.vc_max_iterations`: internal metadata key for the graph-search iteration count
- `search.random_seed`: random seed used for the run
- `search.total_nupack_budget`: total NUPACK call budget, when one was used
- `search.total_nupack_calls`: total NUPACK calls executed by the search
- `search.search_duration_s`: total search runtime in seconds
- `nupack.material`: DNA or RNA model
- `nupack.celsius`: temperature
- `nupack.sodium`: sodium concentration
- `nupack.magnesium`: magnesium concentration

This sheet is the source of truth for replaying the thermodynamic model used during the search.

#### `found_pairs`
This is the final orthogonal sequence-pair set. Each row corresponds to one final selected sequence pair and includes:

- the pair index used in the report
- the global pair ID when available
- `seq`: the handle strand
- `rc_seq`: the antihandle strand, which is the intended binding partner derived from the reverse complement of the core binding domain
- verified on-target energy
- verified secondary-structure energy for `seq`
- verified secondary-structure energy for `rc_seq`

When SeqWalk mode was used, the sheet can also include:

- `origin_core`: the original sampled SeqWalk core before OrthoSeq canonicalized the sequence pair
- `origin_seq_with_flank`: the original SeqWalk-oriented strand after adding the fixed 5' and 3' extensions

These provenance columns are only attached to the final `found_pairs` sheet. They are meant for cases where the final exported sequences are used as barcodes and the original SeqWalk orientation must be preserved, even though the internal search logic still canonicalizes sequence-pair order.

#### `selected_hh`, `selected_hah`, `selected_ahah`
These are the verified off-target energy matrices for the final selected set:

- `selected_hh`: handle-handle interactions, meaning interactions between the `seq` strands
- `selected_hah`: handle-antihandle interactions, meaning interactions between `seq` and `rc_seq`
- `selected_ahah`: antihandle-antihandle interactions, meaning interactions between the `rc_seq` strands

The row and column labels encode:

```text
pair_id : strand_type : sequence
```

where `strand_type` is `H` for the handle strand and `A` for the intended partner strand.

#### `search_progress`
This sheet records the main generation stages of the search. For hybrid search runs it includes rows for the initial graph-search stage and the collection stage. Typical columns include:

- `pass`: stage name, for example `seed` or `collection`
- `pairs_collected`: number of sequence pairs collected into that stage before graph search
- `pairs_after_vc`: number of orthogonal sequence pairs recovered from that stage after graph search
- `total_retained`: total orthogonal sequence pairs retained after the stage completed
- `nupack_calls_executed`: NUPACK calls charged to that stage
- `stopped_early`: whether the stage ended by stop request, interrupt, budget, or another non-default termination condition
- `attempts`: number of sequence-pair draws attempted in that stage
- `passed_ontarget_and_self`: number of sequence pairs that passed the on-target and secondary-structure filters
- `passed_homodimer`: number of sequence pairs that also passed the same-strand off-target screen
- `accepted_into_pool`: number of sequence pairs that entered the stage pool
- `notes`: termination reason or other short stage note

This sheet is most useful for understanding how much of the result came from the initial graph search versus the later sequence-pair pool.

#### `validation`
This sheet stores simple pass/fail checks on the final selected set, including:

- whether the selected set is nonempty
- whether all on-target energies lie within the requested range
- whether all self energies lie above the requested limit
- how many verified off-target violations remain

### Optional sheets

#### `seed_pass_pairs`
For hybrid search runs, this sheet stores the sequence pairs selected for the initial graph search, before the graph search removes conflicts. These sequence pairs are therefore **not** necessarily orthogonal.

#### `seed_hh`, `seed_hah`, `seed_ahah`
For hybrid search runs, these are the verified off-target energy matrices for the initial graph-search input pool stored in `seed_pass_pairs`, using the same handle-handle, handle-antihandle, and antihandle-antihandle convention described above. These matrices are useful for inspecting the structure of the conflict graph before graph search removes conflicting sequence pairs.


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
- The legacy scripts are self-contained and have their own pre_compute_library
- The `results` folder is created automatically in the legacy directory and contains the found orthogonal sequences in for example`independent_sequences.txt`.  
- The off-target energies (here `subset_data_7mers96to101.pkl`) are saved in the same folder as the script.
