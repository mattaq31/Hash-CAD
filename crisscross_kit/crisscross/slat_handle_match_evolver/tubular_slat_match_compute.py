import numpy as np
from itertools import product
from collections import defaultdict, OrderedDict
import eqcorr2d

def extract_handle_dicts(handle_array, slat_array, list_indices_only=False, custom_index_map=None):
    """
    Extracts all slats from a design and organizes them into dictionaries of handles and antihandles.
    If list_indices_only is set to True, the function will return lists of indices instead of the actual handle values.
    :param handle_array: Array of XxYxZ-1 dimensions containing the IDs of all the handles in the design
    :param slat_array: Array of XxYxZ dimensions containing the positions of all slats in the design
    :param list_indices_only: Set to True to return lists of indices instead of the actual handle values
    :param custom_index_map: A dictionary mapping (layer, slat_id) tuples to specific indices in the handle_array.
    :return: Two dictionaries or lists containing the handle sequences (or indices) for each slat
     - one for handles and one for antihandles
    """

    # identifies all slats in design
    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    if list_indices_only:
        handle_index_list = []
        antihandle_index_list = []
    else:
        handle_dict = OrderedDict()
        antihandle_dict = OrderedDict()

    # extracts handle values for all slats in the design -
    # note that a slat value is only unique within a layer,
    # and so each slat must be identified by both its layer and ID.

    # TODO: if handle/antihandle assumption changed, need to update here too
    for layer_position, layer_slats in enumerate(unique_slats_per_layer):
        # an assumption is made here that the bottom-most slat will always start with handles,
        # then alternate to anti-handles and so on.  Thus, the bottom layer will only have handles
        # and the top layer will only have antihandles.  Everything in between will have both.
        handles_available = True
        antihandles_available = True
        if layer_position == 0:
            handles_available = True
            antihandles_available = False
        if layer_position == len(unique_slats_per_layer) - 1:
            handles_available = False
            antihandles_available = True

        # iterate over all slat names in the selected layer, and pulls their handle values into a single list for each slat
        for slat in layer_slats:
            slat_key = (layer_position + 1, slat)
            if handles_available:
                if list_indices_only:
                    handle_index_list.append((layer_position, slat, layer_position))
                else:
                    if custom_index_map and slat_key in custom_index_map:
                        handle_dict[slat_key] = handle_array[custom_index_map[slat_key]]
                    else:
                        handle_dict[slat_key] = handle_array[slat_array[..., layer_position] == slat, layer_position]

            if antihandles_available:
                if list_indices_only:
                    antihandle_index_list.append((layer_position, slat, layer_position - 1))
                else:
                    if custom_index_map and slat_key in custom_index_map:
                        indices = custom_index_map[slat_key]
                        antihandle_dict[slat_key] = handle_array[indices]
                    else:
                        antihandle_dict[slat_key] = handle_array[slat_array[..., layer_position] == slat, layer_position - 1]

    if list_indices_only:
        return handle_index_list, antihandle_index_list
    else:
        return handle_dict, antihandle_dict


def oneshot_hamming_compute(handle_dict, antihandle_dict, slat_length):
    """
    Given a dictionary of slat handles and antihandles, this function computes the hamming distance between all possible combinations.
    This is the fastest implementation available, making full use of Numpy's efficient vector computation.
    :param handle_dict: Dictionary of handles i.e. {slat_id: slat_handle_array}
    :param antihandle_dict: Dictionary of antihandles i.e. {slat_id: slat_antihandle_array}
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """

    handles = np.array(list(handle_dict.values()))
    num_handles = handles.shape[0]
    flippedhandles = handles[:, ::-1]

    # Generate every possible shift and reversed shift of the handle sequences -
    # the goal is to simulate every possible physical interaction between two slats
    # The total length will be 4 * the slat length - 2 (two states are repeated)
    # The operations are repeated for all handles in the input array
    shifted_handles = np.zeros((handles.shape[0], (4 * slat_length)-2, slat_length), dtype=np.uint16)

    for i in range(slat_length):
        # Normal shifts
        shifted_handles[:, i, i:] = handles[:, :slat_length - i]
        if i != 0: # skip the first one as it repeats the normal slat
            shifted_handles[:, slat_length + i - 1, :slat_length - i] = handles[:, i:] # index has a -1 due to the skipped first combination
        # Reversed shifts
        shifted_handles[:, 2 * slat_length + i - 1, i:] = flippedhandles[:, :slat_length - i]
        if i != 0:  # skip the first one as it repeats the normal reversed slat
            shifted_handles[:, 3 * slat_length + i - 2, :slat_length - i] = flippedhandles[:, i:] # index has a -2 due to the two skipped combinations at this point

    # The antihandles should simply be tiled to generate the same number of sequences as the handles, shifts are not needed
    antihandles = np.array(list(antihandle_dict.values()))
    num_antihandles = antihandles.shape[0]
    tiled_antihandles = np.tile(antihandles[:, np.newaxis, :], (1, (4 * slat_length) - 2, 1))

    # tiles all the handle and antihandles into a large 4D array containing:
        # all combinations of handles with antihandles (dimensions 1 and 2)
        # all possible shifts of the handles (dimension 3)
    # This final tiling ensures that each and every handle-slat is matched with each and every antihandle-slat
    combinatorial_matrix_handles = np.tile(shifted_handles[:, np.newaxis, :, :], (1, num_antihandles, 1, 1))
    combinatorial_matrix_antihandles = np.tile(tiled_antihandles[np.newaxis, :, :, :], (num_handles, 1, 1, 1))

    # After all the matches are built up, the hamming distance can be computed for all combinations in one go
    all_matches = (combinatorial_matrix_handles == combinatorial_matrix_antihandles) & (combinatorial_matrix_handles != 0)
    hamming_results = slat_length - np.count_nonzero(all_matches, axis=3) # hamming distance maximum is always the length of the slats

    return hamming_results


def multirule_oneshot_hamming(slat_array, handle_array,
                              report_worst_slat_combinations=True,
                              per_layer_check=False,
                              specific_slat_groups=None,
                              request_substitute_risk_score=False,
                              slat_length=32,
                              partial_area_score=False,
                              return_match_histogram=False):
    """
    Given a slat and handle array, this function computes the hamming distance of all handle/antihandle combinations provided.
    Scores for individual components, such as specific slat groups, can also be requested.
    Note: This function is our current fastest implementation. Due to its optimization, it cannot be instructed to
    compute lesser combinations of slats in the design - it will compute all hamming results at once.

    Implementation comment:  Requesting the similarity score requires that more hamming combinations are computed.
    This will of course slow down the function by a factor of 3 (approx).  We tried to reduce this speed loss by
    combining the handles and antihandles into a duplicate array, which computes the following combinations:
    - handle vs handle
    - antihandle vs antihandle
    - handle vs antihandle (duplicated twice)
    However, the end result was a minor slowdown rather than speed increase.  We suspect that the additional computations
    forced by the duplicated handle vs antihandle combination outweights the speed increase by computing the arrays all in one go.
    It might be possible to improve this further, but we do not think the solution is obvious (or potentially worth the time investment).

    :param slat_array: Array of XxYxZ dimensions, where X and Y are the dimensions of the design and Z is the number of layers in the design
    :param handle_array: Array of XxYxZ-1 dimensions containing the IDs of all the handles in the design
    :param report_worst_slat_combinations: Set to true to provide the IDs of the worst handle/antihandle slat combinations
    :param per_layer_check: Set to true to provide a hamming score for the individual layers of the design (i.e. the interface between each layer)
    :param specific_slat_groups: Provide a dictionary, where the key is a group name and the value is a list of tuples containing the layer and slat ID of the slats in the group for which the specific hamming distance is being requested.
    :param slat_length: The length of a single slat (must be an integer)
    :param request_substitute_risk_score: Set to true to provide a measure of the largest amount of handle duplication between slats of the same type (handle or antihandle)
    :param partial_area_score: Calculates Hamming distance and substitution risk among a subset of provided slats when only considering a subset of the handles.
    Provide a dictionary with key as a group name and the values as dictionarys with keys "handle" and "antihandle".
    The corresponding values are dictionaries, where the key is a tuple like so (slat layer, slat ID) and the value is a list of TRUE/FALSE depending on whether that position's handle is included.
    :param return_match_histogram: If True, returns a histogram of the number of matches of each type (0 matches, 1 match, etc.).
    :return: Dictionary of scores (or slat layer/handle IDS for the worst slat combinations)
     for each of the slat combinations requested from the design
    """

    slat_array = np.array(slat_array, dtype=np.uint16) # converts to int to reduce memory usage
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
                    partial_slat_handles = np.array([x if y else 0 for x,y in zip(full_slat_handles, slat_inclusion)], dtype=np.uint16)
                    handle_dict_partial[(slat_layer, slat_ID)] = partial_slat_handles
                except KeyError: # Not included - leave in all slats but filter out at the end using indices
                    handle_dict_partial[(slat_layer, slat_ID)] = full_slat_handles

            for (slat_layer, slat_ID), full_slat_antihandles in antihandle_dict.items():
                try:
                    slat_inclusion = slat_dict["antihandles"][(slat_layer, slat_ID)]
                    partial_slat_antihandles = np.array([x if y else 0 for x,y in zip(full_slat_antihandles, slat_inclusion)], dtype=np.uint16)
                    antihandle_dict_partial[(slat_layer, slat_ID)] = partial_slat_antihandles
                except KeyError: # Not included - leave in all slats but filter out at the end using indices
                    antihandle_dict_partial[(slat_layer, slat_ID)] = full_slat_antihandles

            hamming_results_partial[group_key] = oneshot_hamming_compute(handle_dict_partial, antihandle_dict_partial, slat_length)

    score_dict = {}
    handle_ordered_list = list(handle_dict.keys())
    antihandle_ordered_list = list(antihandle_dict.keys())

    # The universal hamming score representing the worst case scenario
    score_dict['Universal'] = np.min(hamming_results)

    # physics-based score motivated by the definition of the partition function in the dirks 2007 paper (original nupack paper)
    score_dict['Physics-Informed Partition Score'] = -np.average(np.exp(-10 * (hamming_results - slat_length)))

    # If requested, the hamming distance for each layer and each specific slat group is calculated (these will always be better than or identical to the universal score)
    if per_layer_check or specific_slat_groups:
        layer_hammings = defaultdict(list)
        group_hammings = defaultdict(list)
        for (handle_layer, handle_id), (antihandle_layer, antihandle_id) in product(handle_ordered_list, antihandle_ordered_list):
            handle_matrix_index = handle_ordered_list.index((handle_layer, handle_id))
            antihandle_matrix_index = antihandle_ordered_list.index((antihandle_layer, antihandle_id))

            if per_layer_check and handle_layer == antihandle_layer - 1:
                layer_hammings[handle_layer].append(min(hamming_results[handle_matrix_index, antihandle_matrix_index, :]))
            if specific_slat_groups:
                for group_key, group in specific_slat_groups.items():
                    if (handle_layer, handle_id) in group and (antihandle_layer, antihandle_id) in group:
                        group_hammings[group_key].append(min(hamming_results[handle_matrix_index, antihandle_matrix_index, :]))

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
            global_min = np.min([np.min(sim_list[np.eye(num_handles)==0,:]), global_min])  # ignores diagonal i.e. slat self-comparisons
        score_dict['Substitute Risk'] = np.int64(global_min)

    # if a specific region was requested, filter for just the slats that were considered rather than all slats
    if partial_area_score:
        handle_ordered_list_partial = list(handle_dict_partial.keys())
        antihandle_ordered_list_partial = list(antihandle_dict_partial.keys())
        for group_key, slat_dict in partial_area_score.items():
            handle_matrix_indices = np.array([handle_ordered_list_partial.index((x,y)) for x,y in slat_dict["handles"].keys()], dtype=np.uint16)
            antihandle_matrix_indices = np.array([antihandle_ordered_list_partial.index((x,y)) for x,y in slat_dict["antihandles"].keys()], dtype=np.uint16)
            score_dict[group_key] = np.min([hamming_results_partial[group_key][hID, ahID, :] for hID, ahID in product(handle_matrix_indices, antihandle_matrix_indices)])

    # Precomputes match histogram (based on oneshot results computed above)
    if return_match_histogram:
        matches = -(hamming_results - slat_length)
        flat_matches = matches.flatten()
        match_type, counts = np.unique(flat_matches, return_counts=True)
        # Return as numpy arrays; callers can convert to Python lists if needed
        score_dict['match_histogram'] = (match_type, counts)

    return score_dict


def precise_hamming_compute(handle_dict, antihandle_dict, valid_product_indices, slat_length):
    """
    Given a dictionary of slat handles and antihandles, this function computes the hamming distance between all possible combinations.
    It can be restricted to certain combinations by providing a list of valid product indices.
    This is not the fastest hamming implementation available, but does use numpy vectorization to reduce runtime.
    :param handle_dict: Dictionary of handles i.e. {slat_id: slat_handle_array}
    :param antihandle_dict: Dictionary of antihandles i.e. {slat_id: slat_antihandle_array}
    :param valid_product_indices: A list of indices matching the possible
    products that should be computed (i.e. if a product is not being requested, the index should be False)
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """
    single_combo = 4 * slat_length
    total_combos = single_combo * sum(valid_product_indices)
    combination_matrix_1 = np.zeros((total_combos, slat_length), dtype=np.uint16)
    combination_matrix_2 = np.zeros((total_combos, slat_length), dtype=np.uint16)
    valid_combo_index = 0
    for i, ((hk, handle_slat), (ahk, antihandle_slat)) in enumerate(product(handle_dict.items(), antihandle_dict.items())):
        if valid_product_indices[i]:
            for j in range(slat_length):
                # 4 combinations:
                # 1. X vs Y, rotation to the left
                # 2. X vs Y, rotation to the right
                # 3. X vs Y, rotation to the left, reversed X
                # 4. X vs Y, rotation to the right, reversed X
                # All rotations padded with zeros (already in array)

                combination_matrix_1[(valid_combo_index * single_combo) + j, :slat_length - j] = handle_slat[j:]
                combination_matrix_1[(valid_combo_index * single_combo) + slat_length + j, j:] = handle_slat[:slat_length - j]
                combination_matrix_1[(valid_combo_index * single_combo) + (2 * slat_length) + j, :slat_length - j] = handle_slat[::-1][j:]
                combination_matrix_1[(valid_combo_index * single_combo) + (3 * slat_length) + j, j:] = handle_slat[::-1][:slat_length - j]
            combination_matrix_2[valid_combo_index * single_combo:(valid_combo_index + 1) * single_combo, :] = antihandle_slat
            valid_combo_index += 1
    results = np.count_nonzero(np.logical_or(combination_matrix_1 != combination_matrix_2, combination_matrix_1 == 0, combination_matrix_2 == 0), axis=1)
    return results


def multirule_precise_hamming(slat_array, handle_array, universal_check=True, per_layer_check=False,
                              specific_slat_groups=None, slat_length=32, request_substitute_risk_score=False,
                              partial_area_score=False):
    """
    Given a slat and handle array, this function computes the hamming distance of all handle/antihandle combinations provided.
    Scores for individual components, such as specific slat groups, can also be requested.
    This does not use the fastest hamming calculation implementation,
    but can be configured to restrict the number of combinations computed.
    :param slat_array: Array of XxYxZ dimensions, where X and Y are the dimensions of the design and Z is the number of layers in the design
    :param handle_array: Array of XxYxZ-1 dimensions containing the IDs of all the handles in the design
    :param universal_check: Set to true to provide a hamming score for the entire set of slats in the design
    :param per_layer_check: Set to true to provide a hamming score for the individual layers of the design (i.e. the interface between each layer)
    :param specific_slat_groups: Provide a dictionary, where the key is a group name and the value is a list of tuples containing the layer and slat ID of the slats in the group for which the specific hamming distance is being requested.
    :param slat_length: The length of a single slat (must be an integer)
    :param request_substitute_risk_score: Set to true to provide a measure of the largest amount of handle duplication between slats of the same type (handle or antihandle)
    :param partial_area_score: Calculates Hamming distance and substitution risk among a subset of provided slats when only considering a subset of the handles.
    Provide a dictionary with key as a group name and the values as dictionaries with keys "handle" and "antihandle".
    The corresponding values are dictionaries, where the key is a tuple like so (slat layer, slat ID) and the value is a list of TRUE/FALSE depending on whether that position's handle is included.
    :return: Dictionary of scores for each of the aspects requested from the design
    """

    slat_array = np.array(slat_array, dtype=np.uint16) # converts to int to reduce memory usage
    handle_array = np.array(handle_array, dtype=np.uint16)

    # extracts handle values for all slats in the design
    bag_of_slat_handles, bag_of_slat_antihandles = extract_handle_dicts(handle_array, slat_array)

    # in the case that smaller subsets of the entire range of handle/antihandle products are required, this code snippet will remove those products that can be ignored to speed up computation
    valid_product_indices = []
    final_combination_index = 0
    layer_indices = defaultdict(list)
    group_indices = defaultdict(list)
    for i, ((hkey, handle_slat), (antihkey, antihandle_slat)) in enumerate(product(bag_of_slat_handles.items(), bag_of_slat_antihandles.items())):
        valid_product = False
        if universal_check:
            valid_product = True
        if per_layer_check and hkey[0] == antihkey[0] - 1:
            valid_product = True
            layer_indices[hkey[0]].extend(
                range(final_combination_index * (4 * slat_length), (final_combination_index + 1) * (4 * slat_length)))
        if specific_slat_groups: 
            for group_key, group in specific_slat_groups.items(): 
                if hkey in group and antihkey in group:
                    group_indices[group_key].extend(range(final_combination_index * (4 * slat_length),
                                                          (final_combination_index + 1) * (4 * slat_length)))
                    valid_product = True
        if valid_product:
            final_combination_index += 1
        valid_product_indices.append(valid_product)

    # the actual hamming computation is all done here
    hamming_results = precise_hamming_compute(bag_of_slat_handles, bag_of_slat_antihandles, valid_product_indices, slat_length)
    score_dict = {}

    # calculate hamming distance in the case that we are only considering a partial area, which requires editing slat handles in non-considered regions to be "0"
    if partial_area_score:
        hamming_results_partial = {}
        for group_key, slat_dict in partial_area_score.items():
            bag_of_slat_handles_partial = OrderedDict()
            bag_of_slat_antihandles_partial = OrderedDict()
            
            for (slat_layer, slat_ID), full_slat_handles in bag_of_slat_handles.items():
                if (slat_layer, slat_ID) in slat_dict['handles']:
                    slat_inclusion = slat_dict["handles"][(slat_layer, slat_ID)]
                    partial_slat_handles = np.array([x if y else 0 for x,y in zip(full_slat_handles, slat_inclusion)], dtype=np.uint16)
                    bag_of_slat_handles_partial[(slat_layer, slat_ID)] = partial_slat_handles

            for (slat_layer, slat_ID), full_slat_antihandles in bag_of_slat_antihandles.items():
                if (slat_layer, slat_ID) in slat_dict['antihandles']:
                    slat_inclusion = slat_dict["antihandles"][(slat_layer, slat_ID)]
                    partial_slat_antihandles = np.array([x if y else 0 for x,y in zip(full_slat_antihandles, slat_inclusion)], dtype=np.uint16)
                    bag_of_slat_antihandles_partial[(slat_layer, slat_ID)] = partial_slat_antihandles

                # Filters out the selection here - everything listed is included
            valid_product_indices_partial = [True for _ in product(bag_of_slat_handles_partial, bag_of_slat_antihandles_partial)] 
            hamming_results_partial[group_key] = precise_hamming_compute(bag_of_slat_handles_partial, bag_of_slat_antihandles_partial, valid_product_indices_partial, slat_length)
    
    # this computes the risk that two slats are identical i.e. the risk that one slat could replace another in the wrong place if it has enough complementary handles
    # for now, no special index validation is provided for this feature.
    if request_substitute_risk_score:
        duplicate_results = []
        for bag in [bag_of_slat_handles, bag_of_slat_antihandles]:
            duplicate_product_indices = []
            for i, ((hkey, _), (hkey2, _)) in enumerate(product(bag.items(), bag.items())):
                if hkey == hkey2:
                    duplicate_product_indices.append(False)
                else:
                    duplicate_product_indices.append(True)
            duplicate_results.append(precise_hamming_compute(bag, bag, duplicate_product_indices, slat_length))

        global_min = np.inf
        for sim_list in duplicate_results:
            global_min = np.min([np.min(sim_list), global_min])
        score_dict['Substitute Risk'] = np.int64(global_min)

    # the individual scores for the components requested are computed here
    if universal_check:
        score_dict['Universal'] = np.min(hamming_results)
    if per_layer_check:
        for layer, indices in layer_indices.items():
            score_dict[f'Layer {layer}'] = np.min(hamming_results[indices])
    if specific_slat_groups:
        for group_key, indices in group_indices.items():
            score_dict[group_key] = np.min(hamming_results[indices])
    if partial_area_score:
        for group_key, slat_dict in partial_area_score.items():
            #selected_indices = np.array([(x,y) for x,y in slat_dict["handles"].keys()] + [(x,y) for x,y in slat_dict["antihandles"].keys()], dtype=np.uint16)
            score_dict[group_key] = np.min(hamming_results_partial[group_key])

    return score_dict


