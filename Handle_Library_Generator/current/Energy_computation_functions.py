import pickle
import os
import itertools
from matplotlib.style.core import library
from nupack import *
import numpy as np
import matplotlib.pyplot as plt
from nupack.rotation import sample_state
from tqdm import tqdm
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from matplotlib.ticker import AutoMinorLocator
import time


# Computes the reverse complement of a DNA sequence (input and output are strings).
def revcom(sequence):
    dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return "".join(dna_complement[n] for n in reversed(sequence))

# Returns True if the sequence contains four identical consecutive bases (e.g., "GGGG", "CCCC", etc.)
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
def create_sequence_pairs_pool(length=7, fivep_ext="TT", threep_ext="", avoid_gggg=True):

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

    return unique_flanked_n_mers






# Helper function that returns the file path to the precomputed energy library.
# This path points to a pickle file containing a dictionary of previously calculated Gibbs free energies.
# Change this path if you want to generate a new energy library from scratch.
def get_library_path():
    return "pre_computed_energies/interactions_matrix.pkl"

# Computes the Gibbs free energy of hybridization between two DNA sequences using NUPACK.
#
# Parameters:
# - seq1, seq2 (str): DNA sequences to be analyzed.
# - samples (int): Number of samples used in NUPACK's sampling routine. For short sequences (<10 bp),
#   varying this number does not change results. I tested this!
# - type (str): Either 'total' or 'minimum'.
#       - 'total': Computes the total/ summed up Gibbs free energy from all possible secondary structures.
#       - 'minimum': Returns the energy of the most stable (minimum free energy) structure only.
#       - Changing this parameter (from 'total' to 'minimum' or vice versa) will require you to delete the precomputed energy library file.
#         The library does not store metadata about the computation type, so mixing types will lead to incorrect results.
#
# - Use_Library (bool): If True, attempts to use a precomputed energy value from a local library (cache).
#
# Returns:
# - float: Gibbs free energy in kcal/mol.
#          If the strands do not interact or an error occurs, returns -1.0 (interpreted as "no interaction").
#          A Gibbs free energy is of -1 is already very weak in comparison to commonly computed values
# Notes:
# - The precomputed energy library is cached on first access to avoid repeated disk I/O.
# - Energies are stored using a canonical sorted key to ensure (seq1, seq2) and (seq2, seq1) map to the same value.
def nupack_compute_energy_precompute_library(seq1, seq2, samples = 1, type = 'total', Use_Library= False):


    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    library1= {}
    key= sorted_key(seq1, seq2)
    if Use_Library:
        #check if the precopute library was already loaded. if not open it
        if not hasattr(nupack_compute_energy_precompute_library, "library_cache"):
            #load library form here
            file_name = get_library_path()
            #if it exists load it, else create a new one
            if os.path.exists(file_name):
                with open(file_name, "rb") as file:
                    nupack_compute_energy_precompute_library.library_cache = pickle.load(file)
            else:
                nupack_compute_energy_precompute_library.library_cache = {}
        # put precompute library in a convenient variable
        library1 = nupack_compute_energy_precompute_library.library_cache

    #if the precompute library should be used and the energy has been computed, return it immediately
    if  Use_Library and (key in library1):
        return library1[key]
    else:
        #we catch here the exception that the strands don't bind at all. In this case we set the binding energy to -1 which is almost +infinity
        try:
            # if we ask for the sequence binding to itself extract a different value from nupack: (H1+H1)
            if seq1==seq2:
                HHcomplex = '(H1+H1)'
                B= Strand( 'TTT', name='H2') # TTT is a dummy sequence here otherwise it wont run

            else:
                 HHcomplex = '(H1+H2)'

            # parameters for the computation
            t1 = Tube(strands={A: 100e-6, B: 100e-6}, complexes=SetSpec(max_size=2), name='t1')
            model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.025)

            # Do the actual gibbs free energy computation
            tube_results = tube_analysis(tubes=[t1], model=model1, compute=['pairs', 'mfe', 'sample'], options={'num_sample': samples})

            # unpack what was asked for i.e. minimum or total gibbs free energy
            if type == 'minimum':
                energy = tube_results[HHcomplex].mfe[0].energy
            elif type == 'total':
                energy = tube_results[HHcomplex].free_energy
                # Set weak/non-binding interaction to -1.0.
                # Note: We reserve 0.0 to indicate "not yet computed" in other parts of the code,
                # so -1.0 serves as a placeholder for effectively no binding (very weak interaction).
                if energy >0:
                    energy = -1.0
            else:
                raise ValueError('type must be either "minimum" or "total"')

            return energy
        except Exception as e:
            # This block will execute if any error caught that is a subclass of Exception. It might just be that the sequences do not interact
            print(f"The following error occurred: {e}")
            print(seq1, seq2)
            return -1.0

# This is an older version of the energy computation function.
# It does not use a precomputed library, so it computes everything from scratch.
def nupack_compute_energy(seq1, seq2, samples = 10, type = 'total'):

    # use total for the total gibbs free energy
    # use minimum for the minimum free energy of the secondary strucutre
    # whe catch here the exception that the strands dont bind at all. In this case we set the binding energy to -1 which is almost +infinity
    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    try:
        t1 = Tube(strands={A: 1e-8, B: 1e-8}, complexes=SetSpec(max_size=2), name='t1')
        # analyze tubes
        model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.025)
        tube_results = tube_analysis(tubes=[t1], model=model1, compute=['pairs', 'mfe', 'sample'], options={'num_sample': samples})
        #print(tube_results)
        if type == 'minimum':
            energy = tube_results['(H1+H2)'].mfe[0].energy
        elif type == 'total':
            energy = tube_results['(H1+H2)'].free_energy
            if energy >0:
                energy = -1
        else:
            raise ValueError('type must be either "minimum" or "total"')
        #print(energy)
        return energy
    except Exception as e:
        # This block will execute if any error caught that is a subclass of Exception
        print(f"The following error occurred: {e}")
        return -1.0

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
#
# Notes:
# - Uses complex_analysis for speed. Much faster than tube_analysis.
# - The precomputed energy library is cached on first access to avoid repeated disk I/O.
# - Energies are stored using a canonical sorted key to ensure (seq1, seq2) and (seq2, seq1) map to the same value.
def nupack_compute_energy_precompute_library_fast(seq1, seq2, samples=1, type='total', Use_Library=False):

    A = Strand(seq1, name='H1')  # name is required for strands
    B = Strand(seq2, name='H2')
    library1 = {}
    key = sorted_key(seq1, seq2)

    # Try loading from library if requested
    if Use_Library:
        if not hasattr(nupack_compute_energy_precompute_library_fast, "library_cache"):
            file_name = get_library_path()
            if os.path.exists(file_name):
                with open(file_name, "rb") as file:
                    nupack_compute_energy_precompute_library_fast.library_cache = pickle.load(file)
            else:
                nupack_compute_energy_precompute_library_fast.library_cache = {}
        library1 = nupack_compute_energy_precompute_library_fast.library_cache

    # Return value from cache if available
    if Use_Library and key in library1:
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


# helper function for parallel computing on-target energies
def compute_pair_energy_on(i, seq, rc_seq, Use_Library):
    return i, nupack_compute_energy_precompute_library_fast(seq, rc_seq, samples=1, Use_Library=Use_Library)


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
def compute_ontarget_energies(sequence_list, Use_Library=False):
    # Preallocate array for better performance
    energies = np.zeros(len(sequence_list))

    # Announce what is about to happen
    print(f"Computing on-target energies for {len(sequence_list)} sequences...")

    max_workers = max(1, os.cpu_count() * 3 // 4)
    print(f"Calculating with {max_workers} cores...")

    # parallelize energy computation
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, (seq, rc_seq) in enumerate(sequence_list):
            futures.append(executor.submit(compute_pair_energy_on, i, seq, rc_seq, Use_Library))

        for future in tqdm(as_completed(futures), total=len(futures)):
            i, energy = future.result()
            energies[i] = energy

    # update the precompute library if required
    if Use_Library:
        # save to existing library or create a new one
        file_name = get_library_path()

        if os.path.exists(file_name):
            # open library if exists
            with open(file_name, "rb") as file:
                library1 = pickle.load(file)
        else:
            library1 = {}

        for i, (seq, rc_seq) in enumerate(sequence_list):
            library1[sorted_key(seq, rc_seq)] = energies[i]

        # Save the updated dictionary
        with open(file_name, "wb") as file:
            pickle.dump(library1, file)

    return energies



# helper function for parallel computing off target energies
def compute_pair_energy_off(i, j, seq1, seq2, Use_Library):
    # return i, j, nupack_compute_energy(seq1, seq2)
    return i, j, nupack_compute_energy_precompute_library_fast(seq1, seq2, Use_Library=Use_Library)
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
def compute_offtarget_energies(sequence_pairs, Use_Library= True):
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
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, seq1 in enumerate(seqs1):
                for j, seq2 in enumerate(seqs2):
                    if condition(i, j):
                        futures.append(executor.submit(compute_pair_energy_off, i, j, seq1, seq2, Use_Library))

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
    if Use_Library:
        file_name = get_library_path()
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
        with open(file_name, "wb") as file:
            pickle.dump(library1, file)

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
def select_subset(sequence_pairs, max_size=200):

    if len(sequence_pairs) > max_size:
        subset = random.sample(sequence_pairs, max_size)
        print(f"Selected random subset of {max_size} pairs from {len(sequence_pairs)} available pairs.")
    else:
        subset = sequence_pairs
        print(f"Using all {len(sequence_pairs)} available pairs (less than or equal to {max_size}).")
    return subset


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
    # Define test sequences
    seq1 = "ATGCGTGCCTT"
    seq2 = revcom(seq1)  # Should be complementary

    print("=== Testing Energy Computation ===")

    # --- Old tube-based: total ---
    start = time.time()
    energy_old_total = nupack_compute_energy_precompute_library(seq1, seq2, type="total", Use_Library=False)
    end = time.time()
    print(f"OLD total   (tube):     {energy_old_total:.3f} kcal/mol   Time: {end - start:.3f}s")

    # --- New complex-based: total ---
    start = time.time()
    energy_new_total = nupack_compute_energy_precompute_library_fast(seq1, seq2, type="total", Use_Library=False)
    end = time.time()
    print(f"NEW total   (complex):  {energy_new_total:.3f} kcal/mol   Time: {end - start:.3f}s")

    # --- Old tube-based: minimum ---
    start = time.time()
    energy_old_min = nupack_compute_energy_precompute_library(seq1, seq2, type="minimum", Use_Library=False)
    end = time.time()
    print(f"OLD minimum (tube):     {energy_old_min:.3f} kcal/mol   Time: {end - start:.3f}s")

    # --- New complex-based: minimum ---
    start = time.time()
    energy_new_min = nupack_compute_energy_precompute_library_fast(seq1, seq2, type="minimum", Use_Library=False)
    end = time.time()
    print(f"NEW minimum (complex):  {energy_new_min:.3f} kcal/mol   Time: {end - start:.3f}s")

    # --- Comparison assertions ---
    assert abs(energy_old_total - energy_new_total) < 0.1, "Total energy mismatch!"
    assert abs(energy_old_min - energy_new_min) < 0.1, "Minimum energy mismatch!"






    # run test to see if the functions above work
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    ontarget7mer=create_sequence_pairs_pool(length=13,fivep_ext="", threep_ext="",avoid_gggg=False)

    subset = select_subset(ontarget7mer, max_size=100*100)
    on_e = compute_ontarget_energies(subset, Use_Library=False)

    # Select a random subset if there are more than 400 pairs
    subset = select_subset(ontarget7mer, max_size=100)

    # Compute the off-target energies for the subset
    off_e_subset = compute_offtarget_energies(subset, Use_Library=False)
    stats = plot_on_off_target_histograms(on_e, off_e_subset, output_path='energy_hist.pdf')

