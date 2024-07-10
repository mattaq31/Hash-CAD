
import numpy as np
import pandas as pd
import os


# For getting inventory plate drivers
from os.path import join
import ast

from crisscross.plate_mapping import get_plateclass

from generic_cargo_importer import createGenericPlate


def slat_dict_to_array(grid_dict, trim_offset = False):
    """
    Converts a slat dictionary (produced by javascript) into a slat array.
    :param grid_dict: dictionary of slat IDs by (x,y,layer) coordinates.
    :param trim_offset: If true, will trim unoccupied positions from top/left of array. If false, will leave full array.
    :return: array - slat IDs by (x,y,layer) coordinates.
    """
    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in grid_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in grid_dict.keys()) + 1
    min_x = 0 #min(int(key.split(',')[0]) for key in grid_dict.keys())
    min_y = 0 #min(int(key.split(',')[1]) for key in grid_dict.keys())
    max_layer = max(int(key.split(',')[2]) for key in grid_dict.keys()) + 1

    if(trim_offset==True):
        min_x = min(int(key.split(',')[0]) for key in grid_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in grid_dict.keys())

    # Initialize the array
    array = np.zeros((max_x-min_x, max_y-min_y, max_layer))

    # Populate the array
    for key, slatId in grid_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x-min_x, y-min_y, layer] = slatId

    return array

def cargo_dict_to_array(grid_dict, trim_offset = False, slat_grid_dict ={}):
    """
    Converts a cargo dictionary (produced by javascript) into a cargo array.
    :param grid_dict: dictionary of cargo IDs by (x,y,layer) coordinates.
    :param trim_offset: If true, will trim unoccupied positions from top/left of array. If false, will leave full array.
    :param slat_grid_dict: If trim_offset is set to true, will trim based upon the shape of the slat dictionary
    :return: array - cargo types/IDs by (x,y,layer) coordinates.
    """

    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in grid_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in grid_dict.keys()) + 1
    min_x = 0
    min_y = 0
    max_layer = max(int(key.split(',')[2]) for key in grid_dict.keys()) + 1

    if (trim_offset == True):
        max_x = max(int(key.split(',')[0]) for key in slat_grid_dict.keys()) + 1
        max_y = max(int(key.split(',')[1]) for key in slat_grid_dict.keys()) + 1
        min_x = min(int(key.split(',')[0]) for key in slat_grid_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in slat_grid_dict.keys())

    # Initialize the array
    array = np.zeros((max_x-min_x, max_y-min_y, max_layer), dtype='<U100')

    # Populate the array
    for key, cargo_type in grid_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x-min_x, y-min_y, layer] = str(cargo_type)

    return array

def array_to_dict(array):
    """
    Converts python array to dictionary for use in javascript.
    :param array: array of slats or cargos
    :return: grid dictionary
    """
    # Convert numpy array to a list of dictionaries
    dict = {}
    x_dim, y_dim, layer_dim = array.shape
    for x in range(x_dim):
        for y in range(y_dim):
            for layer in range(layer_dim):
                entry = array[x, y, layer]
                if entry != 0:
                    dict[f'{x},{y},{layer}'] = entry
    return dict



# Function to create the acronym
def create_acronym(word):
    vowels = 'aeiouAEIOU'

    # Check if the word contains 'mer-'
    if 'mer-' in word:
        prefix, rest = word.split('mer-', 1)
        if rest.startswith('anti'):
            rest = rest[4:]  # Remove 'anti'
            acronym = prefix + 'a' + ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels])
        else:
            acronym = prefix + ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels])
    elif word.startswith('anti'):
        rest = word[4:]  # Remove 'anti'
        acronym = 'a' + ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels])
    else:
        acronym = ''.join([char for i, char in enumerate(word) if i == 0 or char not in vowels])

    return acronym




def convert_np_to_py(data):
    if isinstance(data, dict):
        return {key: convert_np_to_py(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_np_to_py(element) for element in data]
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        return data



def getDriverNames(plate_mapping_filepath):
    base_directory = os.path.abspath(join(__file__, os.path.pardir, os.path.pardir))

    available_plate_loaders = {}

    for file in os.listdir(plate_mapping_filepath):
        if file == '.DS_Store' or file == '__init__.py' or '.py' not in file:
            continue
        p = ast.parse(open(os.path.join(plate_mapping_filepath, file), 'r').read())
        classes = [node.name for node in ast.walk(p) if isinstance(node, ast.ClassDef)]
        for _class in classes:
            available_plate_loaders[_class] = 'crisscross.plate_mapping.%s.%s' % (file.split('.py')[0], _class)

    return list(available_plate_loaders.keys())





def cargo_to_inventory(cargo_plate_filepath, cargo_plate_folder):
    plate = createGenericPlate(os.path.basename(cargo_plate_filepath) + ".xlsx", cargo_plate_folder )
    plate_cargo_dict = plate.cargo_key

    # Create the list of elements with the specified format
    inventory = []
    hexColors = ['#ff0000', '#9dd1eb', '#ffff00', '#ff69b4', '#008000', '#ffa500'];
    for id_char, name in plate_cargo_dict.items():
        #tag = create_acronym(id_name)
        id_num = int(id_char)
        element = {
            "id": str(id_num) + "-plate:" + os.path.basename(cargo_plate_filepath),
            "name": name,
            "tag": name,
            "color": hexColors[len(inventory)%6],
            "plate": os.path.basename(cargo_plate_filepath)
        }
        inventory.append(element)

    return inventory


def break_array_by_plates(array):
    # Extract the tags from each element (assuming the format is ID-plate:PLATE)
    id_parts = np.vectorize(lambda x: x.split('-plate:')[0])(array)
    int_id_parts = [[int(i) if i else 0 for i in j] for j in id_parts]
    plates = np.vectorize(lambda x: x.split('-plate:')[-1])(array)

    # Get the unique tags
    unique_plates = np.unique(plates)

    # Dictionary to store arrays for each unique tag
    plate_arrays = {plate: np.zeros_like(array, dtype=int) for plate in unique_plates}
    #plate_arrays = dict((plate, np.zeros_like(array, dtype=int)) for plate in unique_plates)

    # Iterate over the array and populate the tag-specific arrays
    for plate in unique_plates:
        plate_arrays[plate] = np.where(plates == plate, int_id_parts, 0)

    return plate_arrays