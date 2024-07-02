
import numpy as np
def slat_dict_to_array(grid_dict):
    """
    Converts a slat dictionary (produced by javascript) into a slat array.
    :param grid_dict: dictionary of slat IDs by (x,y,layer) coordinates.
    :return: array - slat IDs by (x,y,layer) coordinates.
    """
    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in grid_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in grid_dict.keys()) + 1
    max_layer = max(int(key.split(',')[2]) for key in grid_dict.keys()) + 1

    # Initialize the array
    array = np.zeros((max_x, max_y, max_layer))

    # Populate the array
    for key, slatId in grid_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x, y, layer] = slatId

    return array

def cargo_dict_to_array(grid_dict):
    """
    Converts a cargo dictionary (produced by javascript) into a cargo array.
    :param grid_dict: dictionary of cargo IDs by (x,y,layer) coordinates.
    :return: array - cargo types/IDs by (x,y,layer) coordinates.
    """

    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in grid_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in grid_dict.keys()) + 1
    max_layer = max(int(key.split(',')[2]) for key in grid_dict.keys()) + 1

    # Initialize the array
    array = np.zeros((max_x, max_y, max_layer))

    # Populate the array
    for key, cargo_type in grid_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x, y, layer] = cargo_type

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
