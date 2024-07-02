
import numpy as np
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
        min_x = min(int(key.split(',')[0]) for key in slat_grid_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in slat_grid_dict.keys())

    # Initialize the array
    array = np.zeros((max_x-min_x, max_y-min_y, max_layer))

    # Populate the array
    for key, cargo_type in grid_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x-min_x, y-min_y, layer] = cargo_type

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
