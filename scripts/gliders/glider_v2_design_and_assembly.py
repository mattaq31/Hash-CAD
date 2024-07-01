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
                                                         seed_plug_plate_center, cargo_plate_folder, simpsons_mixplate_antihandles,
                                                         nelson_quimby_antihandles, seed_plug_plate_corner)
############### DESIGN PREPARATION ###############
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/gliders/design_v2'
design_file = 'layer_arrays.xlsx'
read_handles_from_file = True  # if true, skips hamming distance optimization
skip_redesign = True  # if true, skips the regeneration of the slat layers
same_layer_hamming_only = True  # if true, will only optimize hamming distance between adjacent layers rather than universally
np.random.seed(8)

if not skip_redesign:
    # GRID PREPARATION
    xtot = 96  # grid lines
    ytot = 66
    slat_nodes = 32  # there are 32 positions for one slat
    slat_length = 31  # length of slat is actually nodes - 1 (gaps between nodes)
    chevron_standard_slat_count = 32  # number of slats in a typical chevron segment

    pattern = np.zeros((xtot, ytot))  # just a grid to display when plotting
    slat_positions = np.zeros((xtot, ytot, 4))  # 4 channels for 4 layers

    for i in range(0, xtot, 2):  # generates the zig-zag pattern for the grid
        for j in range(0, ytot):
            if j % 2 == 0:
                pattern[i, j] = 1
            else:
                pattern[i + 1, j] = 1

    slat_id = 1  # slat id counter

    #### LAYER 0 [bottom + seed]
    for i in range(5):
        # set y position to 26 for previous design (and x position to 32)
        for j in range(16):
            slat_positions[70 + (2 * i) + j, int((chevron_standard_slat_count/2) - j), 0] = -1

    # first core slats holding the two sides of the glider together
    for i in range(int(chevron_standard_slat_count/2)):
        for j in range(chevron_standard_slat_count):
            slat_positions[(int(chevron_standard_slat_count/2)) + (2 * i) + j, int(chevron_standard_slat_count*(3/2)) - j, 0] = slat_id
        slat_id += 1

    # additional set of slats to rigidify the nose of the glider
    for i in range(int(chevron_standard_slat_count/2)-1):
        for j in range(chevron_standard_slat_count):
            slat_positions[1 + i + j, 33 + i - j, 0] = slat_id
        slat_id += 1

    #### LAYER 1 ####
    for i in range(chevron_standard_slat_count):
        slat_positions[i:(slat_nodes*2)+i, chevron_standard_slat_count - i, 1] = slat_id
        slat_id += 1

    for i in range(chevron_standard_slat_count):
        for j in range(chevron_standard_slat_count):
            slat_positions[2*i + 1 + j, chevron_standard_slat_count + 1 + j, 1] = slat_id
        slat_id += 1

    #### LAYER 2 ####
    for i in range(chevron_standard_slat_count):
        for j in range(chevron_standard_slat_count):
            slat_positions[2 * i + j, chevron_standard_slat_count - j, 2] = slat_id
        slat_id += 1

    for i in range(chevron_standard_slat_count):
        slat_positions[i+1:(slat_nodes*2) + 1 + i, chevron_standard_slat_count + 1 + i, 2] = slat_id
        slat_id += 1

    #### LAYER 3 ####

    # core slats that bind the two wings of the glider together
    for i in range(int(chevron_standard_slat_count/2)+1):  # 17 total: 1 extra to complete full side
        for j in range(chevron_standard_slat_count):
            slat_positions[int(chevron_standard_slat_count/2) - 1 + (2 * i) + j, int(chevron_standard_slat_count/2) + 1 + j, 3] = slat_id
        slat_id += 1

    # additional set of slats to rigidify the nose of the glider
    for i in range(int(chevron_standard_slat_count/2)-1):
        for j in range(chevron_standard_slat_count):
            slat_positions[i + j, 32 - i + j, 3] = slat_id
        slat_id += 1

    # ensures the zig-zag pattern is enforced (just in case)
    slat_positions[..., 0] = slat_positions[..., 0] * pattern
    slat_positions[..., 1] = slat_positions[..., 1] * pattern
    slat_positions[..., 2] = slat_positions[..., 2] * pattern
    slat_positions[..., 3] = slat_positions[..., 3] * pattern

    # Inner layer vis and slat export
    writer = pd.ExcelWriter(os.path.join(output_folder, design_file), engine='xlsxwriter')
    for i in range(4):
        # Convert numpy array to pandas DataFrame
        df = pd.DataFrame(slat_positions[..., i])
        # Write each DataFrame to a separate worksheet
        df.to_excel(writer, sheet_name='Layer_%s' % i, index=False, header=False)
    writer.close()
    print(Fore.GREEN + 'New slat design created successfully and saved to file.')
else:
    print(Fore.GREEN + 'Slat design read from file.')

############### MEGASTRUCTURE CREATION ###############
# reads in and formats slat design into a 3D array
design_df = pd.read_excel(os.path.join(output_folder, design_file), sheet_name=None, header=None)
slat_array = np.zeros((design_df['Layer_0'].shape[0], design_df['Layer_0'].shape[1], len(design_df)))
for i, key in enumerate(design_df.keys()):
    slat_array[..., i] = design_df[key].values

slat_array[slat_array == -1] = 0  # removes the seed values, will re-add them later

# Generates/reads handle array
if read_handles_from_file:  # this is to re-load a pre-computed handle array and save time later
    handle_array = np.zeros((slat_array.shape[0], slat_array.shape[1], slat_array.shape[2]-1))
    for i in range(slat_array.shape[-1]-1):
        handle_array[..., i] = np.loadtxt(os.path.join(output_folder, 'optimized_handle_array_layer_%s.csv' % (i+1)), delimiter=',').astype(np.float32)

    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    _, _, res = calculate_slat_hamming(slat_array, handle_array, unique_slats_per_layer, unique_sequences=32,
                                       same_layer_hamming_only=same_layer_hamming_only)
    print('Hamming distance from file-loaded design: %s' % np.min(res))
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, min_hamming=29, max_rounds=400,
                                                    same_layer_hamming_only=same_layer_hamming_only)
    for i in range(handle_array.shape[-1]):
        np.savetxt(os.path.join(output_folder, 'optimized_handle_array_layer_%s.csv' % (i+1)),
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
nelson_plate = get_plateclass('AntiNelsonQuimbyPlate', nelson_quimby_antihandles, cargo_plate_folder)
simpsons_plate = get_plateclass('SimpsonsMixPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
edge_seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)

# Prepares the seed array, assuming the first position will start from the far right of the layer
seed_array = np.copy(design_df['Layer_0'].values)
seed_array[seed_array > 0] = 0
far_right_seed_pos = np.where(seed_array == -1)[1].max()
for i in range(16):
    column = far_right_seed_pos - i
    filler = (seed_array[:, column] == -1) * (i + 1)
    seed_array[:, column] = filler

# prepares the fluorescent attachment cargo
cargo_file_0 = 'cargo_array_layer_0.xlsx'
cargo_array_0 = pd.read_excel(os.path.join(output_folder, cargo_file_0), sheet_name=None, header=None)['Layer_2_cargo'].values

cargo_file_1 = 'cargo_array_layer_1.xlsx'
cargo_array_1 = pd.read_excel(os.path.join(output_folder, cargo_file_1), sheet_name=None, header=None)['Layer_2_cargo'].values


# prepares the actual full megastructure here
nelson_mega = Megastructure(slat_array, None, connection_angle='60')

for rev_slat in range(48, 64):  # this intervention is being done to accommodate the seed plate handles we have available
    nelson_mega.slats[f'layer2-slat{rev_slat}'].reverse_direction()

nelson_mega.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
nelson_mega.assign_seed_handles(seed_array, edge_seed_plate, layer_id=2)
nelson_mega.assign_cargo_handles(cargo_array_0, nelson_plate, layer=1, requested_handle_orientation=2)
nelson_mega.assign_cargo_handles(cargo_array_1, nelson_plate, layer=2, requested_handle_orientation=2)
nelson_mega.patch_control_handles(core_plate)
# nelson_mega.create_standard_graphical_report(os.path.join(output_folder, 'Design Graphics'), colormap='Set1',
#                                              cargo_colormap='Paired')
print(Fore.GREEN + 'Design exported to Echo commands successfully.')

convert_slats_into_echo_commands(nelson_mega.slats, 'glider_plate', output_folder,
                                 'all_echo_commands.csv', transfer_volume=100)

# prepares the actual full megastructure here
nelson_mega_2 = Megastructure(slat_array, None, connection_angle='60')

for rev_slat in range(48, 64):  # this intervention is being done to accommodate the seed plate handles we have available
    nelson_mega_2.slats[f'layer2-slat{rev_slat}'].reverse_direction()

nelson_mega_2.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
nelson_mega_2.assign_seed_handles(seed_array, edge_seed_plate, layer_id=2)
nelson_mega_2.assign_cargo_handles(cargo_array_0, simpsons_plate, layer=1, requested_handle_orientation=2)
nelson_mega_2.assign_cargo_handles(cargo_array_1, simpsons_plate, layer=2, requested_handle_orientation=2)
nelson_mega_2.patch_control_handles(core_plate)
# nelson_mega.create_standard_graphical_report(os.path.join(output_folder, 'Design Graphics'), colormap='Set1',
#                                              cargo_colormap='Paired')
print(Fore.GREEN + 'Design exported to Echo commands successfully.')


convert_slats_into_echo_commands(nelson_mega_2.slats, 'glider_plate', output_folder,
                                 'all_echo_commands_with_src007.csv', transfer_volume=100)

print(Fore.GREEN + 'Alternative plate mapping design exported to Echo commands successfully.')

