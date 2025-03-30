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
import importlib

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, multirule_precise_hamming
from crisscross.assembly_handle_optimization.handle_mutation import mutate_handle_arrays
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization import generate_random_slat_handles, generate_layer_split_handles
from crisscross.helper_functions import save_list_dict_to_file, create_dir_if_empty

optuna_spec = importlib.util.find_spec("optuna")  # only imports optuna if this is available
if optuna_spec is not None:
    import optuna

    optuna_available = True
else:
    optuna_available = False


def evolve_handles_from_slat_array(slat_array,
                                   early_hamming_stop=None,
                                   evolution_generations=20,
                                   evolution_population=30,
                                   process_count=None,
                                   generational_survivors=3,
                                   mutation_rate=0.0025,
                                   slat_length=32,
                                   unique_handle_sequences=32,
                                   mutation_type_probabilities=(0.425, 0.425, 0.15),
                                   split_sequence_handles=False,
                                   log_tracking_directory=None,
                                   progress_bar_update_iterations=None,
                                   seed_handle_array=None,
                                   random_seed=8,
                                   optuna_optimization_trial=None):
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
    :param mutation_type_probabilities: Probability of selecting a specific mutation type for a target handle/antihandle
    (either handle, antihandle or mixed mutations)
    :param split_sequence_handles: Set to true to enforce the splitting of handle sequences between subsequent layers
    :param log_tracking_directory: Set to a directory to export plots and metrics during the optimization process (optional)
    :param progress_bar_update_iterations: Number of iterations before progress bar is updated
    - useful for server output files, but does not seem to work consistently on every system (optional)
    :param random_seed: Random seed to use to ensure consistency
    :param seed_handle_array: Can initiate the evolution from a specific initial handle array generated from a previous run here.
    :param optuna_optimization_trial: If running an optuna optimization, this is the trial object to report the score to
    :return: The final optimized handle array for the supplied slat array.
    """

    np.random.seed(random_seed)

    # initiate population of handle arrays
    candidate_handle_arrays = []
    if not split_sequence_handles:
        for j in range(evolution_population):
            candidate_handle_arrays.append(generate_random_slat_handles(slat_array, unique_handle_sequences))
    else:
        for j in range(evolution_population):
            candidate_handle_arrays.append(generate_layer_split_handles(slat_array, unique_handle_sequences))

    if seed_handle_array is not None:
        candidate_handle_arrays[0] = seed_handle_array

    initial_candidates = candidate_handle_arrays.copy()

    physical_scores = np.zeros(evolution_population)  # initialize the score variable which will be used as the phenotype for the selection.
    hammings = np.zeros(evolution_population)
    duplicate_risk_scores = np.zeros(evolution_population)

    if log_tracking_directory:
        create_dir_if_empty(log_tracking_directory)
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
    with tqdm(total=evolution_generations, desc='Evolution Progress', miniters=progress_bar_update_iterations) as pbar:
        for generation in range(1, evolution_generations + 1):

            hallofshame_handle_values = []
            hallofshame_antihandle_values = []
            #### first step: analyze handle array population individual by individual and gather reports of the scores
            # and the bad handles of each
            # multiprocessing will be used to speed up overall computation and parallelize the hamming distance calculations
            # refer to the multirule_oneshot_hamming function for details on input arguments
            multiprocess_start = time.time()
            with multiprocessing.Pool(processes=num_processes) as pool:
                results = pool.starmap(multirule_oneshot_hamming,
                                       [(slat_array, candidate_handle_arrays[j], True, True, None, True, slat_length)
                                        for j in range(evolution_population)])
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
            max_physics_score_of_population = -np.max(physical_scores)
            # Get the indices of the top 'survivors' largest elements
            indices_of_largest_scores = np.argpartition(physical_scores, -generational_survivors)[-generational_survivors:]
            # Sort the indices based on the scores to get the largest scores in descending order
            sorted_indices_of_largest_scores = indices_of_largest_scores[np.argsort(-physical_scores[indices_of_largest_scores])]

            # Get the largest elements using the sorted indices
            best_physical_scores = physical_scores[sorted_indices_of_largest_scores]

            if log_tracking_directory:
                metric_tracker['Best Physics-Based Score'].append(max_physics_score_of_population)
                # All other metrics should match the specific handle array that has the best hamming distance
                metric_tracker['Corresponding Hamming Distance'].append(hammings[np.argmax(physical_scores)])
                metric_tracker['Corresponding Duplicate Risk Score'].append(duplicate_risk_scores[np.argmax(physical_scores)])
                metric_tracker['Hamming Compute Time'].append(multiprocess_time)
                metric_tracker['Generation'].append(generation)

                similarity_scores = []
                for candidate in candidate_handle_arrays:
                    for initial_candidate in initial_candidates:
                        similarity_scores.append(np.sum(candidate == initial_candidate))
                metric_tracker['Similarity Score'].append(sum(similarity_scores)/len(similarity_scores))

                # saves the metrics to a csv file for downstream analysis/plotting (will append data if the file already exists)
                save_list_dict_to_file(log_tracking_directory, 'metrics.csv', metric_tracker,
                                       selected_data=generation - 1 if generation > 1 else None)

                # saves the best handle array to an excel file for downstream analysis
                if generation % 10 == 0 or generation == evolution_generations or max(metric_tracker['Corresponding Hamming Distance']) >= early_hamming_stop:  # TODO: add logic to adjust this output interval and implement file cleanup if necessary

                    fig, ax = plt.subplots(5, 1, figsize=(10, 10))

                    for ind, (name, data) in enumerate(zip(['Candidate with Best Physics-Based Partition Score',
                                                            'Corresponding Hamming Distance',
                                                            'Corresponding Duplication Risk Score',
                                                            'Similarity of Population to Initial Candidates',
                                                            'Hamming Compute Time (s)'],
                                                           [metric_tracker['Best Physics-Based Score'],
                                                            metric_tracker['Corresponding Hamming Distance'],
                                                            metric_tracker['Corresponding Duplicate Risk Score'],
                                                            metric_tracker['Similarity Score'],
                                                            metric_tracker['Hamming Compute Time']])):
                        ax[ind].plot(data, linestyle='--', marker='o')
                        ax[ind].set_xlabel('Iteration')
                        ax[ind].set_ylabel('Measurement')
                        ax[ind].set_title(name)
                        ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

                    ax[0].set_yscale('log')
                    plt.tight_layout()
                    plt.savefig(fig_name)
                    plt.close(fig)

                    intermediate_best_array = candidate_handle_arrays[np.argmin(physical_scores)]
                    writer = pd.ExcelWriter(
                        os.path.join(log_tracking_directory, f'best_handle_array_generation_{generation}.xlsx'),
                        engine='xlsxwriter')

                    # prints out slat dataframes in standard format
                    for layer_index in range(intermediate_best_array.shape[-1]):
                        df = pd.DataFrame(intermediate_best_array[..., layer_index])
                        df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
                        # Apply conditional formatting for easy color-based identification
                        writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],
                                                                                                df.shape[1] - 1,
                                                                                                excel_conditional_formatting)
                    writer.close()

                if optuna_optimization_trial:
                    if not optuna_available:
                        raise ImportError('Optuna is not available on this system.')
                    optuna_optimization_trial.report(physical_scores[np.argmax(hammings)], generation)

                    # Optuna can 'prune' i.e. stop a trial early if it thinks the trajectory is already very slow
                    if optuna_optimization_trial.should_prune():
                        with open(os.path.join(log_tracking_directory, 'trial_pruned.txt'), 'w') as f:
                            f.write(f'Trial was pruned at generation {generation}')
                        raise optuna.TrialPruned()

                pbar.update(1)
                pbar.set_postfix({f'Current best hamming score': max(hammings),
                                  'Time for hamming calculation': multiprocess_time,
                                  'Best physics partition scores': best_physical_scores}, refresh=False)

            if early_hamming_stop and  max(metric_tracker['Corresponding Hamming Distance']) >= early_hamming_stop:
                break

            #### second step: mutate best handle arrays from previous generation, and create a new population for the next generation
            candidate_handle_arrays, mutation_maps = mutate_handle_arrays(slat_array, candidate_handle_arrays,
                                                                          hallofshame_handle_values,
                                                                          hallofshame_antihandle_values,
                                                                          best_score_indices=indices_of_largest_scores,
                                                                          unique_sequences=unique_handle_sequences,
                                                                          mutation_rate=mutation_rate,
                                                                          mutation_type_probabilities=mutation_type_probabilities,
                                                                          split_sequence_handles=split_sequence_handles)

            # for map_index, map in enumerate(mutation_maps):
            #     fig, ax = plt.subplots(1, 1)
            #     ax.imshow(map[:, :, 0])
            #     plt.savefig(os.path.join(log_tracking_directory, f'mutation_map_{generation}_{map_index}.png'))
            #     plt.close(fig)
            z=5

    return candidate_handle_arrays[np.argmax(hammings)]  # returns the best array in terms of hamming distance (which might not necessarily match the physics-based score)


if __name__ == '__main__':
    # JUST A TESTING AREA
    slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(slat_array, 32)

    print('Original Results:')
    print(
        multirule_oneshot_hamming(slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
                                  request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))

    ergebnüsse = evolve_handles_from_slat_array(slat_array, unique_handle_sequences=32,
                                                early_hamming_stop=30, evolution_population=943,
                                                generational_survivors=2,
                                                mutation_rate=0.01427,
                                                process_count=10,
                                                evolution_generations=100,
                                                split_sequence_handles=False,
                                                progress_bar_update_iterations=2,
                                                log_tracking_directory='/Users/matt/Desktop')

    print('New Results:')
    print(multirule_oneshot_hamming(slat_array, ergebnüsse, per_layer_check=True, report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, ergebnüsse, per_layer_check=True, request_substitute_risk_score=True))
