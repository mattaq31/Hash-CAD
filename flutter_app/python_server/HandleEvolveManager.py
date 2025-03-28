from collections import defaultdict

import numpy as np
import time
import os
import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from crisscross.assembly_handle_optimization import generate_random_slat_handles, generate_layer_split_handles
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.assembly_handle_optimization.handle_evolution import mutate_handle_arrays
from crisscross.helper_functions import save_list_dict_to_file

from server_architecture import hamming_evolve_communication_pb2_grpc, hamming_evolve_communication_pb2

def proto_to_numpy(proto_layers):
    """Convert gRPC response into a 3D NumPy array"""
    array_3d = []
    for layer3d in proto_layers:  # Iterate over Layer3D
        array_2d = []
        for layer2d in layer3d.layers:
            for layer1d in layer2d.rows: # Iterate over Layer2D
                array_2d.append(layer1d.values)  # Extract 1D array
        array_3d.append(array_2d)

    return np.array(array_3d, dtype=np.int32)  # Convert to NumPy array

def convert_string_to_float_if_numeric(value):
    try:
        return float(value) if value.replace(".", "", 1).isdigit() else value
    except ValueError:
        return value


class EvolveManager:
    def __init__(self, initial_slat_array, initial_handle_array=None, slat_length=32, seed=8, generational_survivors=3,
                 mutation_rate=0.0025,  mutation_type_probabilities=(0.425, 0.425, 0.15), number_unique_handles=32,
                 evolution_generations=200, evolution_population=30, split_sequence_handles=False, process_count=None):
        np.random.seed(int(seed))
        self.seed = int(seed)
        self.slat_array = initial_slat_array
        self.handle_array = initial_handle_array
        self.slat_length = slat_length
        self.metrics = defaultdict(list)

        self.generational_survivors = int(generational_survivors)
        self.mutation_rate = mutation_rate

        # convert a string with 3 floats into a tuple of floats
        if isinstance(mutation_type_probabilities, str):
            self.mutation_type_probabilities = tuple(map(float, mutation_type_probabilities.split(', ')))
        else:
            self.mutation_type_probabilities = mutation_type_probabilities

        self.max_evolution_generations = int(evolution_generations)
        self.current_generation = 0
        self.number_unique_handles = int(number_unique_handles)
        self.evolution_population = int(evolution_population)

        self.num_processes = process_count
        if isinstance(split_sequence_handles, str):
            self.split_sequence_handles = eval(split_sequence_handles.capitalize())
        else:
            self.split_sequence_handles = split_sequence_handles

        if isinstance(process_count, float):
            self.num_processes = process_count
        else:
            # if no exact count specified, use 67 percent of the cores available on the computer as a reasonable load
            self.num_processes = max(1, int(multiprocessing.cpu_count() / 1.5))

        self.next_candidates = self.initialize_evolution()
        self.initial_candidates = self.next_candidates.copy()

        self.excel_conditional_formatting = {'type': '3_color_scale',
                                             'criteria': '<>',
                                             'min_color': "#63BE7B",  # Green
                                             'mid_color': "#FFEB84",  # Yellow
                                             'max_color': "#F8696B",  # Red
                                             'value': 0}

    def initialize_evolution(self):

        # initiate population of handle arrays
        candidate_handle_arrays = []
        if not self.split_sequence_handles:
            for j in range(self.evolution_population):
                candidate_handle_arrays.append(generate_random_slat_handles(self.slat_array, self.number_unique_handles))
        else:
            for j in range(self.evolution_population):
                candidate_handle_arrays.append(generate_layer_split_handles(self.slat_array,  self.number_unique_handles))

        if self.handle_array is not None:
            candidate_handle_arrays[0] = self.handle_array

        return candidate_handle_arrays

    def broadcast_metrics_update(self):
        return hamming_evolve_communication_pb2.ProgressUpdate(hamming=self.metrics['Corresponding Hamming'][-1], physics=self.metrics['Best Physics-Based Score'][-1])

    def single_evolution_step(self):
        physical_scores = np.zeros(self.evolution_population)  # initialize the score variable which will be used as the phenotype for the selection.
        hammings = np.zeros(self.evolution_population)
        duplicate_risk_scores = np.zeros(self.evolution_population)

        hallofshame_handle_values = []
        hallofshame_antihandle_values = []
        #### first step: analyze handle array population individual by individual and gather reports of the scores
        # and the bad handles of each
        # multiprocessing will be used to speed up overall computation and parallelize the hamming distance calculations
        # refer to the multirule_oneshot_hamming function for details on input arguments
        print('Starting Inner Evolution')
        multiprocess_start = time.time()
        with multiprocessing.Pool(processes=self.num_processes) as pool:
            results = pool.starmap(multirule_oneshot_hamming,
                                   [(self.slat_array, self.next_candidates[j], True, True, None, True, self.slat_length)
                                    for j in range(self.evolution_population)])
        multiprocess_time = time.time() - multiprocess_start

        # Unpack and store results from multiprocessing
        for index, res in enumerate(results):
            physical_scores[index] = res['Physics-Informed Partition Score']
            hammings[index] = res['Universal']
            duplicate_risk_scores[index] = res['Substitute Risk']
            hallofshame_handle_values.append(res['Worst combinations handle IDs'])
            hallofshame_antihandle_values.append(res['Worst combinations antihandle IDs'])

        # compare and find the individual with the best hamming distance i.e. the largest one. Note: there might be several
        max_physics_score_of_population = -np.max(physical_scores)
        # Get the indices of the top 'survivors' largest elements
        indices_of_largest_scores = np.argpartition(physical_scores, -self.generational_survivors)[-self.generational_survivors:]

        # Get the largest elements using the sorted indices
        self.metrics['Best Physics-Based Score'].append(max_physics_score_of_population)
        self.metrics['Corresponding Hamming Distance'].append(hammings[np.argmax(physical_scores)])
        # All other metrics should match the specific handle array that has the best physics score
        self.metrics['Corresponding Duplicate Risk Score'].append(duplicate_risk_scores[np.argmax(physical_scores)])
        self.metrics['Hamming Compute Time'].append(multiprocess_time)

        similarity_scores = []
        for candidate in self.next_candidates:
            for initial_candidate in self.initial_candidates:
                similarity_scores.append(np.sum(candidate == initial_candidate))

        self.metrics['Similarity Score'].append(sum(similarity_scores) / len(similarity_scores))

        self.handle_array = self.next_candidates[np.argmax(physical_scores)] # stores intermediate best array
        print('Generating Metrics')

        candidate_handle_arrays, mutation_maps = mutate_handle_arrays(self.slat_array, self.next_candidates,
                                                                     hallofshame_handle_values,
                                                                     hallofshame_antihandle_values,
                                                                     best_score_indices=indices_of_largest_scores,
                                                                     unique_sequences=self.number_unique_handles,
                                                                     mutation_rate=self.mutation_rate,
                                                                     mutation_type_probabilities=self.mutation_type_probabilities,
                                                                     split_sequence_handles=self.split_sequence_handles)
        self.next_candidates = candidate_handle_arrays
        self.current_generation += 1

    def export_results(self, main_folder_path):
        # create a new folder with the current date
        output_folder = os.path.join(main_folder_path, f"evolution_results_{time.strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_folder, exist_ok=True)

        fig, ax = plt.subplots(5, 1, figsize=(10, 10))

        for ind, (name, data) in enumerate(zip(['Candidate with Best Physics-Based Partition Score',
                                                'Corresponding Hamming Distance',
                                                'Corresponding Duplication Risk Score',
                                                'Similarity of Population to Initial Candidates',
                                                'Hamming Compute Time (s)'],
                                               [self.metrics['Best Physics-Based Score'],
                                                self.metrics['Corresponding Hamming Distance'],
                                                self.metrics['Corresponding Duplicate Risk Score'],
                                                self.metrics['Similarity Score'],
                                                self.metrics['Hamming Compute Time']])):

            ax[ind].plot(data, linestyle='--', marker='o')
            ax[ind].set_xlabel('Iteration')
            ax[ind].set_ylabel('Measurement')
            ax[ind].set_title(name)
            ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        ax[0].set_yscale('log')
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'metrics_visualization.pdf'))
        plt.close(fig)

        # saves the metrics to a csv file for downstream analysis/plotting
        save_list_dict_to_file(output_folder, 'metrics.csv', self.metrics, selected_data=None)

        writer = pd.ExcelWriter(
            os.path.join(output_folder, f'best_handle_array_generation_{self.current_generation}.xlsx'),
            engine='xlsxwriter')

        # prints out slat dataframes in standard format
        for layer_index in range(self.handle_array.shape[-1]):
            df = pd.DataFrame(self.handle_array[..., layer_index])
            df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
            # Apply conditional formatting for easy color-based identification
            writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],
                                                                                    df.shape[1] - 1,
                                                                                    self.excel_conditional_formatting)
        writer.close()


class HandleEvolveService(hamming_evolve_communication_pb2_grpc.HandleEvolveServicer):
    def __init__(self):
        self.pause_signal = False
        self.evolve_manager = None

    def evolveQuery(self, request, context):
        print('INITIATING HAMMING EVOLUTION')
        self.pause_signal = False
        if self.evolve_manager is None:
            slat_array = proto_to_numpy(request.slatArray)
            converted_dict = {key: convert_string_to_float_if_numeric(value) for key, value in dict(request.parameters).items()}
            self.evolve_manager = EvolveManager(slat_array, **converted_dict)

        for generation in range(self.evolve_manager.current_generation, self.evolve_manager.max_evolution_generations):
            if self.pause_signal:
                break
            self.evolve_manager.single_evolution_step()
            print(
                f"Yielding generation {generation} - Hamming: {self.evolve_manager.metrics['Corresponding Hamming Distance'][-1]}")

            yield hamming_evolve_communication_pb2.ProgressUpdate(hamming=self.evolve_manager.metrics['Corresponding Hamming Distance'][-1],
                                                                  physics=np.log10(self.evolve_manager.metrics['Best Physics-Based Score'][-1]))

        print('HAMMING EVOLUTION COMPLETE')

    def PauseProcessing(self, request, context):
        self.pause_signal = True
        print('PAUSE TOGGLED')

    def StopProcessing(self, request, context):
        self.pause_signal = True
        print('RECEIVED STOP REQUEST')
        # Convert NumPy array to protobuf format
        handleArray = [
            hamming_evolve_communication_pb2.Layer3D(layers=[
                hamming_evolve_communication_pb2.Layer2D(rows=[
                    hamming_evolve_communication_pb2.Layer1D(values=row.tolist()) for row in layer
                ])
            ]) for layer in self.evolve_manager.handle_array
        ]
        self.evolve_manager = None

        return hamming_evolve_communication_pb2.FinalResponse(handleArray=handleArray)

    def requestExport(self, request, context):
        print('RECEIVED EXPORT REQUEST')
        self.evolve_manager.export_results(request.folderPath)
        return hamming_evolve_communication_pb2.ExportResponse()
