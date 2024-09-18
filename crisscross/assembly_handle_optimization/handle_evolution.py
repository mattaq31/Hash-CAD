import os
from collections import defaultdict
import pandas as pd
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import multiprocessing
import time
import matplotlib.ticker as ticker
from colorama import Fore

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, multirule_precise_hamming
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization import generate_random_slat_handles, generate_layer_split_handles
from crisscross.helper_functions import save_list_dict_to_file


def mutate_handle_arrays(slat_array, candidate_handle_arrays,
                         hallofshame_handles, hallofshame_antihandles,
                         best_score_indices, unique_sequences=32,
                         mutation_rate=1.0, split_sequence_handles=False):
    """
    Mutates (randomizes handles) a set of candidate arrays into a new generation,
    while retaining the best scoring arrays  from the previous generation.
    :param slat_array: Base slat array for design
    :param candidate_handle_arrays: Set of candidate handle arrays from previous generation
    :param hallofshame_handles: Worst handle combinations from previous generation
    :param hallofshame_antihandles: Worst antihandle combinations from previous generation
    :param best_score_indices: The indices of the best scoring arrays from the previous generation
    :param unique_sequences: Total length of handle library available
    :param mutation_rate: If a handle is selected for mutation, the probability that it will be changed
    :param split_sequence_handles: Set to true if the handle library needs to be split between subsequent layers
    :return: New generation of handle arrays to be screened
    """

    # These are the arrays that will be mutated
    mutated_handle_arrays = []

    # These are the arrays that will be the mutation sources
    parent_handle_arrays = [candidate_handle_arrays[i] for i in best_score_indices]

    # these are the combinations that had the worst scores in the previous generation
    parent_hallofshame_handles = [hallofshame_handles[i]for i in best_score_indices]
    parent_hallofshame_antihandles = [hallofshame_antihandles[i] for i in best_score_indices]

    # number of arrays to generate
    generation_array_count = len(candidate_handle_arrays)
    parent_array_count = len(parent_handle_arrays)

    # mask to prevent the assigning of a handle in areas where none should be placed (zeros)
    mask = candidate_handle_arrays[0] > 0

    # all parents are members of the next generation and survive
    mutated_handle_arrays.extend(parent_handle_arrays)

    # prepares masks for each new candidate to allow mutations to occur in select areas
    for i in range(parent_array_count, generation_array_count):

        # pick someone to mutate
        pick = np.random.randint(0, parent_array_count)
        mother = parent_handle_arrays[pick].copy()
        random_choice = np.random.choice(['mutate handles', 'mutate antihandles', 'mutate anywhere'],
                                         p=[0.425, 0.425, 0.15]) # TODO: do we want these to be customizable?

        if random_choice == 'mutate handles':

            mother_hallofshame_handles = parent_hallofshame_handles[pick]

            # locates the target slats for mutation, and prepares a mask
            mask2 = np.full(candidate_handle_arrays[0].shape, False, dtype=bool)
            for layer, slatname in mother_hallofshame_handles:  # indexing has a -1 since the handles always face up (and are 1-indexed)
                mask2[:, :, layer - 1] = (slat_array[:, :, layer - 1] == slatname) | mask2[:, :, layer - 1]

        elif random_choice == 'mutate antihandles':  # or some bad antihandle sequences
            mother_hallofshame_antihandles = parent_hallofshame_antihandles[pick]

            # locates the target slats for mutation, and prepares a mask
            mask2 = np.full(candidate_handle_arrays[0].shape, False, dtype=bool)

            for layer, slatname in mother_hallofshame_antihandles: # indexing has a -2 since the antihandles always face down (and are 1-indexed)
                mask2[:, :, layer - 2] = ((slat_array[:, :, layer - 2] == slatname)) | mask2[:, :, layer - 2]

        elif random_choice == 'mutate anywhere':
            mask2 = np.full(candidate_handle_arrays[0].shape, True, dtype=bool)

        next_gen_member = mother.copy()
        # This fills an array with true values at random locations with the probability of mutationrate at each location
        # Mask and mask2 two are the places where mutations are allowed
        logicforpointmutations = np.random.random(candidate_handle_arrays[0].shape) < mutation_rate
        logicforpointmutations = logicforpointmutations & mask & mask2

        # The actual mutation happens here
        if not split_sequence_handles: # just use the entire library for any one handle
            next_gen_member[logicforpointmutations] = np.random.randint(1, unique_sequences + 1,
                                                                        size=np.sum(logicforpointmutations))
        else: # in the split case, only half the library is available for any one layer
            for layer in range(logicforpointmutations.shape[2]):
                if layer % 2 == 0:
                    h1 = 1
                    h2 = int(unique_sequences / 2) + 1
                else:
                    h1 = int(unique_sequences / 2) + 1
                    h2 = unique_sequences + 1

                next_gen_member[:, :, layer][logicforpointmutations[:, :, layer]] = np.random.randint(h1, h2,size=np.sum(logicforpointmutations[:, :, layer]))
        mutated_handle_arrays.append(next_gen_member)

    return mutated_handle_arrays


def evolve_handles_from_slat_array(slat_array,
                                   early_hamming_stop=None,
                                   evolution_generations=20,
                                   evolution_population=30,
                                   process_count=None,
                                   generational_survivors=3,
                                   mutation_rate=0.0025,
                                   slat_length=32,
                                   unique_handle_sequences=32,
                                   split_sequence_handles=False,
                                   log_tracking_directory=None,
                                   progress_bar_update_time=None,
                                   random_seed=8):
    """
    Generates an optimal handle array from a slat array using an evolutionary algorithm
    and a physics-informed partition score.
    WARNING: Make sure to use the "if __name__ == '__main__':" block to run this function in a script.
    Otherwise, the spawned processes will cause a recursion error.
    :param slat_array: The basis slat array for which a handle set needs to be found
    :param early_hamming_stop: If this hamming distance is achieved, the evolution will stop early
    :param evolution_generations: Number of generations to consider before stopping
    :param evolution_population: Number of handle arrays to mutate in each generation
    :param process_count: Number of threads to use for hamming multiprocessing (if set to default, will use 67% of available cores)
    :param generational_survivors: Number of surviving candidate arrays that persist through each generation
    :param mutation_rate: Probability of an individual eligible handle being mutated after selection
    :param slat_length: Slat length in terms of number of handles
    :param unique_handle_sequences: Handle library length
    :param split_sequence_handles: Set to true to enforce the splitting of handle sequences between subsequent layers
    :param log_tracking_directory: Set to a directory to export plots and metrics during the optimization process (optional)
    :param progress_bar_update_time: Time interval for updating the progress bar (optional)
    :param random_seed: Random seed to use to ensure consistency
    :return: The final optimized handle array for the supplied slat array.
    """

    np.random.seed(random_seed)
    if progress_bar_update_time:
        mininterval = progress_bar_update_time
        maxinterval = progress_bar_update_time
    else:
        mininterval = 0.1
        maxinterval = 10

    # initiate population of handle arrays
    candidate_handle_arrays = []
    if not split_sequence_handles:
        for j in range(evolution_population):
            candidate_handle_arrays.append(generate_random_slat_handles(slat_array, unique_handle_sequences))
    else:
        for j in range(evolution_population):
            candidate_handle_arrays.append(generate_layer_split_handles(slat_array, unique_handle_sequences))

    physical_scores = np.zeros(evolution_population)  # initialize the score variable which will be used as the phenotype for the selection.
    hammings = np.zeros(evolution_population)
    duplicate_risk_scores = np.zeros(evolution_population)
    hallofshame_handle_values = []
    hallofshame_antihandle_values = []


    if log_tracking_directory:
        fig_name = os.path.join(log_tracking_directory, 'hamming_evolution_tracking.pdf')
        metric_tracker = defaultdict(list)
        excel_conditional_formatting = {'type': '3_color_scale',
                                        'criteria': '<>',
                                        'min_color': "#63BE7B",  # Green
                                        'mid_color': "#FFEB84",  # Yellow
                                        'max_color': "#F8696B",  # Red
                                        'value': 0}

    if process_count:
        num_processes = process_count
    else:
        # if no exact count specified, use 67 percent of the cores available on the computer as a reasonable load
        num_processes = max(1, int(multiprocessing.cpu_count() / 1.5))

    print(Fore.BLUE + f'Will be using {num_processes} core(s) for the handle array evolution.' + Fore.RESET)

    # This is the main game/evolution loop where generations are created, evaluated, and mutated
    with tqdm(total=evolution_generations, desc='Evolution Progress', mininterval=mininterval, maxinterval=maxinterval) as pbar:
        for generation in range(evolution_generations):
            #### first step: analyze handle array population individual by individual and gather reports of the scores
            # and the bad handles of each

            # multiprocessing will be used to speed up overall computation and parallelize the hamming distance calculations
            # refer to the multirule_oneshot_hamming function for details on input arguments
            multiprocess_start = time.time()
            with multiprocessing.Pool(processes=num_processes) as pool:
                results = pool.starmap(multirule_oneshot_hamming, [(slat_array, candidate_handle_arrays[j], True, True, None, True, slat_length) for j in range(evolution_population)])

            multiprocess_time = time.time() - multiprocess_start

            # Unpack and store results from multiprocessing
            for index, res in enumerate(results):
                physical_scores[index] = res['Physics-Informed Partition Score']
                hammings[index] = res['Universal']
                duplicate_risk_scores[index] = res['Substitute Risk']
                hallofshame_handle_values.append(res['Worst combinations handle IDs'])
                hallofshame_antihandle_values.append(res['Worst combinations antihandle IDs'])

            # TODO: these operations here can probably be optimized
            # compare and find the individual with the best hamming distance i.e. the largest one. Note: there might be several
            max_hamming_value_of_population = np.max(hammings)
            # Get the indices of the top 'survivors' largest elements
            indices_of_largest_scores = np.argpartition(physical_scores, -generational_survivors)[-generational_survivors:]
            # Sort the indices based on the scores to get the largest scores in descending order
            sorted_indices_of_largest_scores = indices_of_largest_scores[np.argsort(-physical_scores[indices_of_largest_scores])]

            # Get the largest elements using the sorted indices
            best_physical_scores = physical_scores[sorted_indices_of_largest_scores]

            if log_tracking_directory:
                metric_tracker['Best Hamming'].append(max_hamming_value_of_population)
                # All other metrics should match the specific handle array that has the best hamming distance
                metric_tracker['Corresponding Physics-Based Score'].append(-physical_scores[np.argmax(hammings)])
                metric_tracker['Corresponding Duplicate Risk Score'].append(duplicate_risk_scores[np.argmax(hammings)])
                metric_tracker['Hamming Compute Time'].append(multiprocess_time)

                fig, ax = plt.subplots(4, 1, figsize=(10, 10))

                # TODO: optimize here
                for ind, (name, data) in enumerate(zip(['Candidate with Best Hamming Distance',
                                                        'Corresponding Physics-Based Partition Score',
                                                        'Corresponding Duplication Risk Score', 'Hamming Compute Time (s)'],
                                                       [metric_tracker['Best Hamming'],
                                                        metric_tracker['Corresponding Physics-Based Score'],
                                                        metric_tracker['Corresponding Duplicate Risk Score'],
                                                        metric_tracker['Hamming Compute Time']])):
                    ax[ind].plot(data, linestyle='--', marker='o')
                    ax[ind].set_xlabel('Iteration')
                    ax[ind].set_ylabel('Measurement')
                    ax[ind].set_title(name)
                    ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

                ax[1].set_yscale('log')
                plt.tight_layout()
                plt.savefig(fig_name)
                plt.close(fig)

                # saves the metrics to a csv file for downstream analysis/plotting
                save_list_dict_to_file(log_tracking_directory, 'metrics.csv', metric_tracker)

                # saves the best handle array to an excel file for downstream analysis
                if generation % 10 == 0 or generation == evolution_generations-1 or max_hamming_value_of_population >= early_hamming_stop:  # TODO: add logic to adjust this output interval and implement file cleanup if necessary
                    intermediate_best_array = candidate_handle_arrays[np.argmax(hammings)]
                    writer = pd.ExcelWriter(
                        os.path.join(log_tracking_directory, f'best_handle_array_generation_{generation}.xlsx'),
                        engine='xlsxwriter')

                    # prints out slat dataframes in standard format
                    for layer_index in range(intermediate_best_array.shape[-1]):
                        df = pd.DataFrame(intermediate_best_array[..., layer_index])
                        df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
                        # Apply conditional formatting for easy color-based identification
                        writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],df.shape[1] - 1, excel_conditional_formatting)
                    writer.close()


                pbar.update(1)
                pbar.set_postfix({f'Current best hamming score': max_hamming_value_of_population,
                                  'Time for hamming calculation': multiprocess_time,
                                  'Best physics partition scores': best_physical_scores})

            if early_hamming_stop and max_hamming_value_of_population >= early_hamming_stop:
                break

            #### second step: mutate best handle arrays from previous generation, and create a new population for the next generation
            candidate_handle_arrays = mutate_handle_arrays(slat_array, candidate_handle_arrays,
                                                           hallofshame_handle_values,
                                                           hallofshame_antihandle_values,
                                                           best_score_indices=indices_of_largest_scores,
                                                           unique_sequences=unique_handle_sequences,
                                                           mutation_rate=mutation_rate,
                                                           split_sequence_handles=split_sequence_handles)


    return candidate_handle_arrays[np.argmax(hammings)] # returns the best array in terms of hamming distance (which might not necessarily match the physics-based score)


if __name__ == '__main__':
    # JUST A TESTING AREA
    slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(slat_array, 32)

    print ('Original Results:')
    print(multirule_oneshot_hamming(slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False, request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))

    ergebnüsse = evolve_handles_from_slat_array(slat_array, unique_handle_sequences=32,
                                                early_hamming_stop=28, evolution_population=300,
                                                generational_survivors=5,
                                                mutation_rate=0.03,
                                                process_count=1,
                                                evolution_generations=200,
                                                split_sequence_handles=False,
                                                log_tracking_directory='/Users/matt/Desktop')

    print ('New Results:')
    print(multirule_oneshot_hamming(slat_array, ergebnüsse, per_layer_check=True, report_worst_slat_combinations=False, request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, ergebnüsse, per_layer_check=True, request_substitute_risk_score=True))
