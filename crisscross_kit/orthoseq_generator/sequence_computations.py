import pickle
import itertools
from nupack import *
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from matplotlib.ticker import AutoMinorLocator

from orthoseq_generator import helper_functions as hf
import time






def revcom(sequence):
    """
    Computes the reverse complement of a DNA sequence.

    :param sequence: Single DNA sequence as a string.
    :type sequence: str

    :returns: Reverse complement of the input sequence as a string.
    :rtype: str
    """
    dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return "".join(dna_complement[n] for n in reversed(sequence))


def has_four_consecutive_bases(seq):
    """
    Returns True if the sequence contains four identical consecutive bases 
    (e.g., "GGGG", "CCCC", "AAAA", "TTTT").

    Notes
    -----
    Additional sequence constraints (e.g., homopolymer runs of other lengths)
    can be added here as needed.

    :param seq: DNA sequence as a string.
    :type seq: str

    :returns: True if any base appears four times in a row, False otherwise.
    :rtype: bool
    """
    return 'GGGG' in seq or 'CCCC' in seq or 'AAAA' in seq or 'TTTT' in seq


def sorted_key(seq1, seq2):
    """
    Returns a tuple with the two input sequences sorted alphabetically.

    Description
    -----------
    Ensures that (seq1, seq2) and (seq2, seq1) map to the same dictionary key.

    :param seq1: First DNA sequence.
    :type seq1: str

    :param seq2: Second DNA sequence.
    :type seq2: str

    :returns: Tuple of the two sequences in alphabetical order.
    :rtype: tuple
    """
    return (min(seq1, seq2), max(seq1, seq2))


def create_sequence_pairs_pool(length=7, fivep_ext="", threep_ext="", avoid_gggg=True):

    """
    Generates a list of unique DNA sequence pairs (and their reverse complements) with optional flanking sequences.

    Procedure
    ---------
    1. Generate all possible core sequences of specified `length`.  
    2. Compute each sequence's reverse complement and alphabetically sort the pair.  
    3. If `avoid_gggg` is True, filter out any pair where either sequence contains four identical bases in a row.  
    4. Prepend `fivep_ext` and append `threep_ext` to both members of each pair.  
    5. Enumerate the resulting list, assigning a unique integer ID to each pair.

    :param length: Length of the core DNA sequences (without flanks).
    :type length: int

    :param fivep_ext: Optional 5′ flanking sequence prepended to each strand.
    :type fivep_ext: str

    :param threep_ext: Optional 3′ flanking sequence appended to each strand.
    :type threep_ext: str

    :param avoid_gggg: If True, filters out pairs containing four identical consecutive bases.
    :type avoid_gggg: bool

    :returns: List of tuples `[(index, (sequence, reverse_complement)), ...]`,
              where `index` is a unique ID and each tuple contains the complementary pair.
    :rtype: list of tuple
    """

    # Define the DNA bases
    bases = ['A', 'T', 'G', 'C']
    n_mers = [''.join(mer) for mer in itertools.product(bases, repeat=length)]

    unique_pairs_set = set()
    unique_n_mers = []

    # Generate unique sequence pairs with a progress bar
    for mer in tqdm(n_mers, desc="Generating unique pairs"):
        rc_mer = revcom(mer)
        pair = sorted_key(mer, rc_mer)

        if pair not in unique_pairs_set:
            if avoid_gggg and (has_four_consecutive_bases(mer) or has_four_consecutive_bases(rc_mer)):
                continue
            unique_pairs_set.add(pair)
            unique_n_mers.append(pair)

    # Add flanks
    unique_flanked_n_mers = [
        (f"{fivep_ext}{mer}{threep_ext}", f"{fivep_ext}{rc_mer}{threep_ext}")
        for mer, rc_mer in unique_n_mers
    ]

    return list(enumerate(unique_flanked_n_mers))





def nupack_compute_energy_precompute_library_fast(seq1, seq2, type='total', Use_Library=None):
    
    """
    Computes the Gibbs free energy of hybridization between two DNA sequences using NUPACK,
    with optional caching via a precompute library.

    Notes
    -----
    - Uses a local cache to avoid redundant NUPACK calls when provided with `Use_Library=True`. The input variable overwrites the global state. 
    - Energies are stored under a sorted key so (seq1, seq2) and (seq2, seq1) map identically. Saving is not done here
    - This function is called by multiprocessing. Each instance loads its own precompute library once from file. 
    - Does not write to the cache during multiprocessing to prevent conflicts.
    - All energies larger than -1 kcal/mol are mapped to -1 kcal/mol. 0 is used in other routines as an idicator that the energy has not been computed. -1 kcal/mol is already extremely weak. (virtually no interaction) 
    - Model parameters are fixed at 37°C, sodium=0.05 M, magnesium=0.025 M; change with a fresh cache.

    :param seq1: First DNA sequence.
    :type seq1: str

    :param seq2: Second DNA sequence.
    :type seq2: str

    :param type: Either 'total' (partition sum) or 'minimum' (MFE) calculation. The result of 'total' is what you would use to compute a binding constant.
    :type type: str

    :param Use_Library: If True, use and load the precompute cache; defaults to global setting.
    :type Use_Library: bool or None

    :returns: Gibbs free energy in kcal/mol, or -1.0 kcal/mol if no interaction or on error.
    :rtype: float
    """
    
    
    # Use global state if no input is given
    if Use_Library is None:         
        Use_Library = hf.USE_LIBRARY
   
   
   
    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    library1 = {}
    key = sorted_key(seq1, seq2)

    # Try loading from library if requested
    if Use_Library:
        if not hasattr(nupack_compute_energy_precompute_library_fast, "library_cache"):
            file_name = hf.get_library_path()
            if os.path.exists(file_name):
                with open(file_name, "rb") as file:
                    nupack_compute_energy_precompute_library_fast.library_cache = pickle.load(file)
            else:
                nupack_compute_energy_precompute_library_fast.library_cache = {}
        library1 = nupack_compute_energy_precompute_library_fast.library_cache
    
    # Return value from cache if available
    if Use_Library and key in library1:
        #print("retrived from lib")
        return library1[key]

    try:
        # Define the complex (symmetric if seq1 == seq2)
        if seq1 == seq2:
            complex_obj = Complex([A, A], name='(H1+H1)')
        else:
            complex_obj = Complex([A, B], name='(H1+H2)')

        # Define model
        model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.025)

        # Run complex analysis only for what's needed
        if type == 'minimum':
            results = complex_analysis([complex_obj], model=model1, compute=['mfe'])
            mfe_list = results[complex_obj].mfe
            if len(mfe_list) == 0:
                return -1.0
            energy = mfe_list[0].energy

        elif type == 'total':
            results = complex_analysis([complex_obj], model=model1, compute=['pfunc'])
            energy = results[complex_obj].free_energy
            if energy > 0:
                energy = -1.0

        else:
            raise ValueError('type must be either "minimum" or "total"')

        return energy

    except Exception as e:
        print(f"The following error occurred: {e}")
        print(seq1, seq2)
        return -1.0


def _init_worker(lib_filename, use_lib):
    """
    Initializes worker processes for parallel energy computations by configuring
    the precompute library filename and cache usage flag.

    :param lib_filename: Name of the precompute library file to load.
    :type lib_filename: str

    :param use_lib: Whether to use the precompute library in this worker.
    :type use_lib: bool

    :returns: None
    :rtype: None
    """
    
    
    hf._precompute_library_filename = lib_filename
    hf.USE_LIBRARY = use_lib
    #print("Worker using", _precompute_library_filename, USE_LIBRARY)



def compute_pair_energy_on(i, seq, rc_seq):
    """
    Helper function for parallel computing of on-target energies.

    :param i: Sequence index.
    :type i: int

    :param seq: DNA sequence.
    :type seq: str

    :param rc_seq: Reverse complement sequence.
    :type rc_seq: str

    :returns: Tuple containing the index and its computed Gibbs free energy.
    :rtype: tuple (int, float)
    """
    
    return i, nupack_compute_energy_precompute_library_fast(seq, rc_seq)


def compute_ontarget_energies(sequence_list):
    """
    Computes on-target Gibbs free energies for a list of sequence pairs using multiprocessing.

    Notes
    -----
    - Uses `ProcessPoolExecutor` (with `initializer=_init_worker`) to parallelize calls to NUPACK via `nupack_compute_energy_precompute_library_fast`.
    - If `hf.USE_LIBRARY` is True, the initializer function (`_init_worker`) passes the library filename and flag to each worker so that `nupack_compute_energy_precompute_library_fast` can load its cache. After all parallel computations finish, this function saves the cache with the new energies.
    - Saves the updated cache atomically using `DelayedKeyboardInterrupt` to prevent corruption.
    - Prints progress and CPU core usage to the console.

    :param sequence_list: List of tuples, each containing a sequence and its reverse complement.
    :type sequence_list: list of tuple

    :returns: NumPy array of Gibbs free energies (kcal/mol) for each sequence pair.
    :rtype: numpy.ndarray
    """

    # Preallocate array for better performance
    energies = np.zeros(len(sequence_list))

    # Announce what is about to happen
    print(f"Computing on-target energies for {len(sequence_list)} sequences...")

    max_workers = max(1, os.cpu_count() * 3 // 4)
    print(f"Calculating with {max_workers} cores...")

    # parallelize energy computation
    pool_args = (hf._precompute_library_filename, hf.USE_LIBRARY)
    
    with ProcessPoolExecutor(max_workers=max_workers,
                             initializer=_init_worker,
                             initargs=pool_args) as executor:
        futures = []
        for i, (seq, rc_seq) in enumerate(sequence_list):
            futures.append(executor.submit(compute_pair_energy_on, i, seq, rc_seq))

        for future in tqdm(as_completed(futures), total=len(futures)):
            i, energy = future.result()
            energies[i] = energy

    # update the precompute library if required
    if hf.USE_LIBRARY:
        # save to existing library or create a new one
        file_name = hf.get_library_path()

        if os.path.exists(file_name):
            # open library if exists
            with open(file_name, "rb") as file:
                library1 = pickle.load(file)
        else:
            library1 = {}

        for i, (seq, rc_seq) in enumerate(sequence_list):
            library1[sorted_key(seq, rc_seq)] = energies[i]

        # Save the updated dictionary
        with hf.DelayedKeyboardInterrupt():
            hf.save_pickle_atomic(library1, file_name)
            print("saved stuff")

    return energies




def compute_pair_energy_off(i, j, seq1, seq2):
    """
     Helper function for parallel computing of off-target energies.

     :param i: Index of the first sequence.
     :type i: int

     :param j: Index of the second sequence.
     :type j: int

     :param seq1: First DNA sequence.
     :type seq1: str

     :param seq2: Second DNA sequence.
     :type seq2: str

     :returns: Tuple `(i, j, energy)` where `energy` is the computed Gibbs free energy.
     :rtype: tuple (int, int, float)
     """
    return i, j, nupack_compute_energy_precompute_library_fast(seq1, seq2)


def compute_offtarget_energies(sequence_pairs):
    
    """
    Computes off-target hybridization energies for all pairwise combinations of a given list of sequence pairs.

    Procedure
    ---------
    1. Extract handles and antihandles from `sequence_pairs`.
    2. Initialize three N×N energy matrices for:
       - handle-handle interactions
       - antihandle-antihandle interactions
       - handle-antihandle interactions
    3. For each matrix, use `ProcessPoolExecutor` (via `compute_pair_energy_off`) to fill only the required entries:
       - i ≥ j for the two symmetric matrices
       - i ≠ j for the mixed handle-antihandle matrix
    4. If `hf.USE_LIBRARY` is True, the initializer function (`_init_worker`) passes the library filename and flag to each worker so that `nupack_compute_energy_precompute_library_fast` can load its cache. After all parallel computations finish, this function saves the cache with the new energies.


    Notes
    -----
    - Off-target interactions are computed for:  
      1) handle with handle  
      2) antihandle with antihandle  
      3) handle with antihandle  
    - Symmetric matrices only compute the lower triangle (i ≥ j) to avoid redundancy.  
    - Entries with no interaction or computation errors return -1.0 (mapped for any energy > -1.0).  
      A value of 0 indicates the energy was skipped due to redundancy.    
    - Uses `DelayedKeyboardInterrupt` to ensure atomic writes when saving the updated cache.

    :param sequence_pairs: List of (sequence, reverse_complement) tuples.
    :type sequence_pairs: list of tuple

    :returns: Dictionary containing three N×N numpy arrays with keys:  
              - 'handle_handle_energies'  
              - 'antihandle_handle_energies'  
              - 'antihandle_antihandle_energies'
    :rtype: dict
    """
    
    

    # call all seq handles and all rc_seq antihandles. this is an arbitrary choice
    # extract them for the pairs
    handles = [seq for seq, rc_seq in sequence_pairs]
    antihandles = [rc_seq for seq, rc_seq in sequence_pairs]

    # define all possible cross corrilations for offtarget binding. handles with handles, antihandles with antihandles and handles with antihandles
    crosscorrelated_handle_handle_energies = np.zeros((len(handles), len(handles)))
    crosscorrelated_antihandle_antihandle_energies = np.zeros((len(antihandles), len(antihandles)))
    crosscorrelated_handle_antihandle_energies = np.zeros((len(handles), len(antihandles)))


    # Define a helper function for parallel energy computation.
    # The `condition` argument is a function that determines whether to compute energy for a given index pair (i, j).
    # For handle-handle and antihandle-antihandle comparisons, we avoid redundant computations by only calculating for i ≥ j.
    # For handle-antihandle comparisons, we skip the diagonal (i == j) to avoid the on-target interactions.
    def parallel_energy_computation(seqs1, seqs2, energy_matrix, condition):
        max_workers = max(1, os.cpu_count() * 3// 4) # Use only 3 quarters of all possible cores on the maching
        print(f'Calculating with {max_workers} cores...')
        pool_args = (hf._precompute_library_filename, hf.USE_LIBRARY)

        with ProcessPoolExecutor(max_workers=max_workers,
                                 initializer=_init_worker,
                                 initargs=pool_args) as executor:
            futures = []
            for i, seq1 in enumerate(seqs1):
                for j, seq2 in enumerate(seqs2):
                    if condition(i, j):
                        futures.append(executor.submit(compute_pair_energy_off, i, j, seq1, seq2))

            for future in tqdm(as_completed(futures), total=len(futures)):
                i, j, energy = future.result()
                energy_matrix[i, j] = energy

    # Parallelize handle-handle energy computation
    print(f'Computing off-target energies for handle-handle interactions')
    parallel_energy_computation(handles, handles, crosscorrelated_handle_handle_energies, lambda i, j: j <= i)

    # Parallelize antihandle-antihandle energy computation
    print(f'Computing off-target energies for antihandle-antihandle interactions')
    parallel_energy_computation(antihandles, antihandles, crosscorrelated_antihandle_antihandle_energies, lambda i, j: j <= i)

    # Parallelize handle-antihandle energy computation
    print(f'Computing off-target energies for handle-antihandle interactions')
    parallel_energy_computation(handles, antihandles, crosscorrelated_handle_antihandle_energies, lambda i, j: j != i)


    #update the precompute library to  make things faster in the future
    if hf.USE_LIBRARY:
        file_name = hf.get_library_path()
        if os.path.exists(file_name):
            with open(file_name, "rb") as file:
                library1 = pickle.load(file)
        else:
            library1 = {}
    # this is redundant. A double loop each that iterates over all the filled entries in the 3 arrays
        for i, seq1 in enumerate(handles):
            for j, seq2 in enumerate(handles):
                # Corrected line: use [] to assign to a dictionary key
                if j <= i:
                    library1[sorted_key(seq1, seq2)] = crosscorrelated_handle_handle_energies[i, j]

        for i, seq1 in enumerate(antihandles):
            for j, seq2 in enumerate(antihandles):
                # Corrected line: use [] to assign to a dictionary key
                if j <= i:
                    library1[sorted_key(seq1, seq2)] = crosscorrelated_antihandle_antihandle_energies[i, j]

        for i, seq1 in enumerate(handles):
            for j, seq2 in enumerate(antihandles):
                # Corrected line: use [] to assign to a dictionary key
                if j != i:
                    library1[sorted_key(seq1, seq2)] = crosscorrelated_handle_antihandle_energies[i, j]

        # Save the updated dictionary
        #print(library1)
        with hf.DelayedKeyboardInterrupt():
            hf.save_pickle_atomic(library1, file_name)

    # Report energies if required

    return{
            'handle_handle_energies': crosscorrelated_handle_handle_energies,
            'antihandle_handle_energies': crosscorrelated_handle_antihandle_energies,
            'antihandle_antihandle_energies': crosscorrelated_antihandle_antihandle_energies
            }


def select_subset(sequence_pairs, max_size=200):
    """
    Selects a random subset of sequence pairs up to a specified maximum size.

    Notes
    -----
    - If the number of available pairs exceeds `max_size`, randomly samples `max_size` pairs using `random.sample`.
    - If the number of pairs is less than or equal to `max_size`, returns all pairs.
    - Uses sampling rather than full shuffling for performance on large datasets.

    :param sequence_pairs: List of `(index, (seq, rc_seq))` tuples.
    :type sequence_pairs: list of tuple

    :param max_size: Maximum number of pairs to select.
    :type max_size: int

    :returns: List of `(seq, rc_seq)` pairs selected.
    :rtype: list of tuple
    """
    
    
    total = len(sequence_pairs)

    if total > max_size:
        selected = random.sample(sequence_pairs, max_size)
        subset = []
        for index, pair in selected:
            subset.append(pair)
        print(f"Selected random subset of {max_size} pairs from {total} available pairs.")
    else:
        subset = []
        for index, pair in sequence_pairs:
            subset.append(pair)
        print(f"Using all {total} available pairs (less than or equal to {max_size}).")

    return subset


def select_subset_in_energy_range(sequence_pairs, energy_min=-np.inf, energy_max=np.inf, max_size=np.inf,
                                  Use_Library=None, avoid_indices=None):
    """
    Selects a random subset of sequence pairs whose on-target energies fall within a given range.

    Notes
    -----
    - Randomly samples without full shuffling for performance on large datasets.
    - Continues until `max_size` pairs are found or all candidates (excluding `avoid_indices`) are tested.
    - Uses `nupack_compute_energy_precompute_library_fast` with `Use_Library` to compute or fetch energies.
    - Prints a summary of how many pairs were selected.

    :param sequence_pairs: List of `(index, (seq, rc_seq))` tuples.
    :type sequence_pairs: list of tuple

    :param energy_min: Minimum allowed Gibbs free energy (inclusive).
    :type energy_min: float

    :param energy_max: Maximum allowed Gibbs free energy (inclusive).
    :type energy_max: float

    :param max_size: Maximum number of pairs to select.
    :type max_size: int or float('inf')

    :param Use_Library: Whether to use a precomputed energy library (overrides global setting if not None).
    :type Use_Library: bool or None

    :param avoid_indices: Set of indices to skip during selection.
    :type avoid_indices: set or None

    :returns: Tuple `(subset, indices)` where:
              - `subset` is a list of `(seq, rc_seq)` pairs within the energy range.
              - `indices` is a list of their corresponding global indices.
    :rtype: tuple (list of tuple, list of int)
    """
    
    if Use_Library is None:
        Use_Library = hf.USE_LIBRARY
    
    if avoid_indices is None:
        avoid_indices = set()

    subset = []
    indices = []
    tested_indices = set(avoid_indices)
    
    
    # I used shuffel here before. For large numbers of sequence_pairs i.e. around 4^12 shuffel is very slow
    while len(indices) < max_size and len(tested_indices) < len(sequence_pairs):
        index, (seq, rc_seq) = random.choice(sequence_pairs)

        if index in tested_indices:
            continue

        tested_indices.add(index)

        energy = nupack_compute_energy_precompute_library_fast(
            seq, rc_seq,
            type='total',
            Use_Library=Use_Library
        )

        if energy_min <= energy <= energy_max:
            subset.append((seq, rc_seq))
            indices.append(index)

    print(f"Selected {len(subset)} sequence pairs with energies in range [{energy_min}, {energy_max}]")

    return subset, indices


def select_all_in_energy_range(sequence_pairs, energy_min=-np.inf, energy_max=np.inf, Use_Library=None, avoid_ids=None):
    """
      Selects all sequence pairs whose on-target energies fall within a given energy range.

      Description
      -----------
      Iterates through every `(global_index, (seq, rc_seq))` tuple, computes the on-target energy
      using `nupack_compute_energy_precompute_library_fast`, and collects those where
      `energy_min <= energy <= energy_max`, skipping any `global_index` values in `avoid_ids`.
      Note that the ID here refers to the global index in the original sequence-pair list.

      Notes
      -----
      - If `Use_Library` is True, energies are fetched from or stored in the precompute cache.
      - Prints progress messages to the console.

      :param sequence_pairs: List of `(global_index, (seq, rc_seq))` tuples.
      :type sequence_pairs: list of tuple

      :param energy_min: Minimum allowed Gibbs free energy (inclusive).
      :type energy_min: float

      :param energy_max: Maximum allowed Gibbs free energy (inclusive).
      :type energy_max: float

      :param Use_Library: Whether to use a precomputed energy library (overrides global if not None).
      :type Use_Library: bool or None

      :param avoid_ids: Set of global indices to skip during selection.
      :type avoid_ids: set or None

      :returns: Tuple `(subset, selected_ids)` where:
                - `subset` is a list of `(seq, rc_seq)` pairs within the energy range.
                - `selected_ids` is a list of their corresponding global indices.
      :rtype: tuple (list of tuple, list of int)
      """
    print("Selecting sequences...")
    
    if Use_Library is None:
        Use_Library = hf.USE_LIBRARY
    
    if avoid_ids is None:
        avoid_ids = set()

    subset = []
    selected_ids = []

    for ID, (seq, rc_seq) in sequence_pairs:
        if ID in avoid_ids:
            continue

        energy = nupack_compute_energy_precompute_library_fast(
            seq, rc_seq, type='total', Use_Library=Use_Library
        )

        if energy_min <= energy <= energy_max:
            subset.append((seq, rc_seq))
            selected_ids.append(ID)

    print(f"Scanned and selected {len(subset)} sequence pairs in range [{energy_min}, {energy_max}]")
    return subset, selected_ids



def plot_on_off_target_histograms(on_energies, off_energies, bins=80, output_path=None):
    """
    Plots histograms comparing on-target and off-target Gibbs free energy distributions.

    Notes
    -----
    - If `off_energies` is a dict, combines:
        * 'handle_handle_energies'
        * 'antihandle_handle_energies'
        * 'antihandle_antihandle_energies'
      into a single array, excluding zeros (uncomputed values).
    - Normalizes frequencies so that area under each histogram sums to 1.
    - Uses consistent bin edges across both distributions for direct comparison.
    - Saves the figure to `output_path` if provided, otherwise only displays it.
    - Prints summary statistics after plotting.

    :param on_energies: On-target energy values.
    :type on_energies: array-like

    :param off_energies: Off-target energies as an array-like or dict of energy matrices.
    :type off_energies: array-like or dict

    :param bins: Number of bins for histograms.
    :type bins: int

    :param output_path: File path to save the plot; if None, the plot is only displayed.
    :type output_path: str or None

    :returns: Dictionary of summary statistics:
              - 'mean_on'  : Mean of on-target energies  
              - 'std_on'   : Standard deviation of on-target energies  
              - 'max_on'   : Maximum on-target energy  
              - 'mean_off' : Mean of off-target energies  
              - 'std_off'  : Standard deviation of off-target energies  
              - 'min_off'  : Minimum off-target energy  
    :rtype: dict
    """
    
    
    # --- Centralized style settings ---
    LINEWIDTH_AXIS = 2.5
    TICK_WIDTH = 2.5
    TICK_LENGTH = 6
    FONTSIZE_TICKS = 16
    FONTSIZE_LABELS = 19
    FONTSIZE_TITLE = 19
    FONTSIZE_LEGEND = 16
    FIGSIZE = (12, 5.5)  # Wide aspect ratio
    #Histogram colors
    color_on = '#1f77b4'  # dark blue
    color_off = '#d62728'  # dark red


    # Unpack dictionary if necessary
    if isinstance(off_energies, dict):
        off_energies = np.concatenate([
            off_energies['handle_handle_energies'].flatten(),
            off_energies['antihandle_handle_energies'].flatten(),
            off_energies['antihandle_antihandle_energies'].flatten()
        ])
        # 0 means per definition that this value has not been computed
        off_energies = off_energies[off_energies != 0]
        # Determine common bin edges
    combined_min = min(np.min(on_energies), np.min(off_energies))
    combined_max = max(np.max(on_energies), np.max(off_energies))
    bin_edges = np.linspace(combined_min, combined_max, bins + 1)


    # Compute statistics
    mean_on = np.mean(on_energies)
    std_on = np.std(on_energies)
    max_on = np.max(on_energies)
    mean_off = np.mean(off_energies)
    std_off = np.std(off_energies)
    min_off = np.min(off_energies)
    # We want a gap between min_off and max_on




    # Plot
    fig, ax = plt.subplots(figsize=FIGSIZE)


    ax.hist(
        off_energies, bins=bin_edges, alpha=0.8, label='Off-target',
        color=color_off, edgecolor='black', linewidth=2, density=True
    )
    ax.hist(
        on_energies, bins=bin_edges, alpha=0.8, label='On-target',
        color=color_on, edgecolor='black', linewidth=2, density=True
    )

    ax.set_xlabel('Gibbs free energy (kcal/mol)', fontsize=FONTSIZE_LABELS)
    ax.set_ylabel('Normalized frequency', fontsize=FONTSIZE_LABELS)
    ax.set_title('On-target vs Off-target Energy Distribution', fontsize=FONTSIZE_TITLE, pad=10)

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(axis='x', which='minor', length=4, width=1.2)

    ax.tick_params(
        axis='both',
        which='major',
        labelsize=FONTSIZE_TICKS,
        width=TICK_WIDTH,
        length=TICK_LENGTH
    )

    for spine in ax.spines.values():
        spine.set_linewidth(LINEWIDTH_AXIS)

    ax.legend(fontsize=FONTSIZE_LEGEND)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path)
    plt.show()

    # Print statistics
    print("\nSummary statistics:")
    print(f"Mean On-Target Energy:  {mean_on:.3f} kcal/mol")
    print(f"Std Dev On-Target:      {std_on:.3f} kcal/mol")
    print(f"Max On-Target Energy:   {max_on:.3f} kcal/mol")
    print(f"Mean Off-Target Energy: {mean_off:.3f} kcal/mol")
    print(f"Std Dev Off-Target:     {std_off:.3f} kcal/mol")
    print(f"Min Off-Target Energy:     {min_off:.3f} kcal/mol")
    

    # Return statistics
    return {
        'mean_on': mean_on,
        'std_on': std_on,
        'max_on': max_on,

        'mean_off': mean_off,
        'std_off': std_off,
        'min_off': min_off,
    }



if __name__ == "__main__":


    # run test to see if the functions above work
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    ontarget7mer=create_sequence_pairs_pool(length=5,fivep_ext="", threep_ext="",avoid_gggg=False)
    #print(ontarget7mer)
    
    # Define energy thresholds
    hf.choose_precompute_library("does_this_work.pkl")
    offtarget_limit = -5
    max_ontarget = -9.6
    min_ontarget = -10.4
    
   
    subset = select_subset(ontarget7mer, max_size=100)
    print(subset)
    hf.USE_LIBRARY = True
    on_e_subset = compute_ontarget_energies(subset)
    on_e_subset = compute_ontarget_energies(subset)
    # Compute the off-target energies for the subset
    t1=time.time()
    off_e_subset = compute_offtarget_energies(subset)
    t2= time.time()
    print(t2-t1)
    hf.USE_LIBRARY= True
    print("lib is on")
    off_e_subset = compute_offtarget_energies(subset)
    t3 = time.time()
    print(t3-t2)
    print("lib is off")
    off_e_subset = compute_offtarget_energies(subset)
    t4 = time.time()
    print(t4-t3)
    
    stats = plot_on_off_target_histograms(on_e_subset, off_e_subset, output_path='dump/energy_hist.pdf')
    


 