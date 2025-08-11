import os
import numpy as np
from itertools import product
from collections import defaultdict, OrderedDict

from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import extract_handle_dicts,oneshot_hamming_compute

########## CONFIG

def custom_analysis_oneshot_hamming(slat_array, handle_array,
                                    report_worst_slat_combinations=True,
                                    per_layer_check=False,
                                    specific_slat_groups=None,
                                    request_substitute_risk_score=False,
                                    slat_length=32,
                                    partial_area_score=False, adjustment_type=None, adjustment_values_dict={}):

    slat_array = np.array(slat_array, dtype=np.uint16)  # converts to int to reduce memory usage
    handle_array = np.array(handle_array, dtype=np.uint16)

    # extract all slats and compute full hamming distance here
    handle_dict, antihandle_dict = extract_handle_dicts(handle_array, slat_array)

    hamming_results = oneshot_hamming_compute(handle_dict, antihandle_dict, slat_length)

    # calculate hamming distance in the case that we are only considering a partial area, which requires editing slat handles in non-considered regions to be "0"
    if partial_area_score:
        hamming_results_partial = {}
        for group_key, slat_dict in partial_area_score.items():
            handle_dict_partial = OrderedDict()
            antihandle_dict_partial = OrderedDict()

            for (slat_layer, slat_ID), full_slat_handles in handle_dict.items():
                try:
                    slat_inclusion = slat_dict["handles"][(slat_layer, slat_ID)]
                    partial_slat_handles = np.array([x if y else 0 for x, y in zip(full_slat_handles, slat_inclusion)],
                                                    dtype=np.uint16)
                    handle_dict_partial[(slat_layer, slat_ID)] = partial_slat_handles
                except KeyError:  # Not included - leave in all slats but filter out at the end using indices
                    handle_dict_partial[(slat_layer, slat_ID)] = full_slat_handles

            for (slat_layer, slat_ID), full_slat_antihandles in antihandle_dict.items():
                try:
                    slat_inclusion = slat_dict["antihandles"][(slat_layer, slat_ID)]
                    partial_slat_antihandles = np.array(
                        [x if y else 0 for x, y in zip(full_slat_antihandles, slat_inclusion)], dtype=np.uint16)
                    antihandle_dict_partial[(slat_layer, slat_ID)] = partial_slat_antihandles
                except KeyError:  # Not included - leave in all slats but filter out at the end using indices
                    antihandle_dict_partial[(slat_layer, slat_ID)] = full_slat_antihandles

            hamming_results_partial[group_key] = oneshot_hamming_compute(handle_dict_partial, antihandle_dict_partial,
                                                                         slat_length)

    score_dict = {}
    handle_ordered_list = list(handle_dict.keys())
    antihandle_ordered_list = list(antihandle_dict.keys())

    if adjustment_type == 'multiple':
        for i in range(hamming_results.shape[0]):
            for j in range(hamming_results.shape[1]):
                hamming_results[i, j, :] = hamming_results[i, j, :] - (32-hamming_results[i, j, :]) * (adjustment_values_dict['multiplier']-1)
    elif adjustment_type == 'sprinkle':
        allotment = adjustment_values_dict['sprinkle_allotment']
        shape = hamming_results.shape
        for _ in range(allotment):
            random_index = tuple(np.random.randint(dim) for dim in shape)
            hamming_results[random_index] -= 1

    elif adjustment_type == 'addition':
        for i in range(hamming_results.shape[0]):
            for j in range(hamming_results.shape[1]):
                hamming_results[i, j, :] = hamming_results[i, j, :] - adjustment_values_dict['add_value']

    # The universal hamming score representing the worst case scenario
    score_dict['Universal'] = np.min(hamming_results)

    # physics-based score motivated by the definition of the partition function in the dirks 2007 paper (original nupack paper)
    score_dict['Physics-Informed Partition Score'] = -np.average(np.exp(-10 * (hamming_results - slat_length)))
    score_dict['Total Mismatches'] = -np.sum(hamming_results - slat_length)

    # If requested, the hamming distance for each layer and each specific slat group is calculated (these will always be better than or identical to the universal score)
    if per_layer_check or specific_slat_groups:
        layer_hammings = defaultdict(list)
        group_hammings = defaultdict(list)
        for (handle_layer, handle_id), (antihandle_layer, antihandle_id) in product(handle_ordered_list,
                                                                                    antihandle_ordered_list):
            handle_matrix_index = handle_ordered_list.index((handle_layer, handle_id))
            antihandle_matrix_index = antihandle_ordered_list.index((antihandle_layer, antihandle_id))

            if per_layer_check and handle_layer == antihandle_layer - 1:
                layer_hammings[handle_layer].append(
                    min(hamming_results[handle_matrix_index, antihandle_matrix_index, :]))
            if specific_slat_groups:
                for group_key, group in specific_slat_groups.items():
                    if (handle_layer, handle_id) in group and (antihandle_layer, antihandle_id) in group:
                        group_hammings[group_key].append(
                            min(hamming_results[handle_matrix_index, antihandle_matrix_index, :]))

        if per_layer_check:
            for layer, all_hammings in layer_hammings.items():
                score_dict[f'Layer {layer}'] = np.min(all_hammings)
        if specific_slat_groups:
            for group_key, all_hammings in group_hammings.items():
                score_dict[group_key] = np.min(all_hammings)

    # generates lists of the worst handle/antihandle combinations - these will be used for mutations in the evolutionary algorithm
    if report_worst_slat_combinations:
        min_hamming_indices = np.where((hamming_results == score_dict['Universal']))
        hallofshamehandles = [handle_ordered_list[i] for i in min_hamming_indices[0]]
        hallofshameantihandles = [antihandle_ordered_list[i] for i in min_hamming_indices[1]]
        score_dict['Worst combinations handle IDs'] = hallofshamehandles
        score_dict['Worst combinations antihandle IDs'] = hallofshameantihandles

    # this computes the risk that two slats are identical i.e. the risk that one slat could replace another in the wrong place if it has enough complementary handles
    # for now, no special index validation is provided for this feature.
    if request_substitute_risk_score:
        duplicate_results = []
        for combo_dict in [handle_dict, antihandle_dict]:
            duplicate_results.append(oneshot_hamming_compute(combo_dict, combo_dict, slat_length))
        global_min = np.inf
        for sim_list in duplicate_results:
            num_handles = sim_list.shape[0]
            global_min = np.min([np.min(sim_list[np.eye(num_handles) == 0, :]),
                                 global_min])  # ignores diagonal i.e. slat self-comparisons
        score_dict['Substitute Risk'] = np.int64(global_min)

    # if a specific region was requested, filter for just the slats that were considered rather than all slats
    if partial_area_score:
        handle_ordered_list_partial = list(handle_dict_partial.keys())
        antihandle_ordered_list_partial = list(antihandle_dict_partial.keys())
        for group_key, slat_dict in partial_area_score.items():
            handle_matrix_indices = np.array(
                [handle_ordered_list_partial.index((x, y)) for x, y in slat_dict["handles"].keys()], dtype=np.uint16)
            antihandle_matrix_indices = np.array(
                [antihandle_ordered_list_partial.index((x, y)) for x, y in slat_dict["antihandles"].keys()],
                dtype=np.uint16)
            score_dict[group_key] = np.min([hamming_results_partial[group_key][hID, ahID, :] for hID, ahID in
                                            product(handle_matrix_indices, antihandle_matrix_indices)])

    return score_dict

version = 1

H_mega = Megastructure(import_design_file='/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/exp_2_sunflowers/v1/v1_design.xlsx')

query_base = custom_analysis_oneshot_hamming(H_mega.generate_slat_occupancy_grid(), H_mega.generate_assembly_handle_grid(), request_substitute_risk_score=True)

physics_results = {'Base': np.log(-query_base['Physics-Informed Partition Score'])}
hamming_results = {'Base': query_base['Universal']}
mismatch_results = {'Base': query_base['Total Mismatches']}
for multiplier in [2, 3, 4, 5]:
    query_scores = custom_analysis_oneshot_hamming(H_mega.generate_slat_occupancy_grid(), H_mega.generate_assembly_handle_grid(),
                                                      request_substitute_risk_score=True, adjustment_type='multiple', adjustment_values_dict={'multiplier':multiplier})
    physics_results[f'multiplier_{multiplier}'] = np.log(-query_scores['Physics-Informed Partition Score'])
    hamming_results[f'multiplier_{multiplier}'] = query_scores['Universal']
    mismatch_results[f'multiplier_{multiplier}'] = query_scores['Total Mismatches']

for adder in [1, 2, 3, 4]:
    query_scores = custom_analysis_oneshot_hamming(H_mega.generate_slat_occupancy_grid(), H_mega.generate_assembly_handle_grid(),
                                                      request_substitute_risk_score=True, adjustment_type='addition', adjustment_values_dict={'add_value':adder})
    physics_results[f'addition_{adder}'] = np.log(-query_scores['Physics-Informed Partition Score'])
    hamming_results[f'addition_{adder}'] = query_scores['Universal']
    mismatch_results[f'addition_{adder}'] = query_scores['Total Mismatches']

for sprinkle in [1000, 10000, 100000, 1000000]:
    query_scores = custom_analysis_oneshot_hamming(H_mega.generate_slat_occupancy_grid(), H_mega.generate_assembly_handle_grid(),
                                                      request_substitute_risk_score=True, adjustment_type='sprinkle', adjustment_values_dict={'sprinkle_allotment':sprinkle})
    physics_results[f'sprinkle_{sprinkle}'] = np.log(-query_scores['Physics-Informed Partition Score'])
    hamming_results[f'sprinkle_{sprinkle}'] = query_scores['Universal']
    mismatch_results[f'sprinkle_{sprinkle}'] = query_scores['Total Mismatches']
