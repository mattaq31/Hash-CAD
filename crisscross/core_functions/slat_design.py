import numpy as np
from itertools import product
import time
from tqdm import tqdm
import pandas as pd
from collections import defaultdict, OrderedDict
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
