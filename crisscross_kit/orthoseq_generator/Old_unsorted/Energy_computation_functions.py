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


def revcom(sequence):
    # Computes reverse complemt of a DNA sequence saved as a string
    dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return "".join(dna_complement[n] for n in reversed(sequence))


def sorted_key(seq1, seq2):
    return (min(seq1, seq2), max(seq1, seq2))


def nupack_compute_energy(seq1, seq2, samples = 10, type = 'total'):

    #use total for the total gibbs free energy
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

def nupack_compute_energy_TT_self(seq1, seq2, samples = 1, type = 'total', Use_Library= False):

    #use total for the total gibbs free energy
    # use minimum for the minimum free energy of the secondary strucutre
    # whe catch here the exception that the strands dont bind at all. In this case we set the binding energy to -1 which is almost +infinity
    A = Strand(''+seq1 , name='H1')  # name is required for strands
    B = Strand(''+seq2  , name='H2')
    library1= {}
    if Use_Library:
        if not hasattr(nupack_compute_energy_TT_self, "library_cache"):
            file_name = "OLD_SCRIPTS/interactions_matrix.pkl"
            if os.path.exists(file_name):
                with open(file_name, "rb") as file:
                    nupack_compute_energy_TT_self.library_cache = pickle.load(file)
            else:
                nupack_compute_energy_TT_self.library_cache = {}

        library1 = nupack_compute_energy_TT_self.library_cache
        #print("access library use")

    if  Use_Library and (sorted_key(seq1, seq2) in library1):
        return library1[sorted_key(seq1, seq2)]
    else:
        try:
            if seq1==seq2:
                #print('I was here')
                HHcomplex = '(H1+H1)'
                B= Strand( 'TTT', name='H2')

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
            # This block will execute if any error caught that is a subclass of Exception
            print(f"The following error occurred: {e}")
            print(seq1, seq2)
            return -1.0


def compute_matching_energies(handles):
    #computes the binding energy of a sequence of with its reverse complement
    energies = np.zeros(len(handles))
    #print(handles)
    for i in range((len(handles))):
        #print(i)
        energies[i] = nupack_compute_energy_TT_self(handles[i], revcom(handles[i]),samples=100, type='total')
    return energies


# Function to compute energy for a pair of sequences
def compute_pair_energy(i, j, seq1, seq2, Use_Library):
    #return i, j, nupack_compute_energy(seq1, seq2)
    return i, j, nupack_compute_energy_TT_self(seq1, seq2, Use_Library = Use_Library)

def selfvalidate(sequences, Report_energies=True, Use_Library= True):
    handles = sequences
    antihandles = [revcom(seq) for seq in sequences]

    crosscorrelated_handle_handle_energies = np.zeros((len(handles), len(handles)))
    crosscorrelated_antihandle_antihandle_energies = np.zeros((len(antihandles), len(antihandles)))
    crosscorrelated_handle_antihandle_energies = np.zeros((len(handles), len(antihandles)))

    # Define a function for parallel processing
    def parallel_energy_computation(seqs1, seqs2, energy_matrix, condition):
        max_workers = max(1, os.cpu_count() * 1 // 3)
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
        file_name = "OLD_SCRIPTS/interactions_matrix.pkl"
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

def crossvalidate(sequences1, sequences2, All_combindations=True, Report_energies=True):

    handles1 = sequences1

    if All_combindations == True:
        antihandles1 = [revcom(seq) for seq in sequences1]
    else:
        antihandles1 = []
    allsequences1 = handles1 + antihandles1

    handles2 = sequences2

    antihandles2 = [revcom(seq) for seq in sequences2]
    allsequences2 = handles2 + antihandles2

    crosscorrelated_sequence1_sequence2_energies = np.zeros((len(allsequences1), len(allsequences2)))

    for i, sequence1_i in enumerate(allsequences1):
        for j, sequence2_j in enumerate(allsequences2):
            test = nupack_compute_energy_TT_self(sequence1_i, sequence2_j)
            crosscorrelated_sequence1_sequence2_energies[i, j] = test

    # Calculate minimum energy across both matrices
    try:
        minimum_energy = np.min(crosscorrelated_sequence1_sequence2_energies)
        mean_energy = np.mean(crosscorrelated_sequence1_sequence2_energies)
    except Exception as e:
        print(f"An error occurred: {e}")
        minimum_energy = 0
        mean_energy = 0

    if Report_energies == True:
        return {
            'all_energies': crosscorrelated_sequence1_sequence2_energies.flatten(),
            'min_energy': minimum_energy,
            'mean_energy': mean_energy
        }
    else:
        return {
            'min_energy': minimum_energy,
            'mean_energy': mean_energy
        }


if __name__ == "__main__":
    # run test to see if the functions above work

    testseq = 'ATGCCCGTCG'
    print(revcom(testseq))

    testenergy= nupack_compute_energy_TT_self(testseq, revcom(testseq))
    print(testenergy)

    testenergy= nupack_compute_energy_TT_self(testseq, revcom(testseq),samples=100)
    print(testenergy)

    testenergy= nupack_compute_energy_TT_self(testseq, testseq,samples=100)
    print(testenergy)

    with open(os.path.join('.', 'core_32_sequences.pkl'), 'rb') as f:
        antihandles, handles = pickle.load(f)
    print(handles)
    test_energy_list = compute_matching_energies(handles)
    print(test_energy_list)
    print('here')
    test_sequence_list = ['ACATGTA']

    result= selfvalidate(test_sequence_list, Report_energies=True,Use_Library=False)

    print(result)
    print(result['all_energies'])
    print(result['handle_handle_energies'])

    more_test_sequences = ['AAAACCTTTCG', 'AGCGGGGTCG', 'ATTTTTTCTTCG']

    cresult = crossvalidate(test_sequence_list, more_test_sequences, Report_energies=True)
    print(cresult)
    print(cresult['all_energies'])