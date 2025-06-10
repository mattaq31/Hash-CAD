import numpy as np

# For generating handles
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.random_hamming_optimizer import generate_handle_set_and_optimize


def extract_min_max_slat_coords(slat_dict):
    """
    Extracts the minimum and maximum x, y, and layer values from a slat dictionary.  This is helpful for trimming
    empty space in user designs.
    :param slat_dict: Slat dictionary from the user design (provided by JS).
    :return: Dictionary containing the minimum and maximum x, y, and layer values.
    """
    max_x = max(int(key.split(',')[0]) for key in slat_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in slat_dict.keys()) + 1
    min_x = min(int(key.split(',')[0]) for key in slat_dict.keys())
    min_y = min(int(key.split(',')[1]) for key in slat_dict.keys())
    max_layer = max(int(key.split(',')[2]) for key in slat_dict.keys())
    return {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y, 'max_layer': max_layer}

def combine_megastructure_arrays(seed_array, slat_array, cargo_dict, handle_array, orientations):
    """
    Given a set of design arrays, combine them all together into a single Megastructure.  Plates  are not considered
    at this point.
    :param seed_array: 3D array containing seed(s) position.  Provide an empty array if no seed has been defined.
    :param slat_array: Base 3D array containing slat positions.
    :param cargo_dict: Dictionary containing the positions and identities of cargo in the design.
    :param handle_array: Array containing the handle IDs corresponding to the slat array.  Provide an array filled with
    zeros if no handles have been defined.
    :param orientations: The handle orientations (2,5) of the design.
    :return: Complete megastructure class.
    """
    crisscross_megastructure = Megastructure(slat_array, orientations, connection_angle='90')

    if np.sum(handle_array) != 0:
        crisscross_megastructure.assign_assembly_handles(handle_array)

    # Add seeds
    if seed_array.size != 0:
        layer_counter = 0
        for layer in range(seed_array.shape[2]):
            if np.any(seed_array[:, :, layer]):
                crisscross_megastructure.assign_seed_handles(seed_array[:, :, layer], layer_id=layer_counter + 1)

    # Add cargo
    if cargo_dict:
        crisscross_megastructure.assign_cargo_handles_with_dict(cargo_dict)

    return crisscross_megastructure


def convert_design_dictionaries_into_arrays(seed_dict=None, slat_dict=None, cargo_dict=None, handle_dict=None,
                                            trim_arrays=True):
    """
    Converts frontend JS dictionaries into arrays for use with the Megastructure class.
    :param seed_dict: TODO: fill in and separate handle definition away from here
    :param slat_dict:
    :param cargo_dict:
    :param handle_dict:
    :param trim_arrays:
    :return:
    """
    seed_array = np.array([])
    slat_array = ()
    cargo_dict_formatted = {}

    if trim_arrays:
        if slat_dict is None:
            raise ValueError("slat_dict must be provided if trim_arrays is set to True.")
        coord_extremities = extract_min_max_slat_coords(slat_dict)
    else:
        coord_extremities = None

    if seed_dict:
        seed_array = positional_dict_to_array(seed_dict, coord_extremities)

    if slat_dict:
        slat_array = positional_dict_to_array(slat_dict, coord_extremities)

    if cargo_dict:
        cargo_dict_formatted = convert_frontend_cargo_dict_to_megastructure_dict(cargo_dict, coord_extremities)

    if handle_dict:
        handle_array = positional_dict_to_array(handle_dict, {**coord_extremities, **{'max_layer': coord_extremities['max_layer'] - 1}})
    else:
        handle_array = np.zeros((slat_array.shape[0], slat_array.shape[1], slat_array.shape[2] - 1))

    return seed_array, slat_array, cargo_dict_formatted, handle_array


def convert_dict_handle_orientations_to_string(handle_configs):
    """
    Converts dict-based handle configurations into the format required by the Megastructure class.
    :param handle_configs: Dictionary of handle configs TODO: add description
    :return: string-formatted handle configs for Megastructure class
    TODO: make converting between systems easier!
    """

    # first extract all the values from the dictionary
    layer_interface_orientation = []
    for orientation in handle_configs.values():
        layer_interface_orientation.append((int(orientation[1]), int(orientation[0])))

    # then change the layer_interface_orientation array into the proper format: ie [2, (5, 2), (5, 2), 5]
    first_orientation = layer_interface_orientation[0][0]
    last_orientation = layer_interface_orientation[-1][1]
    middle_orientations = [(layer_interface_orientation[i][1], layer_interface_orientation[i + 1][0])
                           for i in range(len(layer_interface_orientation) - 1)]
    formatted_orientations = [first_orientation] + middle_orientations + [last_orientation]

    return formatted_orientations


def positional_dict_to_array(position_dict, slat_extremities=None):
    """
    Converts a seed/slat/handle dictionary (produced by javascript) into a standard format array.
    :param position_dict: dictionary of seed/slat/handle ID by (x,y,layer) coordinates.
    :param slat_extremities: dictionary of slat extremities to determine the dimensions of the array (optional).
    :return: array - seed/slat/handle ID by (x,y,layer) coordinates.
    """
    # Parse the keys to determine the dimensions
    if slat_extremities is not None:
        max_x = slat_extremities['max_x']
        max_y = slat_extremities['max_y']
        min_x = slat_extremities['min_x']
        min_y = slat_extremities['min_y']
        max_layer = slat_extremities['max_layer']
    else:
        max_x = max(int(key.split(',')[0]) for key in position_dict.keys()) + 1
        max_y = max(int(key.split(',')[1]) for key in position_dict.keys()) + 1
        min_x = 0
        min_y = 0
        max_layer = max(int(key.split(',')[2]) for key in position_dict.keys())

    # Initialize the array
    array = np.zeros((max_x - min_x, max_y - min_y, max_layer))

    # Populate the array
    for key, object_id in position_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x - min_x, y - min_y, layer - 1] = object_id

    return array


def positional_3d_array_to_dict(array):
    """
    Converts a 3D crisscross object array to dictionary for use in javascript.
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
                if isinstance(entry, (np.integer, np.floating)):
                    entry = int(entry)
                if entry != 0:
                    dict[f'{x},{y},{layer + 1}'] = entry
    return dict


def positional_2d_array_and_layer_to_dict(array, layer):
    """
    Converts a 2D crisscross object array + associated megastructure layer to dictionary for use in javascript.
    :param array: array of slats or cargos
    :return: grid dictionary
    """
    # Convert numpy array to a list of dictionaries
    dict = {}
    x_dim, y_dim = array.shape

    for x in range(x_dim):
        for y in range(y_dim):
            entry = array[x, y]
            if isinstance(entry, (np.integer, np.floating)):
                entry = int(entry)
            if entry != 0:
                dict[f'{x},{y},{layer}'] = entry
    return dict


def convert_frontend_cargo_dict_to_megastructure_dict(cargo_dict, coord_extremities=None):
    """
    Converts a frontend JS cargo dict into a format compatible with the Megastructure class.
    :param cargo_dict: JS cargo dictionary.
    :param coord_extremities: Canvas extremities to help reduce array size (optional).
    :return: Update cargo dictionary that can be fed directly to a Megastructure.
    """
    formatted_dict = {}
    min_x = 0
    min_y = 0

    if coord_extremities is not None:
        min_x = coord_extremities['min_x']
        min_y = coord_extremities['min_y']

    for key, value in cargo_dict.items():
        parts = key.split(',')
        x = int(parts[0]) - min_x
        y = int(parts[1]) - min_y
        layer = int(parts[2])
        orientation = int(parts[3])

        converted_key = ((x, y), layer, orientation)
        formatted_dict[converted_key] = value

    return formatted_dict


def create_cargo_acronym(word):
    """
    Convenience function to help reduce the size of cargo names for display purposes.
    :param word: Cargo name (in-full).
    :return: Shortened version of the cargo name.
    """
    vowels = 'aeiouAEIOU'

    # Check if the word contains 'mer-'
    if '-' in word:
        rest, postfix = word.split('-', 1)
        if rest.startswith('anti'):
            rest = rest[4:]  # Remove 'anti'
            acronym = 'a' + ''.join(
                [char for i, char in enumerate(rest) if i == 0 or char not in vowels]) + "." + postfix[0:2]
        else:
            acronym = ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels]) + "." + postfix[
                                                                                                             0:2]
    elif word.startswith('anti'):
        rest = word[4:]  # Remove 'anti'
        acronym = 'a' + ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels])
    else:
        acronym = ''.join([char for i, char in enumerate(word) if i == 0 or char not in vowels])

    return acronym


def cargo_to_inventory(cargo_plate, plate_filename):
    """
    Converts the standard plate class into a dictionary system compatible with the frontend's plate inventory system.
    :param cargo_plate: The plate class object containing the cargo sequences.
    :param plate_filename: Plate ID or filename.
    :return: Dictionary of attributes for provided plate
    """

    # Extract unique cargo name values
    unique_cargo_names = list({key[2] for key in cargo_plate.sequences.keys()})

    # Create the list of elements with the specified format
    inventory = []
    hexColors = ['#ff0000', '#9dd1eb', '#ffff00', '#ff69b4', '#008000', '#ffa500']
    for name in unique_cargo_names:
        h2_compatibility_arr = []
        for i in range(1, 33):
            if (i, 2, name) in cargo_plate.sequences:
                h2_compatibility_arr.append(i)

        h5_compatibility_arr = []
        for i in range(1, 33):
            if (i, 5, name) in cargo_plate.sequences:
                h5_compatibility_arr.append(i)

        element = {
            "id": str(name),
            "name": name,
            "tag": create_cargo_acronym(name),
            "color": hexColors[len(inventory) % 6],
            "plate": plate_filename,
            "details": [h2_compatibility_arr, h5_compatibility_arr]
        }
        inventory.append(element)

    return inventory
