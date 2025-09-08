# Just need to regenerate non-nucX because 
# want to test two new handles for double purification are here, placed into src004
# nucX in the original H29 square is using edge seed so is compatible
# Y1 and Y2 are the same handle set design

import os
import numpy as np
from itertools import product

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.helper_functions import create_dir_if_empty
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.plate_mapping import get_plateclass, get_standard_plates
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder

########################################
# script setup

#base_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/magnonics/basic_squares'
base_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/double_purification_iteration_2'
graphics_folder = os.path.join(base_folder, 'all_graphics')
temp_folder = os.path.join(base_folder, 'temp_testing_graphics')

echo_folder = os.path.join(base_folder, 'echo_commands')
hamming_folder = os.path.join(base_folder, 'hamming_arrays')
create_dir_if_empty(base_folder, graphics_folder, temp_folder)

best_array_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/magnonics/basic_squares/hamming_arrays/true_mighty_29_square.npy'

########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
double_purification_plate = get_plateclass('HybridPlate', seed_slat_purification_handles, cargo_plate_folder)
########################################
# Shape generation and crisscross handle optimisation
slat_array, _ = generate_standard_square_slats(32)
best_array = np.load(os.path.join(hamming_folder, best_array_file))

########################################
# preparing seed placement
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
corner_seed_array = np.zeros((32, 32))
corner_seed_array[0:16, 0:5] = insertion_seed_array
########################################
# just the one design, the mighty H29 - but! have two versions of the double purification handle
design_names = ["5primetoehold", "3primetoehold"]

# restrict plate to the center e.g. A3-A10
specific_plate_wells = [[(1,x+str(y)) for x,y in product(["A","B"],np.arange(3,10+1))], [(1,x+str(y)) for x,y in product(["C","D"],np.arange(3,10+1))]]

doublepure_key = {1 : "SSW041DoublePurification5primetoehold", 2 : "SSW042DoublePurification3primetoehold"}

fiveprime_handle_pattern = np.zeros((32,32))
for n in np.arange(16,32):
    if n % 2 == 0: # only place on even slats:
        fiveprime_handle_pattern[(n, 31)] = 1
    else: # nothing on odd numbers
        continue

threeprime_handle_pattern = np.zeros((32,32))
for n in np.arange(16,32):
    if n % 2 == 0: # only place on even slats:
        threeprime_handle_pattern[(n, 31)] = 2
    else: # nothing on odd numbers
        continue

doublepure_handle_patterns = [fiveprime_handle_pattern, threeprime_handle_pattern]

non_nucX_slats = ["layer1-slat{}".format(x) for x in np.arange(17,32+1)]
keep_these_slats = {}

for index, design in enumerate(design_names):
    megastructure = Megastructure(slat_array)
    megastructure.assign_assembly_handles(best_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
    megastructure.assign_seed_handles(corner_seed_array, seed_plate)
    megastructure.assign_cargo_handles_with_array(doublepure_handle_patterns[index], doublepure_key, double_purification_plate, layer='bottom') ###
    megastructure.patch_flat_staples(core_plate)

    colormap = ['#1f77b4', '#ff7f0e', '#ffff00']
    megastructure.create_graphical_assembly_handle_view(save_to_folder=graphics_folder, colormap=colormap, instant_view=False)

    # keep only the non-nucX slats
    for slat_name in non_nucX_slats:
        keep_these_slats[slat_name] = megastructure.slats[slat_name]

    #test_wells = [x+str(y) for x,y in product(["A","B","C","D","E","F","G","H"],np.arange(3,10+1))]
    convert_slats_into_echo_commands(slat_dict=keep_these_slats,
                                    destination_plate_name='double_purification_plate',
                                    manual_plate_well_assignments=specific_plate_wells[index], default_transfer_volume=100,
                                    output_folder=echo_folder,
                                    unique_transfer_volume_for_plates={'sw_src004': 250},
                                    output_filename=f'echo_commands_doublepurification_v2_nonnucXonly_' + design +'.csv')


    #convert_slats_into_echo_commands(slat_dict=keep_these_slats,
    #                                destination_plate_name='double_purification_plate',
    #                                manual_plate_well_assignments=specific_plate_wells[index], default_transfer_volume=100,
    #                                output_folder=echo_folder,
    #                                unique_transfer_volume_for_plates={'sw_src004': 250},
    #                                output_filename=f'echo_commands_doublepurification_v2_nonnucXonly_' + design +'.csv')
