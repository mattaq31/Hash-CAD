import pickle
import os

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

def nupack_compute_energy_precompute_library(seq1, seq2, samples = 1, type = 'total', Use_Library= False, fivep_ext="TT", threep_ext=""):

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
            file_name = "pre_computed_energies/interactions_matrix.pkl"
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


def compute_ontarget_energies(handles):
    #computes the binding energy of a sequence of with its reverse complement
    energies = np.zeros(len(handles))
    #print(handles)
    for i in range((len(handles))):
        #print(i)
        energies[i] = nupack_compute_energy_precompute_library(handles[i], revcom(handles[i]), samples=100, type='total')
    return energies

def compute_pair_energy(i, j, seq1, seq2, Use_Library):
    # return i, j, nupack_compute_energy(seq1, seq2)
    return i, j, nupack_compute_energy_precompute_library(seq1, seq2, Use_Library=Use_Library)


def compute_offarget_energies(sequences, Report_energies=True, Use_Library= True):
    handles = sequences
    antihandles = [revcom(seq) for seq in sequences]

    crosscorrelated_handle_handle_energies = np.zeros((len(handles), len(handles)))
    crosscorrelated_antihandle_antihandle_energies = np.zeros((len(antihandles), len(antihandles)))
    crosscorrelated_handle_antihandle_energies = np.zeros((len(handles), len(antihandles)))

    # Function to compute energy for a pair of sequences



    # Define a function for parallel processing
    def parallel_energy_computation(seqs1, seqs2, energy_matrix, condition):
        max_workers = max(1, os.cpu_count() * 3// 4)
        print('calculating with ... cores')
        print(max_workers)
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

    if Use_Library:
        file_name = "pre_computed_energies/interactions_matrix.pkl"
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
    if Report_energies:
        return {
            'handle_handle_energies': crosscorrelated_handle_handle_energies,
            'antihandle_handle_energies': crosscorrelated_handle_antihandle_energies,
            'antihandle_antihandle_energies': crosscorrelated_antihandle_antihandle_energies,
            'all_energies': all_combined,
            'min_energy': minimum_energy
        }
    else:
        return {'min_energy': minimum_energy}


if __name__ == "__main__":
    # run test to see if the functions above work

    testseq = 'ATGCCCGTCG'
    print(revcom(testseq))

    testenergy= nupack_compute_energy_precompute_library(testseq, revcom(testseq))
    print(testenergy)

    testenergy= nupack_compute_energy_precompute_library(testseq, revcom(testseq),samples=100)
    print(testenergy)

    testenergy= nupack_compute_energy_precompute_library(testseq, testseq,samples=100)
    print(testenergy)

    with open(os.path.join('.', 'core_32_sequences.pkl'), 'rb') as f:
        antihandles, handles = pickle.load(f)
    print(handles)
    test_energy_list = compute_ontarget_energies(handles)
    print(test_energy_list)
    print('here')
    test_sequence_list = ['ACATGTA','ATGCCCGTCG']

    result= compute_offarget_energies(test_sequence_list, Report_energies=True,Use_Library=False)

    print(result)
    print(result['all_energies'])
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
        'GGTACGTACC', 'TACGGCTAGT', 'CTAGGTAGAT', 'AGCTGTAGCC', 'GATCGTAGAT',
        'TTAGCGGATG', 'CATGCTGGTA', 'GTAGCCTAGT', 'CGATGTTAGC', 'ATGCGTTACC',
        'TAGCGTACCA', 'ACGTAGTCCA', 'GCTAGCATGA', 'TTGATGCTAA', 'CCGTAGGATC',
        'CTAGTTGACC', 'GATCGCTAGT', 'TTCAGGTAGC', 'CGTACGTGAT', 'TAGCTAGCTA',
        'GCTAGTCGTA', 'ATGCGTAGCA', 'ACGTTCGATG', 'GTAGTTAGCA', 'TTCAGCGTAC',
        'GATCGTTACC', 'CCGTAGTGCA', 'TACGGATCGT', 'AGTACGGTAA', 'GCTTAGCTGA',
        'TAGGATCGTA', 'ACGTTGATGC', 'GTACGATGTC', 'CTAGGCTGTA', 'CGTAGGCTAA',
        'ATCGTGATAC', 'TTAGGCGTAC', 'CATGGTAGTA', 'GTAGCGATGC', 'CGATCGTAGT',
        'GATACGTGAT', 'TTCAGTGCTA', 'CCGTAGTAGC', 'TAGCTGGTAA', 'ACGTAGTACC',
        'GCTTAGGATG', 'CTAGCGGTAC', 'AGCTGCTAGC', 'TGCATCGTAC', 'CGGTAGCTTA',
        'ATCGGATAGC', 'GATCGTACTG', 'TTAGCTGATC', 'AGGCTAGTAC', 'GTAGGCTAAT',
        'TCCGATAGTC', 'CTAGGATGTC', 'CGTACGCTGA', 'GCTAGTAGCA', 'ATGCCGTACC',
        'TAGGATAGCT', 'ACGTTCGTGA', 'GATACGGTAC', 'TTCAGCTGTC', 'CCGATGCTAT',
        'AGTACGCTGA', 'GTTCAGTACC', 'TACGTGATCG', 'CTAGTGGATG', 'GCTAGGTAGC',
        'ATCGTTAGCT', 'CGTACGGATT', 'TTAGCGTATT', 'AGCTAGTTCT', 'GATAGCTACT',
        'TTCAGGATAC', 'CCGTAGGTCT', 'TAGCGTAGAC', 'ACGTAGCGTT', 'GCTTAGTACA',
        'CTAGGCTAGT', 'ATGCGGTACC', 'TTAGCTAGAT', 'GTAGCTGTAA', 'CGATGTACTG',
        'GATCCGTAGC', 'TTCAGTTACA', 'CCGTAGCTGT', 'TAGCTAGATT', 'ACGTTAGCAA',
        'GGTACGTACA', 'TACGGCTAGA', 'CTAGGTAGAG', 'AGCTGTAGCT', 'GATCGTAGAC'
    ]

    cresult = compute_offarget_energies(more_test_sequences, Report_energies=True, Use_Library=True)
    print(cresult)
    print(cresult['all_energies'])