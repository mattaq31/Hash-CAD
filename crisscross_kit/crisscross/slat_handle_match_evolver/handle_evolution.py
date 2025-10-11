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
import re
import toml

from crisscross.slat_handle_match_evolver.handle_mutation import mutate_handle_arrays
from crisscross.slat_handle_match_evolver import generate_random_slat_handles, generate_layer_split_handles
from crisscross.helper_functions import save_list_dict_to_file, create_dir_if_empty
from eqcorr2d.eqcorr2d_interface import comprehensive_score_analysis


class EvolveManager:
    def __init__(self, megastructure, random_seed=8, generational_survivors=3,
                 mutation_rate=5, mutation_type_probabilities=(0.425, 0.425, 0.15), unique_handle_sequences=32,
                 evolution_generations=200, evolution_population=30, split_sequence_handles=False, sequence_split_factor=2,
                 process_count=None, early_max_valency_stop=None, log_tracking_directory=None, progress_bar_update_iterations=2,
                 mutation_memory_system='off', memory_length=10, repeating_unit_constraints=None):
        """
        Prepares an evolution manager to optimize a handle array for the provided slat array.
        WARNING: Make sure to use the "if __name__ == '__main__':" block to run this class in a script.
        Otherwise, the spawned processes will cause a recursion error.
        :param megastructure: Megastructure object containing slat array and optionally a seed handle array for starting evolution
        :param random_seed: Random seed to use to ensure consistency
        :param generational_survivors: Number of surviving candidate arrays that persist through each generation
        :param mutation_rate: The expected number of mutations per iteration
        :param mutation_type_probabilities: Probability of selecting a specific mutation type for a target handle/antihandle
        (either handle, antihandle or mixed mutations)
        :param unique_handle_sequences: Handle library length
        :param evolution_generations: Number of generations to consider before stopping
        :param evolution_population: Number of handle arrays to mutate in each generation
        :param split_sequence_handles: Set to true to enforce the splitting of handle sequences between subsequent layers
        :param sequence_split_factor: Factor by which to split the handle sequences between layers (default is 2, which means that if handles are split, the first layer will have 1/2 of the handles, etc.)
        :param process_count: Number of threads to use for hamming multiprocessing (if set to default, will use 67% of available cores)
        :param early_max_valency_stop: If this worst match score  is achieved, the evolution will stop early
        :param log_tracking_directory: Set to a directory to export plots and metrics during the optimization process (optional)
        :param progress_bar_update_iterations: Number of iterations before progress bar is updated
        - useful for server output files, but does not seem to work consistently on every system (optional)
        :param mutation_memory_system: The type of memory system to use for the handle mutation process. Options are 'all', 'best', 'special', or 'off'.
        :param memory_length: Memory of previous 'worst' handle combinations to retain when selecting positions to mutate.
        :param repeating_unit_constraints: Two dictionaries containing 'link_handles' and 'transplant_handles' that define constraints on handle mutations (mainly for use with repeating unit designs).
        """

        # initial parameter setup
        np.random.seed(int(random_seed))
        self.seed = int(random_seed)
        self.metrics = defaultdict(list)
        self.mismatch_histograms = []

        # creates Megastructure objects to help compute arrays required for compensating match calculation histograms
        self.dummy_megastructure = megastructure
        self.slat_array = megastructure.generate_slat_occupancy_grid()
        self.repeating_unit_constraints = {} if repeating_unit_constraints is None else repeating_unit_constraints

        seed_handle_array = megastructure.generate_assembly_handle_grid()

        if np.sum(seed_handle_array) == 0:
            self.handle_array = None
        else:
            self.handle_array = seed_handle_array # this variable holds the current best handle array in the system (updated throughout evolution)

        self.generational_survivors = int(generational_survivors)
        self.mutation_rate = mutation_rate
        self.max_evolution_generations = int(evolution_generations)
        self.number_unique_handles = int(unique_handle_sequences)
        self.evolution_population = int(evolution_population)
        self.current_generation = 0

        self.log_tracking_directory = log_tracking_directory
        if self.log_tracking_directory is not None:
            create_dir_if_empty(self.log_tracking_directory)

        self.progress_bar_update_iterations = int(progress_bar_update_iterations)
        self.mutation_memory_system = mutation_memory_system
        self.hall_of_shame_memory = memory_length

        # converters for alternative parameter definitions
        if early_max_valency_stop is None:
            self.early_max_valency_stop = None
        else:
            self.early_max_valency_stop = int(early_max_valency_stop)

        if isinstance(mutation_type_probabilities, str):
            self.mutation_type_probabilities = tuple(map(float, mutation_type_probabilities.split(', ')))
        else:
            self.mutation_type_probabilities = mutation_type_probabilities

        if isinstance(split_sequence_handles, str):
            self.split_sequence_handles = eval(split_sequence_handles.capitalize())
        else:
            self.split_sequence_handles = split_sequence_handles
        self.sequence_split_factor = sequence_split_factor

        if isinstance(process_count, float) or isinstance(process_count, int):
            self.num_processes = int(process_count)
        else:
            # if no exact count specified, use 67 percent of the cores available on the computer as a reasonable load
            self.num_processes = max(1, int(multiprocessing.cpu_count() / 1.5))

        print(Fore.BLUE + f'Handle array evolution core count set to {self.num_processes}.' + Fore.RESET)

        self.next_candidates = self.initialize_evolution()
        self.initial_candidates = self.next_candidates.copy()
        if self.handle_array is None:
            self.dummy_megastructure.assign_assembly_handles(self.next_candidates[0])

        self.slat_compensation_match_counts, self.slat_connection_graph = self.dummy_megastructure.get_slat_match_counts(use_original_slat_array=True)

        self.memory_hallofshame = defaultdict(list)
        self.memory_best_parent_hallofshame = defaultdict(list)
        self.initial_hallofshame = defaultdict(list)

        self.excel_conditional_formatting = {'type': '3_color_scale',
                                             'criteria': '<>',
                                             'min_color': "#63BE7B",  # Green
                                             'mid_color': "#FFEB84",  # Yellow
                                             'max_color': "#F8696B",  # Red
                                             'value': 0}


    def initialize_evolution(self):
        """
        Initializes the pool of candidate handle arrays.
        """
        candidate_handle_arrays = []
        if not self.split_sequence_handles or self.slat_array.shape[2] < 3:
            for j in range(self.evolution_population):
                candidate_handle_arrays.append(generate_random_slat_handles(self.slat_array, self.number_unique_handles, **self.repeating_unit_constraints))
        else:
            for j in range(self.evolution_population):
                candidate_handle_arrays.append(generate_layer_split_handles(self.slat_array,  self.number_unique_handles, self.sequence_split_factor, **self.repeating_unit_constraints))

        if self.handle_array is not None:
            candidate_handle_arrays[0] = self.handle_array

        return candidate_handle_arrays

    def single_evolution_step(self):
        """
        Performs a single evolution step, evaluating all candidate arrays and preparing new mutations for the next generation.
        :return:
        """
        self.current_generation += 1
        mean_parasitic_valency = np.zeros(self.evolution_population)  # initialize the score variable which will be used as the phenotype for the selection.
        max_parasitic_valency = np.zeros(self.evolution_population)
        duplicate_risk_scores = np.zeros(self.evolution_population)

        hallofshame = defaultdict(list)

        #### first step: analyze handle array population individual by individual and gather reports of the scores
        # and the bad handles of each
        # multiprocessing will be used to speed up overall computation and parallelize the hamming distance calculations
        # refer to the multirule_oneshot_hamming function for details on input arguments
        multiprocess_start = time.time()

        with multiprocessing.Pool(processes=self.num_processes) as pool:
            analysis_inputs = []
            for j in range(self.evolution_population):
                handles, antihandles = self.dummy_megastructure.get_bag_of_slat_handles(use_original_slat_array=True,
                                                                                        use_external_handle_array = self.next_candidates[j],
                                                                                        remove_blank_slats=True)

                analysis_inputs.append((handles, antihandles, self.slat_compensation_match_counts, self.slat_connection_graph, self.dummy_megastructure.connection_angle, True))
            results = pool.starmap(comprehensive_score_analysis, analysis_inputs)

        multiprocess_time = time.time() - multiprocess_start

        # Unpack and store results from multiprocessing
        for index, res in enumerate(results):
            mean_parasitic_valency[index] = res['mean_log_score']
            max_parasitic_valency[index] = res['worst_match_score']
            duplicate_risk_scores[index] = res['similarity_score']
            worst_handle_combos = [tuple(map(int, re.findall(r'\d+', r[0]))) for r in res['worst_slat_combos']]
            worst_antihandle_combos = [tuple(map(int, re.findall(r'\d+', r[1]))) for r in res['worst_slat_combos']]
            hallofshame['handles'].append(worst_handle_combos)
            hallofshame['antihandles'].append(worst_antihandle_combos)
            if self.current_generation == 1:
                self.initial_hallofshame['handles'].append(worst_handle_combos)
                self.initial_hallofshame['antihandles'].append(worst_antihandle_combos)

        # compare and find the individual with the best hamming distance i.e. the largest one. Note: there might be several
        max_physics_score_of_population = np.min(mean_parasitic_valency)
        # Get the indices of the top 'survivors' largest elements
        indices_of_largest_scores = np.argpartition(mean_parasitic_valency, self.generational_survivors)[:self.generational_survivors]

        # Get the largest elements using the sorted indices
        self.metrics['Best Effective Parasitic Valency'].append(max_physics_score_of_population)
        self.metrics['Corresponding Max Parasitic Valency'].append(max_parasitic_valency[np.argmin(mean_parasitic_valency)])
        # All other metrics should match the specific handle array that has the best physics score
        self.metrics['Corresponding Duplicate Risk Score'].append(duplicate_risk_scores[np.argmin(mean_parasitic_valency)])
        self.metrics['Compute Time'].append(multiprocess_time)
        self.metrics['Generation'].append(self.current_generation)

        similarity_scores = []
        for candidate in self.next_candidates:
            for initial_candidate in self.initial_candidates:
                similarity_scores.append(np.sum(candidate == initial_candidate))

        self.metrics['Similarity Score'].append(sum(similarity_scores) / len(similarity_scores))

        # Select and store the current best handle array
        best_idx = int(np.argmin(mean_parasitic_valency))
        self.handle_array = self.next_candidates[best_idx]

        # Extracts precomputed match histogram from multirule_oneshot_hamming for the best candidate
        self.mismatch_histograms.append(results[best_idx]['match_histogram'])

        candidate_handle_arrays, _ = mutate_handle_arrays(self.slat_array, self.next_candidates,
                                                         hallofshame=hallofshame,
                                                          memory_hallofshame=self.memory_hallofshame,
                                                          memory_best_parent_hallofshame=self.memory_best_parent_hallofshame,
                                                          best_score_indices=indices_of_largest_scores,
                                                          unique_sequences=self.number_unique_handles,
                                                          mutation_rate=self.mutation_rate,
                                                          use_memory_type=self.mutation_memory_system,
                                                          special_hallofshame=self.initial_hallofshame,
                                                          mutation_type_probabilities=self.mutation_type_probabilities,
                                                          split_sequence_handles=self.split_sequence_handles,
                                                          sequence_split_factor=self.sequence_split_factor,
                                                          repeating_unit_constraints=self.repeating_unit_constraints)

        for key, payload in hallofshame.items():
            self.memory_hallofshame[key].extend(payload)
            self.memory_best_parent_hallofshame[key].extend([payload[i] for i in indices_of_largest_scores])

        if len(self.memory_hallofshame['handles']) > self.hall_of_shame_memory * self.evolution_population:
            for key in self.memory_hallofshame.keys():
                self.memory_hallofshame[key] = self.memory_hallofshame[key][-self.hall_of_shame_memory * self.evolution_population:]
                self.memory_best_parent_hallofshame[key] = self.memory_best_parent_hallofshame[key][-self.hall_of_shame_memory * self.generational_survivors:]

        self.next_candidates = candidate_handle_arrays


    def export_results(self, main_folder_path=None, generate_unique_folder_name=True, parameter_export=False):

        if main_folder_path:
            if generate_unique_folder_name:
                output_folder = os.path.join(main_folder_path, f"evolution_results_{time.strftime('%Y%m%d_%H%M%S')}")
            else:
                output_folder = os.path.join(main_folder_path, 'evolution_results')
        else:
            output_folder = self.log_tracking_directory

        create_dir_if_empty(output_folder)

        fig, ax = plt.subplots(5, 1, figsize=(10, 10))

        for ind, (name, data) in enumerate(zip(['Candidate with Best Effective Parasitic Valency',
                                                'Corresponding Max Parasitic Valency',
                                                'Corresponding Duplication Risk Score',
                                                'Similarity of Population to Initial Candidates',
                                                'Compute Time (s)'],
                                               [self.metrics['Best Effective Parasitic Valency'],
                                                self.metrics['Corresponding Max Parasitic Valency'],
                                                self.metrics['Corresponding Duplicate Risk Score'],
                                                self.metrics['Similarity Score'],
                                                self.metrics['Compute Time']])):

            if len(data) > 5000:
                # turn off markers if too many data points
                ax[ind].plot(range(1, len(data)+1), data, linestyle='--')
            else:
                ax[ind].plot(range(1, len(data)+1), data, linestyle='--', marker='o')

            ax[ind].set_xlabel('Generation')
            ax[ind].set_ylabel('Measurement')
            ax[ind].set_title(name)
            ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'metrics_visualization.pdf'))
        plt.close(fig)

        # save the mismatch histograms to csv file
        df = pd.DataFrame(self.mismatch_histograms)
        # rewrite df headers  by appending ' Matches' to each column name
        df.columns = [f'{col} Matches' for col in df.columns]
        df.to_csv(os.path.join(output_folder, 'match_histograms.csv'), index=False, header=True)

        # produces a graph tracking each individual mismatch score throughout time
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        for col in df.columns:
            if len(df[col].dropna()) > 5000:
                ax.plot(range(1, len(df[col].dropna()) + 1), df[col].dropna(), linestyle='--', label=col)
            else:
                ax.plot(range(1, len(df[col].dropna()) + 1), df[col].dropna(), linestyle='--', marker='o', label=col)

        ax.set_xlabel('Generation')
        ax.set_ylabel('Number of combinations')
        ax.set_title('Handle Match Tracking')
        ax.set_yscale('log')
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))
        ax.xaxis.set_minor_locator(ticker.LogLocator(base=10.0, subs='auto', numticks=10))
        ax.xaxis.set_major_formatter(ticker.LogFormatter())

        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'mismatch_tracking_visualization.pdf'), bbox_inches='tight')
        plt.close(fig)

        # save all other generic metrics to csv file
        save_list_dict_to_file(output_folder, 'metrics.csv', self.metrics, append=False, index_column='Generation')

        # prepare a checkpoint of the current best handle array
        writer = pd.ExcelWriter(
            os.path.join(output_folder, f'best_handle_array_generation_{self.current_generation}.xlsx'),
            engine='xlsxwriter')

        # prints out handle dataframes in standard format
        for layer_index in range(self.handle_array.shape[-1]):
            df = pd.DataFrame(self.handle_array[..., layer_index])
            df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
            # Apply conditional formatting for easy color-based identification
            writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],
                                                                                    df.shape[1] - 1,
                                                                                    self.excel_conditional_formatting)
        writer.close()

        if parameter_export:
            full_parameter_set = {
                'random_seed': self.seed,
                'generational_survivors': self.generational_survivors,
                'mutation_rate': self.mutation_rate,
                'mutation_type_probabilities': self.mutation_type_probabilities,
                'unique_handle_sequences': self.number_unique_handles,
                'evolution_generations': self.max_evolution_generations,
                'evolution_population': self.evolution_population,
                'split_sequence_handles': self.split_sequence_handles,
                'sequence_split_factor': self.sequence_split_factor,
                'process_count': self.num_processes,
                'early_max_valency_stop': self.early_max_valency_stop,
                'progress_bar_update_iterations': self.progress_bar_update_iterations,
                'mutation_memory_system': self.mutation_memory_system,
                'memory_length': self.hall_of_shame_memory,
            }

            toml.dump(full_parameter_set, open(os.path.join(output_folder, 'evolution_config.toml'), 'w'))

    def run_full_experiment(self, logging_interval=10):
        """
        Runs a full evolution experiment.
        :param logging_interval: The frequency at which logs should be written to file (including the best hamming array file).
        """
        if self.log_tracking_directory is None:
            raise ValueError('Log tracking directory must be specified to run an automatic full experiment.')
        with tqdm(total=self.max_evolution_generations - self.current_generation, desc='Evolution Progress', miniters=self.progress_bar_update_iterations) as pbar:
            for index, generation in enumerate(range(self.current_generation, self.max_evolution_generations)):
                self.single_evolution_step()
                if (index+1) % logging_interval == 0:
                    self.export_results()

                pbar.update(1)
                pbar.set_postfix({f'Latest max parasitic valency': self.metrics['Corresponding Max Parasitic Valency'][-1],
                                  'Time for calculations': self.metrics['Compute Time'][-1],
                                  'Latest effective parasitic valency': self.metrics['Best Effective Parasitic Valency'][-1]}, refresh=False)

                if self.early_max_valency_stop and min(self.metrics['Corresponding Max Parasitic Valency']) <= self.early_max_valency_stop:
                    print('Early stopping criteria met, ending evolution process.')
                    break

