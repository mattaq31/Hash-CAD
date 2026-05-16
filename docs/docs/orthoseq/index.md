# Orthogonal Sequence Generator (OrthoSeq)
## Problem It Solves
OrthoSeq is a tool to build sets of **orthogonally binding nucleic-acid sequence pairs** for applications where binding thermodynamics matter more than simple sequence dissimilarity.
OrthoSeq uses NUPACK for thermodynamic calculations.  
In this context, sequence pairs are selected such that:
- each sequence binds strongly to its intended partner within a user-defined **on-target binding** energy range
- each sequence avoids binding strongly to unintended partners according to a user-defined **off-target binding** limit
- each individual strand avoids forming overly stable secondary structure according to a user-defined secondary-structure energy limit

The sequence layout can also be defined, including the length of the binding region and optional 5' and 3' flanks.
NUPACK-related thermodynamic parameters can be set, including temperature, sodium concentration, magnesium concentration, and nucleic acid type (DNA or RNA).

The sequence search is integrated into a Streamlit-based graphical user interface. The user interface allows you to define the sequence layout and select thermodynamic parameters such as the on-target energy range and off-target binding limit.
The search can be launched directly from the graphical user interface.


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
To start the app run the following in your conda environment:
```bash
orthoseq_app
```
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

### 2. Run a pilot analysis to choose the on-target range

Start by getting an overview of the binding energies for the selected sequence layout.

In the **Pilot Analysis** tab, choose a sample size and click **Run Pilot Analysis**. The app selects a random set of sequence pairs according to the layout and thermodynamic settings from the left panel. It then computes:
- on-target binding energies
- off-target binding energies
- secondary-structure energies

The results are shown in two plots.

The first plot shows on-target and off-target energy histograms. You can enter minimum and maximum on-target energies in the input fields. The selected range is displayed as vertical lines on the plot. If you are happy with the range, transfer it to the next tab using **Use This Range**.

The second plot shows the secondary-structure energy distribution. You can enter a minimum secondary-structure energy limit, which is also shown as a vertical line. If you are happy with the value, transfer it using **Use This Value**.

### Selection Helper

The **Selection Helper** tab helps interpret what these thermodynamic values mean experimentally.

Because the selection algorithm is based on pairwise sequence comparisons, this tab provides reference plots:
- fraction bound of two strands vs. binding energy
- fraction of strands that remain fully unpaired vs. secondary-structure energy

You can set the strand concentration for the first plot. The plots depend on the temperature selected in the left panel. The relevant equations are shown above the plots together with additional thermodynamic information.

### 3. Choose the off-target binding limit

In the **Off-Target Limit** tab, the on-target range and secondary-structure limit transferred from the pilot analysis are shown again. You can choose a sample size and click **Run Off-Target Analysis**.

The app then selects a random set of sequence pairs that satisfy the previously chosen conditions and computes the on-target and off-target energies again with NUPACK.

You can then choose the off-target energy limit by entering a value in the input field. The selected value is shown as a vertical red line in the plot. The plot also shows the conflict probability, which is the probability that two sequence pairs from the currently selected pool violate the chosen off-target limit.

The off-target limit is chosen in a separate step because the selected on-target energy range affects the off-target energy distribution. Sequences with stronger on-target binding also tend to show stronger off-target binding.

You can use the **Selection Helper** tab again to interpret the off-target energies. Once you are happy with the off-target limit, transfer it to the next tab using **Use This Value**.

### 4. Run the sequence search

Unfortunately, the search can be slow because NUPACK calculations dominate the runtime. For longer runs, it is a good idea to prevent your computer from going to sleep. On macOS, for example, you can run `caffeinate` in a separate terminal before starting the search.

In the **Orthogonal Sequence Search** tab, the parameters transferred from the previous tabs are shown again for reference. Start the search with **Run Search**. While it is running, progress messages are shown in the logging window above the tabs. If you already have enough sequences, you can stop the search with **Stop Searching**.

There is also an **Advanced Search Parameters** panel. In most cases, the default values are a good starting point.

The search has two phases:

- **Pass 1 (seed):** a random pool of sequence pairs is collected under the selected on-target and secondary-structure limits. Same-strand homodimers are screened at collection time. Off-target interactions are then computed within this seed pool, a conflict graph is built, and a graph-based search is performed to obtain an initial orthogonal set.
- **Pass 2 (collection):** new sequence pairs are sampled one by one under the same limits and cross-referenced against the retained seed set. Only candidates with zero conflicts against the retained set are admitted to the fresh collection pool.
- After enough fresh candidates have been collected, off-target interactions are computed among the fresh candidates only, a conflict graph is built on that fresh pool, and the graph-based search is run there.
- Survivors from that fresh-only graph step are then unioned into the retained set.

This keeps pass 2 cheaper than recomputing a full graph on retained plus fresh pairs, because the expensive final vertex-cover step only resolves conflicts among fresh candidates.

The graph-based search can be understood as follows:

- each sequence pair in the current pool is treated as a node in a graph
- two nodes are connected if the corresponding sequence pairs violate the chosen off-target limit
- the goal is then to keep as many nodes as possible while removing enough conflicting nodes that no connections remain
- the vertex-cover routine is the heuristic used to decide which sequence pairs to remove so that the remaining set is as large as possible

You do not need to think in graph-theory terms to use the app, but this is the reason the advanced parameters mainly control repeated graph-search attempts and refinement steps.

Brief explanation of the advanced parameters:

- **Initial Subset Size**: number of requested sequence pairs used to build the seed pool before the first vertex-cover run.
- **Vertex-Cover Max Iterations**: number of refinement iterations used inside each graph-based optimization run.
- **Prune Fraction**: controls how strongly the current graph-based solution is perturbed before it is refined again.
- **Progress Report Interval (min)**: when nonzero, pass 2 collection is chunked into timed intervals. At each boundary a peek vertex cover estimates the current total without committing results.


---




## Advanced use via scripts (from here on no longer up to date)

You can manually download example [`scripts`](https://github.com/mattaq31/Hash-CAD/tree/main/crisscross_kit/orthoseq_generator/scripts) from GitHub demonstrating how to use the tool.

Once downloaded, you can move the scripts into any directory you like and add that directory to your `PATH` environment variable.

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
- Runs the **actual sequence search** based on the parameters you determined using Scripts 1 and 2.  
- Creates the full list of sequence pairs and uses the evolutionary vertex cover algorithm to select an orthogonal set.  
- Logs progress to the console and saves:  
  - The selected sequences (`.txt` files) in the **results** folder.  
  - Energy distribution plots.  
- This is the main script that gives you your usable orthogonal sequences.
- You can press **Ctrl+C** at any time to trigger a keyboard interrupt; the best sequences found so far will still be saved, and the rest of the script will complete its cleanup steps.  
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
A **results** folder will appear automatically with the found orthogonal sequence pairs saved as `.txt` files.  
A **pre_compute_energies** folder will also appear automatically (if it does not exist yet) and will contain `.pkl` files with precomputed energy values.  

The file structure will look like this:

```text
scripts/
    results/
        mysequences101.txt
    pre_compute_energies/
        energy_library.pkl
    the_scripts.py
    some_plots.pdf
```

## Energy Computations and Precompute Library

To compute binding energies, we use **NUPACK 4.0** thermodynamic calculations.  
This is computationally expensive, especially when computing all cross-interactions between sequence pairs.

To speed up the computations, we use two strategies:  
1. **Multiprocessing** to parallelize energy calculations across multiple CPU cores.  
2. A **precompute library** to avoid computing the same interaction energy more than once.

The precompute library is loaded by each instance of the multiprocessing.  
Importantly, updating the precompute library is done **outside** of the multiprocessing processes to avoid file corruption.

There is a global variable:

    USE_LIBRARY = True

which specifies whether to use the precompute library or not.

You can specify the name of the precompute library with:

    hf.choose_precompute_library("my_new_cache.pkl")

If the specified library file does not exist, running any script will automatically create it inside the `pre_computed_energies` folder.

Whether using the precompute library speeds up your run depends on your use case:  
- For **small sequence sets** or **short sequences**, it usually helps.  
- For **longer sequences** (>=7 bases), the library can grow very large, and loading the `.pkl` file may slow things down.

---

### Fixed NUPACK Conditions

The input conditions for NUPACK are currently **hardcoded**:  
- Temperature: 37 °C  
- Sodium concentration: 0.05 M  
- Magnesium concentration: 0.025 M  

If you need different parameters, you must manually adjust the code.

---

### Note on Precompute Library Performance

- The current implementation of saving/loading the precompute library is **not fully optimized**.  
- When the `.pkl` file grows too large, overall runtime can increase due to file I/O.  
- To avoid excessively large libraries, define a **new precompute library** for each on-target energy range you explore.


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

### Core Functions

- **`greedy_vertex_cover_heuristic(E, …)`**  
  Repeatedly removes the highest-degree vertex to greedily cover edges.

- **`iterative_vertex_cover_refinement(V, E, …)`**  
  Wraps the greedy heuristic in an iterative perturbation loop. Each iteration removes a fraction of vertices from the current cover, repairs uncovered edges, cleans the repaired full cover against the full graph, and keeps the result if the independent set improved.

- **`hybrid_search(sequence_source, …)`**  
  The main two-pass search driver. Pass 1 collects a seed pool, computes its conflict graph, and retains an initial independent set. Pass 2 samples additional candidates, cross-references them against the retained seed set, then runs vertex cover on the fresh candidates only and unions those survivors into the retained set.

Each of these functions is documented in detail in their respective docstrings.

### Print statements

There are a couple of print statements that report on the current process of the hybrid search. They’re useful for understanding exactly what the algorithm is doing at each step:

---

```text
=== Pass 1: Initial sampling ===
```
➔ The search has entered the seed pass.

---

```text
Sampling 450 candidate pairs (energy + self-energy filter)...
```
➔ Candidate collection is running. Each sampled pair must pass the on-target, self-energy, and same-strand homodimer gates before it enters the seed pool.

---

```text
Running vertex cover on 191 pairs...
```
➔ The seed pool is fixed. The algorithm is now building the conflict graph for that pool and pruning it down to an independent set.

---

```text
=== Pass 2: Cross-referenced collection ===
Collecting candidate pairs cross-referenced against 27 retained (NUPACK budget: 4926148)...
```
➔ The search has entered the collection pass. New candidates are sampled under the same thermodynamic filters and must additionally have zero conflicts against the retained seed set before entering the fresh pool.

---

```text
Running vertex cover on 31 candidate pairs...
```
➔ The collection pass is finalized by running vertex cover on the fresh candidates only. Survivors are then unioned into the retained set.

---

```text
--- Progress report triggered (20 min interval reached) ---
Running peek vertex cover on 94 collected candidate pairs...
```
➔ Optional progress reporting is enabled. The search estimates the current total without committing a final result for the pass.

---

```text
Calculating with 12 cores...
```
➔ Started parallel processing using 12 worker processes  
```text
100%|████████████████████████████████████████████████████████████████████| 31375/31375 [00:06<00:00, 4822.91it/s]
```
➔ Progress update for one of the batched NUPACK calculations.


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
- The `pre_computed_energies` folder is created automatically and contains the cached `.pkl` energy files.  
- The off-target energies (here `subset_data_7mers96to101.pkl`) are saved in the same folder as the script.
