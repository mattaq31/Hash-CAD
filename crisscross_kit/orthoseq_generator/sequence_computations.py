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





# Computes the reverse complement of a DNA sequence (input and output are strings).
def revcom(sequence):
    dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return "".join(dna_complement[n] for n in reversed(sequence))

# Returns True if the sequence contains four identical consecutive bases (e.g., "GGGG", "CCCC", etc.)
# In principle other sequence constrains could be added here
def has_four_consecutive_bases(seq):
    return 'GGGG' in seq or 'CCCC' in seq or 'AAAA' in seq or 'TTTT' in seq

# Returns a tuple with the two input sequences sorted alphabetically.
# This ensures that (seq1, seq2) and (seq2, seq1) are treated as the same key in a dictionary.
def sorted_key(seq1, seq2):
    return (min(seq1, seq2), max(seq1, seq2))

# Generates a list of unique DNA sequence pairs (and their reverse complements) with optional flanking sequences.
#
# Output:
#   - List of tuples: [(sequence1, reverse_complement1), (sequence2, reverse_complement2), ...]
#
# Input parameters:
#   - length (int): Length of the core DNA sequences (without flanks).
#   - fivep_ext (str): Optional 5' flanking sequence prepended to each strand.
#   - threep_ext (str): Optional 3' flanking sequence appended to each strand.
#   - avoid_gggg (bool): If True, filters out sequences (and their reverse complements) containing
#                        four identical consecutive bases (e.g., "GGGG", "AAAA").
def create_sequence_pairs_pool(length=7, fivep_ext="", threep_ext="", avoid_gggg=True):

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




# Computes the Gibbs free energy of hybridization between two DNA sequences using NUPACK.
#
# Parameters:
# - seq1, seq2 (str): DNA sequences to be analyzed.
# - samples (int): Number of samples used in NUPACK's sampling routine. Only affects 'minimum' mode here.
# - type (str): Either 'total' or 'minimum'.
#       - 'total': Computes the total partition function energy (more stable, better average measure).
#       - 'minimum': Returns the minimum free energy (MFE) structure only.
#
# - Use_Library (bool): If True, attempts to use a precomputed energy value from a local library (cache).
#
# Returns:
# - float: Gibbs free energy in kcal/mol.
#          If the strands do not interact or an error occurs, returns -1.0 (interpreted as "no interaction").
#          A Gibbs free energy of -1 is already very weak in comparison to commonly computed values.
#          0 energy is reserved for values not computed yet
#
# Notes:
# - The precomputed energy library is cached on first access to avoid repeated disk I/O.
# - Energies are stored using a canonical sorted key to ensure (seq1, seq2) and (seq2, seq1) map to the same value.
# - The model parameters are celsius=37, sodium=0.05, magnesium=0.025. If you change them you might want to start a new precompute library
def nupack_compute_energy_precompute_library_fast(seq1, seq2, type='total', Use_Library=None):
    
    
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
    #print("I can print")
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

# initializer for parralel computing 
def _init_worker(lib_filename, use_lib):
    
    hf._precompute_library_filename = lib_filename
    hf.USE_LIBRARY = use_lib
    #print("Worker using", _precompute_library_filename, USE_LIBRARY)


# helper function for parallel computing on-target energies
def compute_pair_energy_on(i, seq, rc_seq):
    return i, nupack_compute_energy_precompute_library_fast(seq, rc_seq)

# Computes the on-target energies of a list of sequence pairs.
# Optionally updates and uses a precomputed energy library to speed up future runs.
#
# Inputs:
# - sequence_list: List of tuples, where each tuple contains a sequence and its reverse complement.
# - Use_Library (bool): Set to True to read from and write to the precomputed energy library.
# Notes:
# - Parallel processing is used for efficiency.
# Returns:
# - energies: A NumPy array of Gibbs free energies (in kcal/mol) for each sequence pair.
def compute_ontarget_energies(sequence_list):
    

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



# helper function for parallel computing off target energies
def compute_pair_energy_off(i, j, seq1, seq2):
    # return i, j, nupack_compute_energy(seq1, seq2)
    return i, j, nupack_compute_energy_precompute_library_fast(seq1, seq2)

# Computes off-target hybridization energies for all pairwise combinations of given list of sequence pairs.
#
# Inputs:
# - sequence_pairs: List of tuples (handle, reverse_complement). These are assumed to be on-target pairs.
# - Use_Library (bool): If True, uses and updates a precomputed energy dictionary to speed up future calculations.
#
# Notes:
# - Parallel processing is used for efficiency.
# - Entries with no interaction or that error out return energy = -1.0.
# - Energies are symmetric where applicable (i.e., (i, j) = (j, i)). These are only computed once for efficiency
# - An Energy of 0 means it was not computed. -1 is the weakest value possible
#
# Returns:
# - Dictionary with keys:
#     'handle_handle_energies': 2D numpy array (N x N). upper triangle excluding diagonal filled with 0 because of redundancy
#     'antihandle_handle_energies': 2D numpy array (N x N) upper triangle excluding diagonal filled with 0 because of redundancy
#     'antihandle_antihandle_energies': 2D numpy array (N x N) diagonel filled with 0 because these are the ontarget energies
def compute_offtarget_energies(sequence_pairs):
    

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

# Selects a random subset of sequence pairs up to `max_size`.
# If the total number of pairs is less than or equal to `max_size`, all are kept.
#
# Parameters:
# - sequence_pairs (list): List of sequence tuples.
# - max_size (int): Maximum number of pairs to keep.
#
# Returns:
# - list: A subset of the input sequence_pairs.
# - list: The indices of the sequences in the input list
def select_subset(sequence_pairs, max_size=200):
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

# Selects a subset of sequence pairs whose on-target energies fall within a given range.
#
# This function randomly selects pairs from a pool of (index, (sequence, rc_sequence)) tuples.
# It avoids indices specified in `avoid_indices` and computes the hybridization energy using
# a precomputed energy library (if enabled). The selection continues until `max_size` valid
# pairs have been found or all eligible pairs have been tested.
#
# Parameters:
# - sequence_pairs (list): List of (index, (seq, rc_seq)) tuples.
# - energy_min (float): Minimum allowed Gibbs free energy (inclusive).
# - energy_max (float): Maximum allowed Gibbs free energy (inclusive).
# - max_size (int): Maximum number of pairs to return.
# - Use_Library (bool): Whether to use and update the precomputed energy library.
# - avoid_indices (set): Set of indices to skip during selection.
#
# Returns:
# - list: A list of (seq, rc_seq) pairs within the specified energy range.
# - list: Their corresponding indices in the original pool.
def select_subset_in_energy_range(sequence_pairs, energy_min=-np.inf, energy_max=np.inf, max_size=np.inf,
                                  Use_Library=None, avoid_indices=None):
    
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

# Selects all sequence pairs whose on-target energies fall within a given range.
#
# This function iterates over all (ID, (sequence, rc_sequence)) tuples in the input list
# and computes the hybridization energy for each using a precomputed energy library (if enabled).
# It skips any IDs listed in `avoid_ids`. All matching pairs within the specified energy range
# are returned. The selection is deterministic and processes the list in order.
#
# Parameters:
# - sequence_pairs (list): List of (ID, (seq, rc_seq)) tuples.
# - energy_min (float): Minimum allowed Gibbs free energy (inclusive).
# - energy_max (float): Maximum allowed Gibbs free energy (inclusive).
# - Use_Library (bool): Whether to use and update the precomputed energy library.
# - avoid_ids (set): Set of IDs to skip during selection.
#
# Returns:
# - list: A list of (seq, rc_seq) pairs within the specified energy range.
# - list: Their corresponding IDs from the original pool.
def select_all_in_energy_range(sequence_pairs, energy_min=-np.inf, energy_max=np.inf, Use_Library=None, avoid_ids=None):
    
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


# Plots histograms of on-target and off-target energies and returns and prints summary statistics.
#
# The `off_energies` argument can either be:
# - a 1D array of energy values, or
# - a dictionary output from `compute_offarget_energies`.
#
# Returns a dictionary containing mean, standard deviation, and max of on-target energies,
# as well as mean, standard deviation, and min of off-target energies.
#
# Keys:
#     'mean_on'  : mean of on-target energies
#     'std_on'   : standard deviation of on-target energies
#     'max_on'   : maximum of on-target energies
#     'mean_off' : mean of off-target energies
#     'std_off'  : standard deviation of off-target energies
#     'min_off'  : minimum of off-target energies
def plot_on_off_target_histograms(on_energies, off_energies, bins=80, output_path=None):

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
    


 