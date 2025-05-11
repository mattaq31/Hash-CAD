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

from Handle_Library_Generator.Old_unsorted.Energy_computation_functions import selfvalidate


def revcom(sequence):
    # Computes reverse complemt of a DNA sequence saved as a string
    dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return "".join(dna_complement[n] for n in reversed(sequence))

# Function to check if a sequence contains four consecutive G's, C's, A's, or T's
def has_four_consecutive_bases(seq):
    return 'GGGG' in seq or 'CCCC' in seq or 'AAAA' in seq or 'TTTT' in seq

def sorted_key(seq1, seq2):
    return (min(seq1, seq2), max(seq1, seq2))


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

def get_library_path():
    return "pre_computed_energies/interactions_matrix.pkl"

def nupack_compute_energy_precompute_library(seq1, seq2, samples = 1, type = 'total', Use_Library= True, fivep_ext="TT", threep_ext=""):

    #use total for the total gibbs free energy
    # use minimum for the minimum free energy of the secondary strucutre
    # we catch here the exception that the strands don't bind at all. In this case we set the binding energy to -1 which is almost +infinity
    A = Strand(fivep_ext+seq1+threep_ext, name='H1')  # name is required for strands
    B = Strand(fivep_ext+seq2+threep_ext , name='H2')
    library1= {}
    if Use_Library:
        #check if the precopute library was already loaded. if not open it
        if not hasattr(nupack_compute_energy_precompute_library, "library_cache"):
            #load library form here
            file_name = get_library_path()
            #if it exists load it else create a new one
            if os.path.exists(file_name):
                with open(file_name, "rb") as file:
                    nupack_compute_energy_precompute_library.library_cache = pickle.load(file)
            else:
                nupack_compute_energy_precompute_library.library_cache = {}
        # put precompute library in a convienient variable
        library1 = nupack_compute_energy_precompute_library.library_cache
        #print("access library use")
    #if the precompute library should be used and the energy has been computed, return it imidiatly
    if  Use_Library and (sorted_key(seq1, seq2) in library1):
        return library1[sorted_key(seq1, seq2)]
    else:
        try:
            # if we ask for the sequence binding to itself extract a different value from nupack (H2) sequence in complex with itself
            if seq1==seq2:
                #print('I was here')
                HHcomplex = '(H1+H1)'
                B= Strand( 'TTT', name='H2') # TTT is a dummy sequence here

            else:
                 HHcomplex = '(H1+H2)'

            t1 = Tube(strands={A: 100e-6, B: 100e-6}, complexes=SetSpec(max_size=2), name='t1')
            # analyze tubes
            model1 = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.025)
            tube_results = tube_analysis(tubes=[t1], model=model1, compute=['pairs', 'mfe', 'sample'], options={'num_sample': samples})

            #print(tube_results)
            if type == 'minimum':
                energy = tube_results[HHcomplex].mfe[0].energy
            elif type == 'total':
                energy = tube_results[HHcomplex].free_energy
                if energy >0:
                    energy = -1.0
            else:
                raise ValueError('type must be either "minimum" or "total"')
            #print(energy)
            return energy
        except Exception as e:
            # This block will execute if any error caught that is a subclass of Exception. It might just be that the sequences do not interact
            print(f"The following error occurred: {e}")
            print(seq1, seq2)
            return -1.0





def preselect_sequences_and_analize(lenght=7,fivep_ext="TT", threep_ext="",avoid_gggg=True,Use_Library=True):
    # Define the DNA bases
    bases = ['A', 'T', 'G', 'C']
    n_mers = [''.join(mer) for mer in itertools.product(bases, repeat=lenght)]
    unique_seven_mers = []
    for mer in n_mers:
        rc_mer = revcom(mer)
        if mer not in unique_seven_mers and rc_mer not in unique_seven_mers:
            unique_seven_mers.append(mer)

    # remove GGGG and CCCC and etc
    if avoid_gggg==True:
        filtered_final_list = []
        for mer in unique_seven_mers:
            if not has_four_consecutive_bases(mer):
                filtered_final_list.append(mer)
    else:
        filtered_final_list = unique_seven_mers


    return compute_ontarget_energies(filtered_final_list,fivep_ext=fivep_ext,threep_ext=threep_ext,Use_Library=Use_Library)


def compute_ontarget_energies(sequence_list, fivep_ext="TT", threep_ext="",Use_Library=True):
    # Preallocate array for better performance
    energies = np.zeros(len(sequence_list))

    # Fill the array with computed energies
    print(f"Computing energies for {len(sequence_list)} sequences...")

    # Wrap the loop in a tqdm progress bar
    for i, seq in tqdm(enumerate(sequence_list), total=len(sequence_list)):
        on_energy = nupack_compute_energy_precompute_library(
            seq,
            revcom(seq),
            samples=1,
            type='total',
            Use_Library=Use_Library,
            fivep_ext=fivep_ext,
            threep_ext=threep_ext
        )
        energies[i] = on_energy

    # update the precompute library to  make things faster in the future
    if Use_Library:
        file_name = get_library_path()
        if os.path.exists(file_name):
            with open(file_name, "rb") as file:
                library1 = pickle.load(file)
        else:
            library1 = {}

        for i, seq in enumerate(sequence_list):
            library1[sorted_key(seq, revcom(seq))] = energies[i]
       # Save the updated dictionary
        print(library1)
        with open(file_name, "wb") as file:
            pickle.dump(library1, file)


    return energies

# helper function for parralel computing
def compute_pair_energy(i, j, seq1, seq2, Use_Library):
    # return i, j, nupack_compute_energy(seq1, seq2)
    return i, j, nupack_compute_energy_precompute_library(seq1, seq2, Use_Library=Use_Library)

def compute_offarget_energies(sequences, Use_Library= True):
    handles = sequences
    antihandles = [revcom(seq) for seq in sequences]

    crosscorrelated_handle_handle_energies = np.zeros((len(handles), len(handles)))
    crosscorrelated_antihandle_antihandle_energies = np.zeros((len(antihandles), len(antihandles)))
    crosscorrelated_handle_antihandle_energies = np.zeros((len(handles), len(antihandles)))

    # Function to compute energy for a pair of sequences



    # Define a function for parallel processing
    def parallel_energy_computation(seqs1, seqs2, energy_matrix, condition):
        max_workers = max(1, os.cpu_count() * 3// 4)
        print(f'Calculating with {max_workers} cores...')
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, seq1 in enumerate(seqs1):
                for j, seq2 in enumerate(seqs2):
                    if condition(i, j):
                        futures.append(executor.submit(compute_pair_energy, i, j, seq1, seq2, Use_Library))

            for future in tqdm(as_completed(futures), total=len(futures)):
                i, j, energy = future.result()
                energy_matrix[i, j] = energy

    # Parallelize handle-handle energy computation
    parallel_energy_computation(handles, handles, crosscorrelated_handle_handle_energies, lambda i, j: j <= i)

    # Parallelize antihandle-antihandle energy computation
    parallel_energy_computation(antihandles, antihandles, crosscorrelated_antihandle_antihandle_energies, lambda i, j: j <= i)

    # Parallelize handle-antihandle energy computation
    parallel_energy_computation(handles, antihandles, crosscorrelated_handle_antihandle_energies, lambda i, j: j != i)

    # Combine the results as in the original function
    all_combined = np.concatenate((
        crosscorrelated_handle_handle_energies.flatten(),
        crosscorrelated_antihandle_antihandle_energies.flatten(),
        crosscorrelated_handle_antihandle_energies.flatten()
    ))
    all_combined = all_combined[all_combined != 0]

    # Calculate the minimum energy
    min_handle_handle_energy = np.min(crosscorrelated_handle_handle_energies)
    min_handle_antihandle_energy = np.min(crosscorrelated_handle_antihandle_energies)
    minimum_energy = min(min_handle_handle_energy, min_handle_antihandle_energy)

    #update the precompute library to  make things faster in the futur
    if Use_Library:
        file_name = get_library_path()
        if os.path.exists(file_name):
            with open(file_name, "rb") as file:
                library1 = pickle.load(file)
        else:
            library1 = {}

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
        print(library1)
        with open(file_name, "wb") as file:
            pickle.dump(library1, file)

    # Report energies if required

    return{
            'handle_handle_energies': crosscorrelated_handle_handle_energies,
            'antihandle_handle_energies': crosscorrelated_handle_antihandle_energies,
            'antihandle_antihandle_energies': crosscorrelated_antihandle_antihandle_energies
            }



if __name__ == "__main__":
    # run test to see if the functions above work


    ontarget6mer=preselect_sequences_and_analize(lenght=5,fivep_ext="TT", threep_ext="",avoid_gggg=True,Use_Library=True)


    testseq1 = 'ATGCCCGTCG'
    print(revcom(testseq1))
    testseq2 = 'GTAGCCATGC'
    testenergy= nupack_compute_energy_precompute_library(testseq1, revcom(testseq1),Use_Library=False)
    print(testenergy)

    testenergy= nupack_compute_energy_precompute_library(testseq1, testseq2,samples=1,Use_Library=False)
    print(testenergy)

    testenergy= nupack_compute_energy_precompute_library(testseq1, testseq2,samples=100,Use_Library=False)
    print(testenergy)


    test_sequence_list = ['ACATGTA','ATGCCCGTCG']

    result= compute_offarget_energies(test_sequence_list,Use_Library=False)

    print(result)
    print(result['handle_handle_energies'])

    more_test_sequences = [
        'TACCGTGTCA', 'ACGTTAGCTT', 'GTAGCCATGC', 'CTAGTACGTA', 'AGCTGGTACC',
        'TTAGCGATCG', 'CGTACCGTTA', 'GATCCTAGTC', 'ATCGGTAGCA', 'GGTACGCTTA',
        'CCGATAGGTA', 'TTCAGGCTAA', 'GATCGTACCT', 'CTAGGATGCA', 'AGCGTAGTTC',
        'TATCGGTACC', 'GCTAGGTACG', 'CATGCTAGAT', 'TAGCGTATCC', 'ACGTGATGTA',
        'TGACGATTAC', 'GCTTACGTAG', 'ATGCGTACTT', 'CGATCGGATA', 'TTAGCGGTCA',
        'GATTAGCTGC', 'CTTACGTAGC', 'AGTCAGTGCT', 'TGCATCGTGA', 'CGTAGCATAC',
        'GACGTACGTA', 'TCCGATGCAT', 'ACGATTCGGA', 'GTAGGATACC', 'CCGTTAGGTA',
        'TATCGGATAG', 'AGGTCGATAC', 'GCTAGCTAAC', 'ATCGTTAGGA', 'TTAGCATGCT',
        'CATGCGGTAC', 'GGATAGTCCA', 'TACGGATGCT', 'CTAGGTAGTC', 'ACGGTACGTA',
        'TTAGGCTTAC', 'GTACGGTATC', 'CGATAGTACC', 'GATACGTAGC', 'TTCAGGATCG',
        'CCGTAGCTAA', 'TAGCTAGTAC', 'ACGTAGTCCA', 'GGTAGCTACC', 'TTGACGTAGC',
        'GCTTAGGCAT', 'CTAGCGTACC', 'AGCTGTCGAT', 'TGCATGGTAA', 'CGGTACCTGA',
        'ATCGGATACC', 'GATCGTACTT', 'TTAGCTGACC', 'AGGCTAGTCA', 'GTAGGCTAAC',
        'TCCGATAGTC', 'CTAGGATAGT', 'CGTACGATGA', 'GCTAGTAGGA', 'ATGCCGTAGT',
        'TAGGATACCT', 'ACGTTCGTAG', 'GATACGGTTA', 'TTCAGCTGAT', 'CCGATGCTAC',
        'AGTACGATGC', 'GTTCAGTACC', 'TACGTGATCG', 'CTAGTGGATC', 'GCTAGGTACC',
        'ATCGTTAGCA', 'CGTACGGATG', 'TTAGCGTATG', 'AGCTAGTTCA', 'GATAGCTACC',
        'TTCAGGATAG', 'CCGTAGGTCA', 'TAGCGTAGAT', 'ACGTAGCGTA', 'GCTTAGTACC',
        'CTAGGCTAGC', 'ATGCGGTACC', 'TTAGCTAGGA', 'GTAGCTGTAC', 'CGATGTACTT',
        'GATCCGTAGT', 'TTCAGTTACC', 'CCGTAGCTGA', 'TAGCTAGATC', 'ACGTTAGCAT',
        'GGTACGTACC', 'TACGGCTAGT', 'CTAGGTAGAT', 'AGCTGTAGCC', 'GATCGTAGAT'
    ]
# run twice to see if use_library makes a difference
    cresult = compute_offarget_energies(more_test_sequences, Use_Library=True)
    print(cresult)
    print(cresult['all_energies'])