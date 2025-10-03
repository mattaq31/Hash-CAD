import os
import pandas as pd
import numpy as np
from pathlib import Path

slat_database_file = 'slat_database.xlsx'

this_folder = str(Path(__file__).resolve().parents[0])

# this reads the basic positional mappings for special slat types,
# which makes it easy to convert them to a standardized shape, which in turn
# helps simplify our handle match comparison algorithms
all_slat_maps = pd.read_excel(os.path.join(this_folder, slat_database_file), sheet_name=None, header=None)
standardized_slat_mappings = {}
triangular_coordinate_slat_mappings = {}

def convert_to_triangular(coord):
    return int((coord[0] - coord[1])/2), int(coord[1])


def convert_coords_to_array(coords):
    # Find the needed array size (max row/col + 1)
    max_row = max(r for r, c in coords) + 1
    max_col = max(c for r, c in coords) + 1

    # Initialize array with zeros (or -1 if you want empty spots marked)
    arr = np.zeros((max_row, max_col), dtype=int)

    # Place index of each coordinate in array
    for idx, (r, c) in enumerate(coords):
        arr[r, c] = idx + 1

    return arr

for sheet_name, df in all_slat_maps.items():
    base_array = df.to_numpy()
    # extracts coordinates
    coords = [tuple(coord) for coord in np.argwhere(base_array > 0)[np.argsort(base_array[base_array > 0])]]
    conv_coords = [convert_to_triangular(c) for c in coords]
    # new_transformed_array = np.rot90(convert_coords_to_array(conv_coords))
    new_transformed_array = convert_coords_to_array(conv_coords)

    standardized_slat_mappings[sheet_name] = base_array
