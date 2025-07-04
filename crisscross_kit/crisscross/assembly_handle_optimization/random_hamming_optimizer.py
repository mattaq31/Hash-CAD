import numpy as np
from tqdm import tqdm

from crisscross.assembly_handle_optimization import generate_layer_split_handles, generate_random_slat_handles, \
    update_split_slat_handles, update_random_slat_handles
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming


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
                if np.sum(handle_array) == 0:
                    print('No handle optimization conducted as no handle positions were found in the slat array provided.')
                    return handle_array
                best_array = np.copy(handle_array)
            else:
                if split_sequence_handles:
                    update_split_slat_handles(handle_array)
                else:
                    update_random_slat_handles(handle_array)

            hamming_dict = multirule_precise_hamming(base_array, handle_array, universal_check=universal_hamming,
                                                     per_layer_check=layer_hamming, specific_slat_groups=group_hamming,
                                                     slat_length=slat_length)
            if hamming_dict[metric_to_optimize] > best_hamming:
                best_hamming = hamming_dict[metric_to_optimize]
                best_array = np.copy(handle_array)
            pbar.update(1)
            pbar.set_postfix({**{f'Current best {metric_to_optimize}': best_hamming}, **hamming_dict})

    print('Optimization complete - final best hamming distance: %s' % best_hamming)
    return best_array
