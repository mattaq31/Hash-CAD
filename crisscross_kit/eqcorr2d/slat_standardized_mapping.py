import os
import pandas as pd
import numpy as np
from pathlib import Path

slat_database_file = 'slat_database.xlsx'

this_folder = str(Path(__file__).resolve().parents[0])


def convert_to_triangular(coord):
    """
    Equation applied: x(new) = (x+y)/2, y(new) = -x
    """
    return -int(coord[1]), int((coord[0] + coord[1])/2)


def convert_triangular_coords_to_array(coords):
    """
    Converts a list of triangular coordinates into a numpy array.
    """

    # Find min in each dimension
    min_x = min(x for x, y in coords)
    min_y = min(y for x, y in coords)

    # Shift so minima become 0
    shifted = [(x - min_x, y - min_y) for x, y in coords]

    # Determine size of new array
    max_row = max(r for r, c in shifted) + 1
    max_col = max(c for r, c in shifted) + 1

    # Initialize array with zeros
    arr = np.zeros((max_row, max_col), dtype=int)

    # Place index of each coordinate in array
    for idx, (r, c) in enumerate(shifted):
        arr[r, c] = idx + 1

    return arr

def generate_standardized_slat_handle_array(slat_1D_array, slat_type):
    """
    Given a list of slat handles in order, assign handles to their corresponding standardized slat shape, which can then
    be used downstream in handle match strength calculations.
    :param slat_1D_array: 1D numpy array containing slat handles
    :param slat_type: Slat type shape to use for matching
    :return: Updated 2D numpy array containing slat handles in standardized shape
    """
    standardized_handle_array = standardized_slat_mappings[slat_type].copy()
    for position, value in enumerate(slat_1D_array):
        standardized_handle_array[standardized_slat_mappings[slat_type]==position+1] = value
    return standardized_handle_array


# this reads the basic positional mappings for special slat types,
# which makes it easy to convert them to a standardized shape, which in turn
# helps simplify our handle match comparison algorithms
all_slat_maps = pd.read_excel(os.path.join(this_folder, slat_database_file), sheet_name=None, header=None)
standardized_slat_mappings = {}
triangular_coordinate_slat_mappings = {}

for sheet_name, df in all_slat_maps.items():
    base_array = df.to_numpy()

    # extracts coordinates
    coords = [tuple(coord) for coord in np.argwhere(base_array > 0)[np.argsort(base_array[base_array > 0])]]

    # transforms to triangular coordinates and assigns to dictionary
    conv_coords = [convert_to_triangular(c) for c in coords]
    new_transformed_array = convert_triangular_coords_to_array(conv_coords)

    standardized_slat_mappings[sheet_name] = new_transformed_array
