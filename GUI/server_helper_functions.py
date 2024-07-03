
import numpy as np
import pandas as pd
import os



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



# Function to create the acronym
def create_acronym(word):
    vowels = 'aeiouAEIOU'
    if word.startswith('anti'):
        rest = word[4:]  # Remove 'anti'
        acronym = 'a' + ''.join([char for i, char in enumerate(rest) if i == 0 or char not in vowels])
    else:
        acronym = ''.join([char for i, char in enumerate(word) if i == 0 or char not in vowels])
    return acronym



def cargo_plate_to_inventory(cargo_plate_filepath):
    #Select the sheet of the cargo plate file storing the cargo names
    sheet_name = 'Names'

    # Load the specified sheet into a DataFrame
    df = pd.read_excel(cargo_plate_filepath, sheet_name=sheet_name, skiprows=1)

    # Step 2: Select the 2nd column (index 1 since indexing starts from 0)
    second_column = df.iloc[:, 1]

    # Step 3: Split each element by '_' and keep the first results in an array
    split_arrays = second_column.dropna().astype(str).apply(lambda x: x.split('_')[:1])

    # Step 4: Find unique arrays and return them as a list
    unique_arrays = split_arrays.drop_duplicates().tolist()

    # Step 5: Create the list of elements with the specified format
    inventory = []
    hexColors = ['#ff0000', '#0000ff', '#ffff00', '#ff69b4', '#008000', '#ffa500'];
    for item in unique_arrays:
        id_name = item[0]
        acronym = create_acronym(id_name)
        element = {
            "id": id_name,
            "name": id_name,
            "acronym": acronym,
            "color": hexColors[len(inventory)%6],
            "plate": os.path.basename(cargo_plate_filepath)
        }
        inventory.append(element)

    return inventory



