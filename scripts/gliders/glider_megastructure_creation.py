import pandas as pd
import os
import numpy as np
from colorama import Fore

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_handle_set_and_optimize, calculate_slat_hamming
from crisscross.plate_mapping import get_plateclass

from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_h5_handle_plates,
                                                         crisscross_h2_handle_plates, assembly_handle_folder,
                                                         seed_plug_plate_center, cargo_plate_folder,
                                                         nelson_quimby_antihandles)


design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/gliders/design_v2'
design_file = 'layer_arrays.xlsx'

read_handles_from_file = True

# reads in and formats slat design into a 3D array
design_df = pd.read_excel(os.path.join(design_folder, design_file), sheet_name=None, header=None)
slat_array = np.zeros((design_df['Layer_0'].shape[0], design_df['Layer_0'].shape[1], len(design_df)))
for i, key in enumerate(design_df.keys()):
    slat_array[..., i] = design_df[key].values

slat_array[slat_array == -1] = 0  # removes the seed values, will re-add them later

cargo_array = np.zeros((slat_array.shape[0], slat_array.shape[1]))  # no cargo for this first design

# Generates/reads handle array
if read_handles_from_file:  # this is to re-load a pre-computed handle array and save time later
    handle_array = np.zeros((slat_array.shape[0], slat_array.shape[1], slat_array.shape[2]-1))
    for i in range(slat_array.shape[-1]-1):
        handle_array[..., i] = np.loadtxt(os.path.join(design_folder, 'optimized_handle_array_layer_%s.csv' % (i+1)), delimiter=',').astype(np.float32)

    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    _, _, res = calculate_slat_hamming(slat_array, handle_array, unique_slats_per_layer, unique_sequences=32)
    print('Hamming distance from file-loaded design: %s' % np.min(res))
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, min_hamming=29, max_rounds=400)
    for i in range(handle_array.shape[-1]):
        np.savetxt(os.path.join(design_folder, 'optimized_handle_array_layer_%s.csv' % (i+1)),
                   handle_array[..., i].astype(np.int32), delimiter=',', fmt='%i')

# Generates plate dictionaries from provided files
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                            crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                            assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[0:3],
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5])
center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, core_plate_folder)

# Combines handle and slat array into the megastructure
megastructure = Megastructure(slat_array, None)
megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)

# Prepares the seed array, assuming the first position will start from the far right of the layer
seed_array = np.copy(design_df['Layer_0'].values)
seed_array[seed_array > 0] = 0
far_right_seed_pos = np.where(seed_array == -1)[1].max()
for i in range(16):
    column = far_right_seed_pos - i
    filler = (seed_array[:, column] == -1) * (i + 1)
    seed_array[:, column] = filler

# Assigns seed array to layer 2
megastructure.assign_seed_handles(seed_array, center_seed_plate, layer_id=2)
megastructure.patch_control_handles(core_plate)

# Exports design to echo format csv file for production
# convert_slats_into_echo_commands(megastructure.slats, 'glider_plate', design_folder, 'all_echo_commands.csv')

# For extended fluorescent microscopy testing, we've also included a cargo array for Nelson handles.  This design is build separately below

cargo_file = 'cargo_array_v2.xlsx'
cargo_array = pd.read_excel(os.path.join(design_folder, cargo_file), sheet_name=None, header=None)['Layer_2_cargo'].values
nelson_plate = get_plateclass('AntiNelsonQuimbyPlate', nelson_quimby_antihandles, cargo_plate_folder)

nelson_mega = Megastructure(slat_array, None)
nelson_mega.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
nelson_mega.assign_seed_handles(seed_array, center_seed_plate, layer_id=2)
nelson_mega.assign_cargo_handles(cargo_array, nelson_plate, layer=2, requested_handle_orientation=2)
nelson_mega.patch_control_handles(core_plate)

convert_slats_into_echo_commands(nelson_mega.slats, 'glider_plate', design_folder,
                                 'all_echo_commands_with_nelson_handles.csv', transfer_volume=100)

print(Fore.GREEN + 'Design exported to Echo commands successfully.')
