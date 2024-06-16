import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.core_functions.slat_design import (generate_standard_square_slats, generate_handle_set_and_optimize,
                                                   attach_cargo_handles_to_core_sequences, calculate_slat_hamming)
from crisscross.core_functions.slats import Slat
from crisscross.graphics.megastructures import generate_patterned_square_cco, two_side_plot
from crisscross.helper_functions.standard_sequences import simpsons_anti, simpsons
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, assembly_handle_folder,
                                                         crisscross_h5_handle_plates,
                                                         seed_plug_plate_corner, seed_plug_plate_center,
                                                         octahedron_patterning_v1, cargo_plate_folder,
                                                         nelson_quimby_antihandles, h2_biotin_direct)
from crisscross.plate_mapping import get_plateclass

# This design is for testing the assembly yield of solution assembly vs bead-based assembly.
# We will be preparing two types of squares - one with GNPs and one without.  Both will be prepared separately, then combined in one mixture and sent for TEM.
# Since only one design will have GNPs, we should be able to distinguish between the two designs easily by eye, and thus compare yield.

########################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/lab_portfolio/experiments/MA006'

np.random.seed(8)
read_handles_from_file = True
read_cargo_patterns_from_file = True
########################################

########################################
# cargo definitions
cargo_1 = 'Bart'
cargo_2 = 'Edna'
cargo_biotin = 'Nelson'
crossbar_linkages = ['Homer', 'Krusty', 'Lisa', 'Marge', 'Patty', 'Quimby', 'Smithers']

# mapping sequences to numbers
crossbar_anti_map = {i + 4: simpsons_anti[crossbar_linkages[i]][:10] for i in range(7)}
crossbar_map = {i + 11: simpsons[crossbar_linkages[i]][-10:] for i in
                range(7)}  # due to reverse complement system, need to take sequence from back
cargo_map = {1: simpsons_anti[cargo_1], 2: simpsons_anti[cargo_2], 3: simpsons_anti[cargo_biotin]}

# mapping names to numbers
crossbar_anti_names = {i + 4: f'10mer-anti{crossbar_linkages[i]}' for i in range(7)}
crossbar_names = {i + 11: f'10mer-{crossbar_linkages[i]}' for i in range(7)}
cargo_names = {1: f'anti{cargo_1}', 2: f'anti{cargo_2}', 3: f'anti{cargo_biotin}'}
cargo_names = {**cargo_names, **crossbar_anti_names, **crossbar_names}
########################################

########################################
# Plate sequences
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
crisscross_y_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[3:], assembly_handle_folder,
                                     plate_slat_sides=[5, 5, 5])
crisscross_x_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[0:3], assembly_handle_folder,
                                     plate_slat_sides=[5, 5, 5])
seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)
center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, core_plate_folder)
cargo_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1, cargo_plate_folder)
nelson_plate = get_plateclass('AntiNelsonQuimbyPlate', nelson_quimby_antihandles, cargo_plate_folder)
########################################

########################################
# Shape generation and crisscross handle optimisation
slat_array, unique_slats_per_layer = generate_standard_square_slats(32)
# optimize handles
if read_handles_from_file:
    handle_array = np.loadtxt(os.path.join(output_folder, 'stella_handle_array.csv'), delimiter=',').astype(
        np.float32)
    handle_array = handle_array[..., np.newaxis]
    _, _, res = calculate_slat_hamming(slat_array, handle_array, unique_slats_per_layer, unique_sequences=32)
    print('Hamming distance from file-loaded design: %s' % np.min(res))
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, min_hamming=29, max_rounds=2)
########################################
# 2,3, 8, 9, 14, 15, 20, 21, 26, 27
########################################
# prepares cargo pattern
cargo_pattern = np.zeros((32, 32))

for i in range(16):
    cargo_pattern[i, 7:9] = 1
    cargo_pattern[i, 13:15] = 1
########################################

########################################
# preparing seed placements
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

corner_seed_array = np.zeros((32, 32))
corner_seed_array[0:16, 0:5] = insertion_seed_array

center_seed_array = np.zeros((32, 32))
center_seed_array[8:24, 13:18] = insertion_seed_array

########################################
# Preparing first design - no cargo on top, barts on the bottom
megastructure = Megastructure(slat_array)
megastructure.assign_crisscross_handles(handle_array, crisscross_x_plates, crisscross_y_plates)
megastructure.assign_seed_handles(corner_seed_array, seed_plate)
megastructure.assign_cargo_handles(cargo_pattern, cargo_plate, layer='bottom')
megastructure.patch_control_handles(core_plate)

convert_slats_into_echo_commands(megastructure.slats, 'gnp_replacement_plate',
                                 output_folder, 'all_echo_commands_bart_handles.csv')
nucx_slats = {}

for key, slat in megastructure.slats.items():
    if 'layer1' in key and int(key.split('slat')[-1]) < 17:
        nucx_slats[key] = slat

convert_slats_into_echo_commands(nucx_slats, 'gnp_replacement_plate',
                                 output_folder, 'nucx_only_echo_commands_bart_handles.csv',
                                 specific_plate_wells=['A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
                                                       'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10'])

########################################
# Preparing second design - no cargo on top, nelsons on the bottom

# prepares cargo pattern
cargo_pattern = np.zeros((32, 32))

for i in range(16):
    cargo_pattern[i, 7:9] = 3
    cargo_pattern[i, 13:15] = 3

megastructure_nelson = Megastructure(slat_array)
megastructure_nelson.assign_crisscross_handles(handle_array, crisscross_x_plates, crisscross_y_plates)
megastructure_nelson.assign_seed_handles(corner_seed_array, seed_plate)
megastructure_nelson.assign_cargo_handles(cargo_pattern, nelson_plate, layer='bottom')
megastructure_nelson.patch_control_handles(core_plate)

convert_slats_into_echo_commands(megastructure_nelson.slats, 'gnp_replacement_plate',
                                 output_folder, 'all_echo_commands_nelson_handles.csv')
nucx_slats_nelson = {}
for key, slat in megastructure_nelson.slats.items():
    if 'layer1' in key and int(key.split('slat')[-1]) < 17:
        nucx_slats_nelson[key] = slat

convert_slats_into_echo_commands(nucx_slats_nelson, 'gnp_replacement_plate',
                                 output_folder, 'nucx_only_echo_commands_nelson_handles.csv',
                                 specific_plate_wells=['A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
                                                       'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10'])

combined_slats = {}

for key, val in nucx_slats.items():
    val.ID = 'bart_gnp_MA006_' + val.ID
    combined_slats['bart_gnp_MA006_' + key] = val

for key, val in nucx_slats_nelson.items():
    val.ID = 'nelson_no_gnp_MA006_' + val.ID
    combined_slats['nelson_no_gnp_MA006_' + key] = val

# combined protocol for both designs
convert_slats_into_echo_commands(combined_slats, 'gnp_replacement_plate',
                                 output_folder, 'nucx_only_echo_commands_both_designs.csv',
                                 specific_plate_wells=['A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
                                                       'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10',
                                                       'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
                                                       'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10'])
