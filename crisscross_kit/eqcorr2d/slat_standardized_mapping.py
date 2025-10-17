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
    return -int(coord[1]), int((coord[0] + coord[1]) / 2)


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
        standardized_handle_array[standardized_slat_mappings[slat_type] == position + 1] = value
    return standardized_handle_array


# this sets up the basic positional mappings for special slat types,
# which makes it easy to convert them to a standardized shape, which in turn
# helps simplify our handle match comparison algorithms
all_slat_maps = {}
standardized_slat_mappings = {}
triangular_coordinate_slat_mappings = {}

# to add new slat types, export to excel, read in as a pandas dataframe, convert to numpy array, and then print and add to the dictionary here.
all_slat_maps['DB-L-120'] = np.array([[0, 0],
                                      [0, 1],
                                      [32, 0],
                                      [0, 2],
                                      [31, 0],
                                      [0, 3],
                                      [30, 0],
                                      [0, 4],
                                      [29, 0],
                                      [0, 5],
                                      [28, 0],
                                      [0, 6],
                                      [27, 0],
                                      [0, 7],
                                      [26, 0],
                                      [0, 8],
                                      [25, 0],
                                      [0, 9],
                                      [24, 0],
                                      [0, 10],
                                      [23, 0],
                                      [0, 11],
                                      [22, 0],
                                      [0, 12],
                                      [21, 0],
                                      [0, 13],
                                      [20, 0],
                                      [0, 14],
                                      [19, 0],
                                      [0, 15],
                                      [18, 0],
                                      [0, 16],
                                      [17, 0]])

all_slat_maps['DB-L-60'] = np.array([[32, 0],
                                     [0, 1],
                                     [31, 0],
                                     [0, 2],
                                     [30, 0],
                                     [0, 3],
                                     [29, 0],
                                     [0, 4],
                                     [28, 0],
                                     [0, 5],
                                     [27, 0],
                                     [0, 6],
                                     [26, 0],
                                     [0, 7],
                                     [25, 0],
                                     [0, 8],
                                     [24, 0],
                                     [0, 9],
                                     [23, 0],
                                     [0, 10],
                                     [22, 0],
                                     [0, 11],
                                     [21, 0],
                                     [0, 12],
                                     [20, 0],
                                     [0, 13],
                                     [19, 0],
                                     [0, 14],
                                     [18, 0],
                                     [0, 15],
                                     [17, 0],
                                     [0, 16]])

all_slat_maps['DB-R-60'] = np.array([
    [0, 0],
    [0, 32],
    [1, 0],
    [0, 31],
    [2, 0],
    [0, 30],
    [3, 0],
    [0, 29],
    [4, 0],
    [0, 28],
    [5, 0],
    [0, 27],
    [6, 0],
    [0, 26],
    [7, 0],
    [0, 25],
    [8, 0],
    [0, 24],
    [9, 0],
    [0, 23],
    [10, 0],
    [0, 22],
    [11, 0],
    [0, 21],
    [12, 0],
    [0, 20],
    [13, 0],
    [0, 19],
    [14, 0],
    [0, 18],
    [15, 0],
    [0, 17],
    [16, 0]
])

all_slat_maps['DB-R-120'] = np.array([[1, 0],
                                      [0, 32],
                                      [2, 0],
                                      [0, 31],
                                      [3, 0],
                                      [0, 30],
                                      [4, 0],
                                      [0, 29],
                                      [5, 0],
                                      [0, 28],
                                      [6, 0],
                                      [0, 27],
                                      [7, 0],
                                      [0, 26],
                                      [8, 0],
                                      [0, 25],
                                      [9, 0],
                                      [0, 24],
                                      [10, 0],
                                      [0, 23],
                                      [11, 0],
                                      [0, 22],
                                      [12, 0],
                                      [0, 21],
                                      [13, 0],
                                      [0, 20],
                                      [14, 0],
                                      [0, 19],
                                      [15, 0],
                                      [0, 18],
                                      [16, 0],
                                      [0, 17]])

for sheet_name, base_array in all_slat_maps.items():
    # extracts coordinates
    coords = [tuple(coord) for coord in np.argwhere(base_array > 0)[np.argsort(base_array[base_array > 0])]]

    # transforms to triangular coordinates and assigns to dictionary
    conv_coords = [convert_to_triangular(c) for c in coords]
    new_transformed_array = convert_triangular_coords_to_array(conv_coords)

    standardized_slat_mappings[sheet_name] = new_transformed_array
