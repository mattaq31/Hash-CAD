import numpy as np
from itertools import product
import time
from tqdm import tqdm
import pandas as pd
from collections import defaultdict


def generate_standard_square_slats(slat_count=32):
    """
    Generates a base array for a square megastructure design
    :param slat_count: Number of handle positions in each slat
    :return: 3D numpy array with x/y slat positions, 1D numpy array with x slat ids, 1D numpy array with y slat ids
    """
    base_array = np.zeros((slat_count, slat_count, 2))  # width, height, X/Y slat ID

    for i in range(1, slat_count+1):  # slats are 1-indexed and must be connected
        base_array[:, i-1, 1] = i
        base_array[i-1, :, 0] = i

    x_slat_ids = np.unique(base_array[:, :, 0])
    x_slat_ids = x_slat_ids[x_slat_ids != 0]
    y_slat_ids = np.unique(base_array[:, :, 1])
    y_slat_ids = y_slat_ids[y_slat_ids != 0]

    return base_array, x_slat_ids, y_slat_ids


def read_design_from_excel(folder, x_sheet, y_sheet):
    """
    Reads a megastructure design pre-populated in excel.  0s indicate no slats, all other numbers are slat IDs
    :param folder: Folder containing excel sheets
    :param x_sheet: Sheet containing x slat positions
    :param y_sheet: Sheet containing y slat positions
    :return: 3D numpy array with x/y slat positions, 1D numpy array with x slat ids, 1D numpy array with y slat ids
    TODO: what to do in case of multi-layer designs?
    """

    YMask = np.loadtxt(folder + x_sheet, delimiter=",", dtype=int)
    XMask = np.loadtxt(folder + y_sheet, delimiter=",", dtype=int)

    base_array = np.zeros((XMask.shape[0], XMask.shape[1], 2))
    base_array[..., 0] = XMask
    base_array[..., 1] = YMask

    x_slat_ids = np.unique(base_array[:, :, 0])
    x_slat_ids = x_slat_ids[x_slat_ids != 0]
    y_slat_ids = np.unique(base_array[:, :, 1])
    y_slat_ids = y_slat_ids[y_slat_ids != 0]

    return base_array, x_slat_ids, y_slat_ids


def generate_random_slat_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1]))
    handle_array = np.random.randint(1, unique_sequences+1, size=handle_array.shape)
    handle_array[np.all(base_array == 0, axis=-1)] = 0  # no handles where there are no slats
    handle_array[np.logical_xor(base_array[..., 0] == 0, base_array[..., 1] == 0)] = -1 # control handles (no attachment)
    return handle_array


def update_random_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the handle array with new random values inplace
    :param handle_array: Pre-populated handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > 0] = np.random.randint(1, unique_sequences+1, size=handle_array[handle_array > 0].shape)


def calculate_slat_hamming(base_array, handle_array, x_slats, y_slats, unique_sequences=32):
    """
    Calculates the hamming distance between all possible combinations of slat handles.
    The higher the number, the less kinetic traps there should be.
    TODO: Could this function be even quicker?  How would it deal with multi-layer designs?
    TODO: Can inputs be transformed a different way?
    :param base_array: Slat position array (3D)
    :param handle_array: Handle ID array (2D)
    :param x_slats: List of x-slat IDs
    :param y_slats: List of y-slat IDs
    :param unique_sequences: Max unique sequences in the handle array
    :return: combination matrices (TODO: remove), results array with hamming distance for each possible slat combination
    """

    single_combo = 4*unique_sequences  # max combinations for a single slat pair
    total_combos = single_combo*len(x_slats)*len(x_slats)  # total number of combinations

    combination_matrix_1 = np.zeros((total_combos, unique_sequences))
    combination_matrix_2 = np.zeros((total_combos, unique_sequences))

    # to speed things up, loops are only used to pre-populate arrays
    # then, hamming distance computed in one go at the end only (numpy is most efficient with matrix operations)
    for i, (x_slat, y_slat) in enumerate(product(x_slats, y_slats)):
        cm1_insertion_array = handle_array[base_array[..., 0] == x_slat]  # pre-computes to save time
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
        combination_matrix_2[i*single_combo:(i+1)*single_combo, :] = handle_array[base_array[..., 1] == y_slat]

    # prevents the -1s (control handles) from being counted as identical sequences (ys are changed to -2 instead)
    combination_matrix_2[combination_matrix_2 == -1] = -2

    # actual hamming distance computation
    results = np.count_nonzero(combination_matrix_1 != combination_matrix_2, axis=1)

    return combination_matrix_1, combination_matrix_2, results


def generate_handle_set_and_optimize(base_array, x_slats, y_slats, unique_sequences=32, min_hamming=25, max_rounds=30):
    """
    Generates a handle set and optimizes it for kinetic traps
    :param base_array: Slat position array (3D)
    :param x_slats: List of x-slat IDs
    :param y_slats: List of y-slat IDs
    :param unique_sequences: Max unique sequences in the handle array
    :param min_hamming: If this Hamming distance is achieved, stops optimization early
    :param max_rounds: Maximum number of rounds to run the optimization
    :return: 2D array with handle IDs
    """
    handle_array = generate_random_slat_handles(base_array, unique_sequences)
    _, _, res = calculate_slat_hamming(base_array, handle_array, x_slats, y_slats, unique_sequences)
    print('Optimizing kinetic traps...')

    best_array = handle_array
    best_hamming = 0

    with tqdm(total=max_rounds, desc='Kinetic Trap Check') as pbar:
        for i in range(max_rounds):
            update_random_slat_handles(handle_array)
            _, _, res = calculate_slat_hamming(base_array, handle_array, x_slats, y_slats, unique_sequences)
            new_hamming = np.min(res)
            if new_hamming > best_hamming:
                best_hamming = new_hamming
                best_array = handle_array
            pbar.update(1)
            pbar.set_postfix(**{'Latest Hamming Distance': new_hamming, 'Best Hamming Distance': best_hamming})
            if best_hamming >= min_hamming:
                print('Optimization concluding early - target Hamming distance achieved.')
                break

    print('Optimization complete - final best hamming distance: %s' % best_hamming)

    return best_array


def attach_cargo_handles_to_slats(pattern, sequence_map, core_sequence_plate, slat_type='X', handle_side='h2'):
    """
    TODO: extend for any shape (currently only 2D squares)
    Concatenates cargo handles to provided sequences according to cargo pattern.
    :param pattern: 2D array showing where each cargo handle will be attached to a slat
    :param sequence_map: Sequence to use for each particular cargo handle in pattern
    :param core_sequence_plate: Pandas dataframe containing the sequences for each handle position
    :param slat_type: Type of slat to attach to (X or Y)
    :return: Dataframe containing all new sequences to be ordered for cargo attachment
    """
    seq_dict = defaultdict(list)
    combinations_seen = set()
    # BEWARE: axis 0 is the y-axis, axis 1 is the x-axis
    for i in range(pattern.shape[0]):
        for j in range(pattern.shape[1]):
            if slat_type == 'y':
                slat_pos_id = i+1
            else:
                slat_pos_id = j+1
            if handle_side == 'h5':
                slat_pos_id += 32
            if pattern[i, j] > 0 and (slat_pos_id, pattern[i, j]) not in combinations_seen:
                core_name = 'slatcore-%s-%sctrl' % (slat_pos_id, handle_side)
                core_sequence = core_sequence_plate['sequence'][core_sequence_plate['name'].str.contains(core_name)].values[0]
                seq_dict['Cargo ID'].append(pattern[i, j])
                seq_dict['Sequence'].append(core_sequence + 'tt' + sequence_map[pattern[i, j]])

                if handle_side == 'h2': # TODO: again, super convoluted
                    seq_dict['Slat Pos. ID'].append(slat_pos_id)
                else:
                    seq_dict['Slat Pos. ID'].append(slat_pos_id-32)

                combinations_seen.add((slat_pos_id, pattern[i, j]))

    seq_df = pd.DataFrame.from_dict(seq_dict)

    return seq_df


# TESTING AREA ONLY
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    np.random.seed(8)
    base_array, x_slats, y_slats = generate_standard_square_slats(32)
    # base_array, x_slats, y_slats = read_design_from_file(folder, sheetnames)

    handle_array = generate_random_slat_handles(base_array)

    for i in tqdm(range(30)):
        t1 = time.time()
        c1, c2, res = calculate_slat_hamming(base_array, handle_array, x_slats, y_slats, unique_sequences=32)
        update_random_slat_handles(handle_array)
        t2 = time.time()
        print('Time: %s, Min: %s, Max: %s' % (t2-t1, np.min(res), np.max(res)))

        # plt.hist(res, bins=np.arange(0.5, 33, 1))
        # plt.yscale('log')
        # plt.title('Min: %s, Max: %s' % (np.min(res), np.max(res)))
        # plt.show()
        # plt.close()
