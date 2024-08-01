import numpy as np
import os

import os
import zipfile

#For generating handles
from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping import get_plateclass
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_h5_handle_plates,
                                                         crisscross_h2_handle_plates, assembly_handle_folder,
                                                         seed_plug_plate_corner)
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands


# Generates crisscross handle plate dictionaries from provided files
crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                            crisscross_h5_handle_plates[0:3],
                                            assembly_handle_folder, plate_slat_sides=[5, 5, 5])

edge_seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)

core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)



def gen_megastructure(seed_array, slat_array, cargo_dict, handle_array, orientations, graphics, echo, save, plate_folder, output_folder, upload_folder):

    # prepares the actual full megastructure here
    crisscross_megastructure = Megastructure(slat_array,
                                             orientations,
                                             connection_angle='90')

    # Assign slat handles
    crisscross_megastructure.assign_crisscross_handles(handle_array,
                                                       crisscross_handle_x_plates,
                                                       crisscross_antihandle_y_plates)

    #Add seeds
    if (seed_array.size != 0):
        layer_counter = 0
        for layer in range(seed_array.shape[2]):
            if(np.any(seed_array[:,:,layer])):
                crisscross_megastructure.assign_seed_handles(seed_array[:, :, layer], edge_seed_plate, layer_id=layer_counter + 1)

    # Add cargo
    if(cargo_dict):
        cargo_by_plate = break_dict_by_plates(cargo_dict)
        for plate, single_plate_cargo in cargo_by_plate.items():
            if (plate != ''):
                plate = get_plateclass('GenericPlate', plate, plate_folder)
                crisscross_megastructure.assign_cargo_handles_with_dict(single_plate_cargo, plate)

    crisscross_megastructure.patch_control_handles(core_plate)

    crisscross_megastructure.export_design('full_design.xlsx', output_folder)

    if(graphics):
        crisscross_megastructure.create_standard_graphical_report(os.path.join(output_folder, 'Design Graphics'),
                                                                  colormap='Set1', cargo_colormap='Paired')

    if(echo):
        convert_slats_into_echo_commands(crisscross_megastructure.slats, 'crisscross_design_plate',
                                         output_folder,'all_echo_commands_with_crisscross_design.csv',
                                         transfer_volume=100)

    if(save):
        zip_folder_to_disk(output_folder, os.path.join(upload_folder, 'outputs.zip'))

    return crisscross_megastructure



def generate_design_arrays(seed_dict, slat_dict, cargo_dict, handle_dict, handle_rounds = 10, use_old_handles = False, trim=True):
    seed_array = np.array([])
    slat_array = ()
    cargo_dict_formatted = {}
    handle_array = []

    if (seed_dict):
        seed_array = seed_dict_to_array(seed_dict, trim_offset=trim, slat_grid_dict=slat_dict)

    if (slat_dict):
        slat_array = slat_dict_to_array(slat_dict, trim_offset=trim)

    if (cargo_dict):
        cargo_dict_formatted = format_cargo_dict(cargo_dict, trim=trim, reference_slat_dict=slat_dict)

    if ((handle_dict) and (use_old_handles)):
        handle_array = handle_dict_to_array(handle_dict, trim_offset=trim, slat_grid_dict=slat_dict)
    else:
        # Generate handle array
        handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, slat_length=32, max_rounds=handle_rounds,
                                                        split_sequence_handles=False, universal_hamming=True,
                                                        layer_hamming=False,
                                                        group_hamming=None, metric_to_optimize='Universal')

    return seed_array, slat_array, cargo_dict_formatted, handle_array

def generate_formatted_orientations(handle_configs):
    layer_interface_orientation = []
    for orientation in handle_configs.values():
        layer_interface_orientation.append((int(orientation[0]), int(orientation[1])))

    # Now change this layer_interface_orientation array into the proper format: ie [2, (5, 2), (5, 2), 5]
    first_orientation = layer_interface_orientation[0][0]
    last_orientation = layer_interface_orientation[-1][1]
    middle_orientations = [(layer_interface_orientation[i][1], layer_interface_orientation[i + 1][0])
                           for i in range(len(layer_interface_orientation) - 1)]
    formatted_orientations = [first_orientation] + middle_orientations + [last_orientation]

    return formatted_orientations


def seed_dict_to_array(seed_dict, trim_offset=False, slat_grid_dict={}):
    """
    Converts a seed dictionary (produced by javascript) into a seed array.
    :param seed_dict: dictionary of seed by (x,y,layer) coordinates.
    :param trim_offset: If true, will trim unoccupied positions from top/left of array. If false, will leave full array.
    :param slat_grid_dict: If trim_offset is set to true, will trim based upon the shape of the slat dictionary
    :return: array - seed by (x,y,layer) coordinates.
    """

    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in seed_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in seed_dict.keys()) + 1
    min_x = 0
    min_y = 0
    max_layer = max(int(key.split(',')[2]) for key in seed_dict.keys()) + 1

    if (trim_offset == True):
        max_x = max(int(key.split(',')[0]) for key in slat_grid_dict.keys()) + 1
        max_y = max(int(key.split(',')[1]) for key in slat_grid_dict.keys()) + 1
        min_x = min(int(key.split(',')[0]) for key in slat_grid_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in slat_grid_dict.keys())
        max_layer = max(int(key.split(',')[2]) for key in slat_grid_dict.keys()) + 1

    # Initialize the array
    array = np.zeros((max_x - min_x, max_y - min_y, max_layer))

    # Populate the array
    for key, seed_id in seed_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x - min_x, y - min_y, layer - 1] = seed_id

    return array



def slat_dict_to_array(grid_dict, trim_offset=False):
    """
    Converts a slat dictionary (produced by javascript) into a slat array.
    :param grid_dict: dictionary of slat IDs by (x,y,layer) coordinates.
    :param trim_offset: If true, will trim unoccupied positions from top/left of array. If false, will leave full array.
    :return: array - slat IDs by (x,y,layer) coordinates.
    """
    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in grid_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in grid_dict.keys()) + 1
    min_x = 0  # min(int(key.split(',')[0]) for key in grid_dict.keys())
    min_y = 0  # min(int(key.split(',')[1]) for key in grid_dict.keys())
    max_layer = max(int(key.split(',')[2]) for key in grid_dict.keys())

    if (trim_offset == True):
        min_x = min(int(key.split(',')[0]) for key in grid_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in grid_dict.keys())

    # Initialize the array
    array = np.zeros((max_x - min_x, max_y - min_y, max_layer))

    # Populate the array
    for key, slatId in grid_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x - min_x, y - min_y, layer - 1] = slatId

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
                    dict[f'{x},{y},{layer+1}'] = entry
    return dict


# Function to create the acronym
def create_acronym(word):
    vowels = 'aeiouAEIOU'

    # Check if the word contains 'mer-'
    if '-' in word:
        rest, postfix = word.split('-', 1)
        if rest.startswith('anti'):
            rest = rest[4:]  # Remove 'anti'
            acronym = 'a' + ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels]) + "." + postfix[0:2]
        else:
            acronym = ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels]) + "." + postfix[0:2]
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




def cargo_to_inventory(cargo_plate_filepath, cargo_plate_folder):
    plate = get_plateclass('GenericPlate', os.path.basename(cargo_plate_filepath), cargo_plate_folder)

    # Extract unique cargo name values
    unique_cargo_names = list({key[2] for key in plate.sequences.keys()})

    # Create the list of elements with the specified format
    inventory = []
    hexColors = ['#ff0000', '#9dd1eb', '#ffff00', '#ff69b4', '#008000', '#ffa500'];
    for name in unique_cargo_names:
        h2_compatibility_arr = []
        for i in range(1, 33):
            if (i, 2, name) in plate.sequences:
                h2_compatibility_arr.append(i)

        h5_compatibility_arr = []
        for i in range(1, 33):
            if (i, 5, name) in plate.sequences:
                h5_compatibility_arr.append(i)

        element = {
            "id": str(name) + "-plate:" + os.path.basename(cargo_plate_filepath),
            "name": name,
            "tag": create_acronym(name),
            "color": hexColors[len(inventory) % 6],
            "plate": os.path.basename(cargo_plate_filepath),
            "details": [h2_compatibility_arr, h5_compatibility_arr]
        }
        inventory.append(element)

    return inventory



def break_dict_by_plates(dict):
    # Initialize the new dictionary to hold separate dictionaries for each <PLATE>
    separated_dicts = {}

    # Iterate through the original dictionary
    for key, value in dict.items():
        # Extract the <PLATE> value
        plate = value.split('-plate:')[1]

        # Initialize the dictionary for this <PLATE> if it doesn't already exist
        if plate not in separated_dicts:
            separated_dicts[plate] = {}

        # Add the entry to the appropriate dictionary
        separated_dicts[plate][key] = value.split('-plate:')[0]

    return separated_dicts

def format_cargo_dict(cargo_dict, trim = False, reference_slat_dict = {}):
    formatted_dict = {}
    min_x = 0
    min_y = 0

    if(trim):
        min_x = min(int(key.split(',')[0]) for key in reference_slat_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in reference_slat_dict.keys())

    for key, value in cargo_dict.items():
        parts = key.split(',')
        x = int(parts[0]) - min_x
        y = int(parts[1]) - min_y
        layer = int(parts[2])
        orientation = int(parts[3])

        converted_key = ((x, y), layer, orientation)
        formatted_dict[converted_key] = value

    return formatted_dict


def format_handle_dict(handle_dict, trim = False, reference_slat_dict = {}):
    formatted_dict = {}
    min_x = 0
    min_y = 0

    if(trim):
        min_x = min(int(key.split(',')[0]) for key in reference_slat_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in reference_slat_dict.keys())

    for key, value in handle_dict.items():
        parts = key.split(',')
        x = int(parts[0]) - min_x
        y = int(parts[1]) - min_y
        layer = int(parts[2])

        converted_key = (x, y, layer)
        formatted_dict[converted_key] = value

    return formatted_dict



def handle_dict_to_array(handle_dict, trim_offset=False, slat_grid_dict={}):
    """
    Converts a handle dictionary (produced by javascript) into a handle array.
    :param handle_dict: dictionary of handle by (x,y,layer) coordinates.
    :param trim_offset: If true, will trim unoccupied positions from top/left of array. If false, will leave full array.
    :param slat_grid_dict: If trim_offset is set to true, will trim based upon the shape of the slat dictionary
    :return: array - handleIDs by (x,y,layer) coordinates.
    """

    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in handle_dict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in handle_dict.keys()) + 1
    min_x = 0
    min_y = 0
    max_layer = max(int(key.split(',')[2]) for key in handle_dict.keys()) + 1

    if (trim_offset == True):
        max_x = max(int(key.split(',')[0]) for key in slat_grid_dict.keys()) + 1
        max_y = max(int(key.split(',')[1]) for key in slat_grid_dict.keys()) + 1
        min_x = min(int(key.split(',')[0]) for key in slat_grid_dict.keys())
        min_y = min(int(key.split(',')[1]) for key in slat_grid_dict.keys())
        max_layer = max(int(key.split(',')[2]) for key in slat_grid_dict.keys()) - 1

    # Initialize the array
    array = np.zeros((max_x - min_x, max_y - min_y, max_layer))

    # Populate the array
    for key, seed_id in handle_dict.items():
        x, y, layer = map(int, key.split(','))
        array[x - min_x, y - min_y, layer - 1] = seed_id

    return array







def zip_folder_to_disk(folder_path, output_zip_path):
    try:
        # Create a ZipFile object with the output path
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk the directory tree
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    # Create the full path to the file
                    file_path = os.path.join(root, file)
                    # Create a relative path inside the zip
                    arcname = os.path.relpath(file_path, folder_path)
                    # Write the file to the zip
                    zipf.write(file_path, arcname=arcname)
        print(f"ZIP file created successfully: {output_zip_path}")
    except Exception as e:
        print(f"An error occurred: {e}")



def clear_folder_contents(root_folder):
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):
        # Remove files
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            os.remove(file_path)
