# Orthogonal Sequence Generator (OrthoSeq)
## Problem It Solves
This tool helps you find sets of **orthogonally binding DNA sequence pairs**. The main focus is on selecting sequences based on **thermodynamic binding energy**, not sequence diversity (as commonly used in barcoding).
The tool allows you to specify an on-target binding energy range and an off-target binding limit.

Orthogonality here means:  
- Each sequence binds strongly to its intended partner (**on-target**)  
- Sequences do **not** bind significantly to any unintended partner (**off-target**)  

Unlike other orthogonal sequence generators that use **De Bruijn graphs** and/or focus on **Hamming distance** for barcode generation, this tool uses **NUPACK** to compute actual hybridization energies. The sequence selection is based **solely on thermodynamic interactions**.

To maximize the number of orthogonal sequences found under given constraints, we employ:  
- **Advanced graph-theoretic algorithms** (vertex cover)  
- **Evolutionary optimization** strategies  

The algorithm works best for sequences up to **13 or 14 nucleotides** long (plus optional fixed 5' and 3' extensions, defined by the user).

---
## Installation

This package is automatically installed when you install the main `crisscross_kit` package as below:

```bash
pip install crisscross_kit
```

You will also need to install the `nupack` package separately from [here](https://www.nupack.org/download/overview).  `Nupack` will work directly in a MacOS or Linux environment, but will require the Windows Subsystem for Linux (WSL) to run on Windows.

---
## Basic Use

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
   Since minimum vertex cover is NP-hard, we use greedy and evolutionary strategies to find a small cover (and thus a large independent set) in reasonable time.

### Core Functions

- **`heuristic_vertex_cover_optimized2(E)`**  
  Repeatedly removes the vertex with the highest degree (most edges).  
  When there’s a tie, it picks among them the vertex whose neighbors have the least overlap with the other top-degree vertices—avoiding redundant removals.

- **`iterative_vertex_cover_multi(V, E, …)`**  
  Wraps the greedy heuristic in two nested loops:  
  1. **Multistart outer loop**: re-runs the heuristic from different random seeds to escape poor starting conditions.  
  2. **Inner loop**: strategically perturbs the current cover (removes some vertices, re-covers uncovered edges) and re-applies the greedy heuristic to refine the solution.

- **`evolutionary_vertex_cover(sequence_pairs, offtarget_limit, max_ontarget, min_ontarget, …)`**  
  The main driver that implements an evolutionary selection process. Iterates for a fixed number of generations:  
  - Samples random subsets within a specified on-target energy range from the candidate list of sequence pairs. Previously preserved sequences that worked well are added to each subset.  
  - Computes off-target interaction energies and builds the corresponding graph.  
  - Uses `iterative_vertex_cover_multi` as the “selection” step to find orthogonal sequences in the subset.  
  - If a larger independent set than in previous generations is found, it replaces the record and clears the preserved sequences.  
  - If the new independent set is at least 95% the size of the previous best, its members are added (without duplicates) to the preserved sequences.

Each of these functions is documented in detail in their respective docstrings.

### Print statements

There are a couple of print statements that report on the current process of the `evolutionary_vertex_cover` function. They’re useful for understanding exactly what the algorithm is doing at each step:

---

```text
Selected 250 sequence pairs with energies in range [-10.4, -9.6]
```
➔ Subset selection based on the on-target energy window defined by the user; 250 pairs chosen for this generation as set as input parameter.

---

```text
Computing off-target energies for handle-handle interactions
```
➔ Now computing cross-interaction energies between “handle” sequences and other antihandle sequences 
```text
Calculating with 12 cores...
```
➔ Started parallel processing using 12 worker processes  
```text
100%|████████████████████████████████████████████████████████████████████| 31375/31375 [00:06<00:00, 4822.91it/s]
```
➔ There is a life update on the progress of the computation

➔ There will be print statements for the other two configurations as well: anti-handles with other anti-handles and handles with other anti-handles

---

```text
Iteration 1 of 30 | current bestest independent set size: 40
…
Iteration 30 of 30 | current bestest independent set size: 44
```
➔ Progress updates of the multistart iterations of iterative_vertex_cover_multi when called: shows progression and best size updates

___


```text
Generation 1 | Current: 40 | Best: 40 | History size: 40
Generation 2 | Current: 46 | Best: 46 | History size: 46
```
➔ Generation summaries of the evolutionary algorithm:  
- **Current** = size of independent set found in this generation  
- **Best**    = best-ever size so far  
- **History** = number of sequences preserved for sampling  


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
