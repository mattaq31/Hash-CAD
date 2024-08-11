import numpy as np
from itertools import product
from tqdm import tqdm
from collections import defaultdict, OrderedDict


def compute_hamming(handle_dict, antihandle_dict, valid_product_indices, slat_length):
    """
    Given a dictionary of slat handles and antihandles, this function computes the hamming distance between all possible combinations.
    :param handle_dict: Dictionary of handles i.e. {slat_id: slat_handle_array}
    :param antihandle_dict: Dictionary of antihandles i.e. {slat_id: slat_antihandle_array}
    :param valid_product_indices: A list of indices matching the possible products that should be computed (i.e. if a product is not being requested, the index should be False)
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """
    single_combo = 4 * slat_length
    total_combos = single_combo * sum(valid_product_indices)
    combination_matrix_1 = np.zeros((total_combos, slat_length))
    combination_matrix_2 = np.zeros((total_combos, slat_length))
    valid_combo_index = 0
    for i, ((hk, handle_slat), (ahk, antihandle_slat)) in enumerate(
            product(handle_dict.items(), antihandle_dict.items())):
        if valid_product_indices[i]:
            for j in range(slat_length):
                # 4 combinations:
                # 1. X vs Y, rotation to the left
                # 2. X vs Y, rotation to the right
                # 3. X vs Y, rotation to the left, reversed X
                # 4. X vs Y, rotation to the right, reversed X
                # All rotations padded with zeros (already in array)
                # TODO: could this be sped up even further?
                combination_matrix_1[(valid_combo_index * single_combo) + j, :slat_length - j] = handle_slat[j:]
                combination_matrix_1[(valid_combo_index * single_combo) + slat_length + j, j:] = handle_slat[:slat_length - j]
                combination_matrix_1[(valid_combo_index * single_combo) + (2 * slat_length) + j, :slat_length - j] = handle_slat[::-1][j:]
                combination_matrix_1[(valid_combo_index * single_combo) + (3 * slat_length) + j, j:] = handle_slat[::-1][:slat_length - j]
            combination_matrix_2[valid_combo_index * single_combo:(valid_combo_index + 1) * single_combo, :] = antihandle_slat
            valid_combo_index += 1
    results = np.count_nonzero(np.logical_or(combination_matrix_1 != combination_matrix_2, combination_matrix_1 == 0, combination_matrix_2 == 0), axis=1)
    return results


def generate_random_slat_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2] - 1))
    handle_array = np.random.randint(1, unique_sequences + 1, size=handle_array.shape)
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i + 2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections
    return handle_array


def generate_layer_split_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, with the possible ids split between each layer,
    with the goal of preventing a single slat from being self-complementary.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2] - 1))

    for i in range(handle_array.shape[2]):
        if i % 2 == 0:
            h1 = 1
            h2 = int(unique_sequences / 2) + 1
        else:
            h1 = int(unique_sequences / 2) + 1
            h2 = unique_sequences + 1
        layer_handle_array = np.random.randint(h1, h2, size=(handle_array.shape[0], handle_array.shape[1]))
        handle_array[..., i] = layer_handle_array
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i + 2] == 0,
                            axis=-1), i] = 0  # no handles where there are no slats, or no slat connections
    return handle_array


def update_split_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the split handle array with new random values inplace
    :param handle_array: Pre-populated split handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > (unique_sequences / 2)] = np.random.randint(int(unique_sequences / 2) + 1, unique_sequences + 1, size=handle_array[handle_array > (unique_sequences / 2)].shape)
    handle_array[((unique_sequences / 2) >= handle_array) & (handle_array > 0)] = np.random.randint(1, int(unique_sequences / 2) + 1, size=handle_array[((unique_sequences / 2) >= handle_array) & (handle_array > 0)].shape)


def update_random_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the handle array with new random values inplace
    :param handle_array: Pre-populated handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > 0] = np.random.randint(1, unique_sequences + 1, size=handle_array[handle_array > 0].shape)


def multi_rule_hamming(slat_array, handle_array, universal_check=True, per_layer_check=False,
                       specific_slat_groups=None, slat_length=32, request_substitute_risk_score=False):
    """
    Given a slat and handle array, this function computes the hamming distance of all handle/antihandle combinations provided.
    Scores for individual components, such as specific slat groups, can also be requested.
    :param slat_array: Array of XxYxZ dimensions, where X and Y are the dimensions of the design and Z is the number of layers in the design
    :param handle_array: Array of XxYxZ-1 dimensions containing the IDs of all the handles in the design
    :param universal_check: Set to true to provide a hamming score for the entire set of slats in the design
    :param per_layer_check: Set to true to provide a hamming score for the individual layers of the design (i.e. the interface between each layer)
    :param specific_slat_groups: Provide a dictionary, where the key is a group name and the value is a list of tuples containing the layer and slat ID of the slats in the group for which the specific hamming distance is being requested.
    :param slat_length: The length of a single slat (must be an integer)
    :param request_substitute_risk_score: Set to true to provide a measure of the largest amount of handle duplication between slats of the same type (handle or antihandle)
    :return: Dictionary of scores for each of the aspects requested from the design
    """

    # identifies all slats in design
    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    # extracts handle values for all slats in the design
    bag_of_slat_handles = OrderedDict()
    bag_of_slat_antihandles = OrderedDict()
    score_dict = {}
    for layer_position, layer_slats in enumerate(unique_slats_per_layer):
        handles_available = True
        antihandles_available = True

        # an assumption is made here that the bottom-most slat will always start with handles, then alternate to anti-handles and so on.
        if layer_position == 0:
            antihandles_available = False
        if layer_position == len(unique_slats_per_layer) - 1:
            handles_available = False
        for slat in layer_slats:
            if handles_available:
                bag_of_slat_handles[(layer_position + 1, slat)] = handle_array[
                    slat_array[..., layer_position] == slat, layer_position]
            if antihandles_available:
                bag_of_slat_antihandles[(layer_position + 1, slat)] = handle_array[
                    slat_array[..., layer_position] == slat, layer_position - 1]

    # in the case that smaller subsets of the entire range of handle/antihandle products are required, this code snippet will remove those products that can be ignored to speed up computation
    valid_product_indices = []
    final_combination_index = 0
    layer_indices = defaultdict(list)
    group_indices = defaultdict(list)
    for i, ((hkey, handle_slat), (antihkey, antihandle_slat)) in enumerate(
            product(bag_of_slat_handles.items(), bag_of_slat_antihandles.items())):
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
    hamming_results = compute_hamming(bag_of_slat_handles, bag_of_slat_antihandles, valid_product_indices, slat_length)

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
            duplicate_results.append(compute_hamming(bag, bag, duplicate_product_indices, slat_length))

        global_min = 32
        for sim_list in duplicate_results:
            global_min = np.min([np.min(sim_list), global_min])
        score_dict['Substitute Risk'] = global_min

    # the individual scores for the components requested are computed here
    if universal_check:
        score_dict['Universal'] = np.min(hamming_results)
    if per_layer_check:
        for layer, indices in layer_indices.items():
            score_dict[f'Layer {layer}'] = np.min(hamming_results[indices])
    if specific_slat_groups:
        for group_key, indices in group_indices.items():
            score_dict[group_key] = np.min(hamming_results[indices])

    return score_dict


def generate_handle_set_and_optimize(base_array, unique_sequences=32, slat_length=32, max_rounds=30,
                                     split_sequence_handles=False, universal_hamming=True, layer_hamming=False,
                                     group_hamming=None, metric_to_optimize='Universal'):
    """
    Generates random handle sets and attempts to choose the best set based on the hamming distance between slat assembly handles.
    :param base_array: Slat position array (3D)
    :param unique_sequences: Max unique sequences in the handle array
    :param slat_length: Length of a single slat
    :param max_rounds: Maximum number of rounds to run the check
    :param split_sequence_handles: Set to true to split the handle sequences between layers evenly
    :param universal_hamming: Set to true to compute the hamming distance for the entire set of slats
    :param layer_hamming: Set to true to compute the hamming distance for the interface between each layer
    :param group_hamming: Provide a dictionary, where the key is a group name and the value is a list
    of tuples containing the layer and slat ID of the slats in the group for which the specific
    hamming distance is being requested.
    :param metric_to_optimize: The metric to optimize for (Universal, Layer X or Group ID)
    :return: 2D array with handle IDs
    """
    best_hamming = 0
    with tqdm(total=max_rounds, desc='Kinetic Trap Check') as pbar:
        for i in range(max_rounds):
            if i == 0:
                if split_sequence_handles:
                    handle_array = generate_layer_split_handles(base_array, unique_sequences)
                else:
                    handle_array = generate_random_slat_handles(base_array, unique_sequences)
                best_array = np.copy(handle_array)
            else:
                if split_sequence_handles:
                    update_split_slat_handles(handle_array)
                else:
                    update_random_slat_handles(handle_array)

            hamming_dict = multi_rule_hamming(base_array, handle_array, universal_check=universal_hamming,
                                              per_layer_check=layer_hamming, specific_slat_groups=group_hamming,
                                              slat_length=slat_length)
            if hamming_dict[metric_to_optimize] > best_hamming:
                best_hamming = hamming_dict[metric_to_optimize]
                best_array = np.copy(handle_array)
            pbar.update(1)
            pbar.set_postfix(**hamming_dict)
    print('Optimization complete - final best hamming distance: %s' % best_hamming)
    return best_array
