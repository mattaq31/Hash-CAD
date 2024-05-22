import numpy as np
from itertools import product
import time
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import os


def generate_standard_square_slats(slat_count=32):
    """
    Generates a base array for a square megastructure design
    :param slat_count: Number of handle positions in each slat
    :return: 3D numpy array with x/y slat positions and a list of the unique slat IDs for each layer
    """
    base_array = np.zeros((slat_count, slat_count, 2))  # width, height, X/Y slat ID

    for i in range(1, slat_count+1):  # slats are 1-indexed and must be connected
        base_array[:, i-1, 1] = i
        base_array[i-1, :, 0] = i

    unique_slats_per_layer = []
    for i in range(base_array.shape[2]):
        slat_ids = np.unique(base_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    return base_array, unique_slats_per_layer


def read_design_from_excel(folder, sheets):
    """
    Reads a megastructure design pre-populated in excel.  0s indicate no slats, all other numbers are slat IDs
    :param folder: Folder containing excel sheets
    :param sheets: List of sheets containing the positions of slats (in order, starting from the bottom layer)
    :return: 3D numpy array with x/y slat positions
    """
    slat_masks = []
    dims = None
    for sheet in sheets:
        slat_masks.append(np.loadtxt(os.path.join(folder, sheet), delimiter=",", dtype=int))
        if dims:
            if slat_masks[-1].shape != dims:
                raise ValueError('All sheets must have the same dimensions')
        else:
            dims = slat_masks[-1].shape

    base_array = np.zeros((dims[0], dims[1], len(slat_masks)))

    for i, mask in enumerate(slat_masks):
        base_array[..., i] = mask

    return base_array


def generate_random_slat_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2]-1))
    handle_array = np.random.randint(1, unique_sequences+1, size=handle_array.shape)
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i+2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections
    return handle_array


def update_random_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the handle array with new random values inplace
    :param handle_array: Pre-populated handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > 0] = np.random.randint(1, unique_sequences+1, size=handle_array[handle_array > 0].shape)


def calculate_slat_hamming(base_array, handle_array, unique_slats_per_layer, unique_sequences=32):
    """
    Calculates the hamming distance between all possible combinations of slat handles.
    The higher the number, the less kinetic traps there should be.
    TODO: Could this function be even quicker?
    TODO: Can inputs be transformed a different way?
    :param base_array: Slat position array (3D)
    :param handle_array: Handle ID array (2D)
    :param unique_slats_per_layer: List of unique slat IDs for each layer
    :param unique_sequences: Max unique sequences in the handle array
    :return: combination matrices (TODO: remove), results array with hamming distance for each possible slat combination
    """
    # TODO: this system includes a potentially large amount of useless computation for slats that are entirely 0s (control handles).  A more intelligent system could potentially sort out the non-interacting slats, but is this worth it?

    single_combo = 4*unique_sequences  # max combinations for a single slat pair

    individual_layer_slat_count = [len(u) for u in unique_slats_per_layer]

    # TODO: is it worth only computing hamming distances for individual layers rather than the entire set of slats all at once?
    individal_layer_combos = [single_combo * individual_layer_slat_count[i] * individual_layer_slat_count[i+1] for i in range(handle_array.shape[-1])]

    # these slat counts assume each layer has the maximum amount of handles, even if some will be replaced by control handles.  This is to simplify the computation logic.
    handle_slat_counts = individual_layer_slat_count[:-1]
    antihandle_slat_counts = individual_layer_slat_count[1:]

    total_combos = single_combo*sum(handle_slat_counts)*sum(antihandle_slat_counts)

    combination_matrix_1 = np.zeros((total_combos, unique_sequences))
    combination_matrix_2 = np.zeros((total_combos, unique_sequences))

    handle_slats_with_layers = []
    anti_handle_slats_with_layers = []

    for layer, slats in enumerate(unique_slats_per_layer[:-1]):
        handle_slats_with_layers.extend([(layer, h) for h in slats])
    for layer, slats in enumerate(unique_slats_per_layer[1:]):
        anti_handle_slats_with_layers.extend([(layer+1, ah) for ah in slats])

    # to speed things up, loops are only used to pre-populate arrays
    # then, hamming distance computed in one go at the end only (numpy is most efficient with matrix operations)
    for i, (handle_slat, antihandle_slat) in enumerate(product(handle_slats_with_layers, anti_handle_slats_with_layers)):
        h_layer, h_slat_id = handle_slat[0], handle_slat[1]
        ah_layer, ah_slat_id = antihandle_slat[0], antihandle_slat[1]
        cm1_insertion_array = handle_array[base_array[..., h_layer] == h_slat_id, h_layer] # slat directions are computed top-down, left-right

        # pre-computes to save time
        for j in range(unique_sequences):
            # 4 combinations:
            # 1. X vs Y, rotation to the left
            # 2. X vs Y, rotation to the right
            # 3. X vs Y, rotation to the left, reversed X
            # 4. X vs Y, rotation to the right, reversed X
            # All rotations padded with zeros (already in array)
            # TODO: could this be sped up even further?
            combination_matrix_1[(i*single_combo) + j, :unique_sequences-j] = cm1_insertion_array[j:]
            combination_matrix_1[(i*single_combo) + unique_sequences + j, j:] = cm1_insertion_array[:unique_sequences-j]
            combination_matrix_1[(i*single_combo) + (2*unique_sequences) + j, :unique_sequences-j] = cm1_insertion_array[::-1][j:]
            combination_matrix_1[(i*single_combo) + (3*unique_sequences) + j, j:] = cm1_insertion_array[::-1][:unique_sequences-j]

        # y-slats can be left as is throughout whole matrix
        combination_matrix_2[i*single_combo:(i+1)*single_combo, :] = handle_array[base_array[..., ah_layer] == ah_slat_id, ah_layer-1]

    # actual hamming distance computation (0s should be ignored as they are non-interacting control handles!)
    results = np.count_nonzero(np.logical_or(combination_matrix_1 != combination_matrix_2, combination_matrix_1 == 0, combination_matrix_2 == 0), axis=1)

    return combination_matrix_1, combination_matrix_2, results

    # This piece of code handles the case where only H-AH combos are computed within specific layers.  Is this worth keeping?  Probably not, as each layer can be packaged and computed separately.
    # for handle_layer in range(handle_array.shape[2]):
    #     for i, (handle_slat, antihandle_slat) in enumerate(product(unique_slats_per_layer[handle_layer], unique_slats_per_layer[handle_layer+1])):
    #         cm1_insertion_array = handle_array[base_array[..., handle_layer] == handle_slat, handle_layer]  # pre-computes to save time
    #         for j in range(unique_sequences):
    #             # 4 combinations:
    #             # 1. X vs Y, rotation to the left
    #             # 2. X vs Y, rotation to the right
    #             # 3. X vs Y, rotation to the left, reversed X
    #             # 4. X vs Y, rotation to the right, reversed X
    #             # All rotations padded with zeros (already in array)
    #             # TODO: could this be sped up even further?
    #             combination_matrix_1[((handle_layer)*individal_layer_combos[handle_layer-1]) + (i*single_combo) + j, :unique_sequences-j] = cm1_insertion_array[j:]
    #             combination_matrix_1[((handle_layer)*individal_layer_combos[handle_layer-1]) + (i*single_combo) + unique_sequences + j, j:] = cm1_insertion_array[:unique_sequences-j]
    #             combination_matrix_1[((handle_layer)*individal_layer_combos[handle_layer-1]) + (i*single_combo) + (2*unique_sequences) + j, :unique_sequences-j] = cm1_insertion_array[::-1][j:]
    #             combination_matrix_1[((handle_layer)*individal_layer_combos[handle_layer-1]) + (i*single_combo) + (3*unique_sequences) + j, j:] = cm1_insertion_array[::-1][:unique_sequences-j]
    #
    #         # y-slats can be left as is throughout whole matrix
    #         combination_matrix_2[((handle_layer)*individal_layer_combos[handle_layer-1]) + i*single_combo:(i+1)*single_combo, :] = handle_array[base_array[..., handle_layer+1] == antihandle_slat, handle_layer]


def generate_handle_set_and_optimize(base_array, unique_sequences=32, min_hamming=25, max_rounds=30):
    """
    Generates a handle set and optimizes it for kinetic traps
    :param base_array: Slat position array (3D)
    :param unique_sequences: Max unique sequences in the handle array
    :param min_hamming: If this Hamming distance is achieved, stops optimization early
    :param max_rounds: Maximum number of rounds to run the optimization
    :return: 2D array with handle IDs
    """
    handle_array = generate_random_slat_handles(base_array, unique_sequences)

    unique_slats_per_layer = []
    for i in range(base_array.shape[2]):
        slat_ids = np.unique(base_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    _, _, res = calculate_slat_hamming(base_array, handle_array, unique_slats_per_layer, unique_sequences)
    print('Optimizing kinetic traps...')

    best_array = handle_array
    best_hamming = 0

    with tqdm(total=max_rounds, desc='Kinetic Trap Check') as pbar:
        for i in range(max_rounds):
            update_random_slat_handles(handle_array)
            _, _, res = calculate_slat_hamming(base_array, handle_array, unique_slats_per_layer, unique_sequences)
            new_hamming = np.min(res)
            if new_hamming > best_hamming:
                best_hamming = new_hamming
                best_array = np.copy(handle_array)
            pbar.update(1)
            pbar.set_postfix(**{'Latest Hamming Distance': new_hamming, 'Best Hamming Distance': best_hamming})
            if best_hamming >= min_hamming:
                print('Optimization concluding early - target Hamming distance achieved.')
                break

    print('Optimization complete - final best hamming distance: %s' % best_hamming)

    return best_array


def attach_cargo_handles_to_core_sequences(pattern, sequence_map, target_plate, slat_type='X', handle_side=2):
    """
    TODO: extend for any shape (currently only 2D squares)
    Concatenates cargo handles to provided sequences according to cargo pattern.
    :param pattern: 2D array showing where each cargo handle will be attached to a slat
    :param sequence_map: Sequence to use for each particular cargo handle in pattern
    :param target_plate: Plate class containing all the pre-mapped sequences/wells for the selected slats
    :param slat_type: Type of slat to attach to (X or Y)
    :param handle_side: H2 or H5 handle position
    :return: Dataframe containing all new sequences to be ordered for cargo attachment
    """
    if slat_type.upper() not in ['X', 'Y']:
        raise ValueError('Slat type must be either X or Y')

    seq_dict = defaultdict(list)

    # BEWARE: axis 0 is the y-axis, axis 1 is the x-axis
    dimension_check = 0
    if slat_type.upper() == 'X':
        dimension_check = 1
    for i in range(1, pattern.shape[dimension_check]+1):
        if slat_type.upper() == 'X':
            unique_cargo = np.unique(pattern[:, i-1])
        else:
            unique_cargo = np.unique(pattern[i-1, :])
        for cargo in unique_cargo:
            if cargo < 1:  # no cargo
                continue
            core_sequence = target_plate.get_sequence(i, handle_side, 0)
            seq_dict['Cargo ID'].append(cargo)
            seq_dict['Sequence'].append(core_sequence + 'tt' + sequence_map[cargo])
            seq_dict['Slat Pos. ID'].append(i)

    seq_df = pd.DataFrame.from_dict(seq_dict)

    return seq_df


# TESTING AREA ONLY
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    np.random.seed(8)
    base_array, unique_slats_per_layer = generate_standard_square_slats(32)
    # base_array, x_slats, y_slats = read_design_from_file(folder, sheetnames)

    handle_array = generate_random_slat_handles(base_array)

    for i in tqdm(range(30)):
        t1 = time.time()
        c1, c2, res = calculate_slat_hamming(base_array, handle_array, unique_slats_per_layer, unique_sequences=32)
        update_random_slat_handles(handle_array)
        t2 = time.time()
        print('Time: %s, Min: %s, Max: %s' % (t2-t1, np.min(res), np.max(res)))

        # plt.hist(res, bins=np.arange(0.5, 33, 1))
        # plt.yscale('log')
        # plt.title('Min: %s, Max: %s' % (np.min(res), np.max(res)))
        # plt.show()
        # plt.close()
