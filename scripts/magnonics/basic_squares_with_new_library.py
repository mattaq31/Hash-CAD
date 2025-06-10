# This file regenerates the plain square design, but also generates another system using the new handle library as a comparison test
import copy

import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.core_functions.slats import Slat
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping.plate_constants import octahedron_patterning_v1, cargo_plate_folder, plate96_center_pattern
from crisscross.plate_mapping import get_plateclass, get_standard_plates, get_assembly_handle_v2_sample_plates

########################################
# script setup
base_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/magnonics/basic_squares_handle_library_comparison'
graphics_folder = os.path.join(base_folder, 'all_graphics')
temp_folder = os.path.join(base_folder, 'temp_testing_graphics')

echo_folder = os.path.join(base_folder, 'echo_commands')
hamming_folder = os.path.join(base_folder, 'hamming_arrays')
lab_helper_folder = os.path.join(base_folder, 'lab_helper_sheets')
create_dir_if_empty(base_folder, graphics_folder, temp_folder, lab_helper_folder)

np.random.seed(8)
handle_array_file = 'true_mighty_29_square.npy'
optim_rounds = 5

########################################
# crossbar definitions
crossbar_linkages = ['Homer', 'Krusty', 'Lisa', 'Marge', 'Patty', 'Quimby', 'Smithers']

crossbar_key = {**{i + 11: f'{crossbar_linkages[i]}-10mer' for i in range(7)},
                **{i + 4: f'anti{crossbar_linkages[i]}-10mer' for i in range(7)}}
########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate, all_8064_seed_plugs = get_standard_plates()
v2_crisscross_antihandle_y_plates, v2_crisscross_handle_x_plates = get_assembly_handle_v2_sample_plates()

crossbar_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
########################################
# Shape generation and crisscross handle optimisation
slat_array, _ = generate_standard_square_slats(32)
# handle reading/generation
handle_array = np.load(os.path.join(hamming_folder, handle_array_file))
optimized_hamming_results = multirule_precise_hamming(slat_array, handle_array, request_substitute_risk_score=True)

print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (
optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))
########################################
# prepares crossbar attachment pattern (pre-made in the optical computing script)
crossbar_pattern = np.zeros((32, 32))

crossbar_1_start_stop = {}
for index, sel_pos in enumerate(  # crossbar 1
        [[21.0, 2.0], [18.0, 6.0], [15.0, 10.0], [12.0, 14.0], [9.0, 18.0], [6.0, 22.0], [3.0, 26.0]]):
    if index == 0:
        crossbar_1_start_stop[1] = sel_pos[::-1]  # reversed to match np.where system
    if index == 6:
        crossbar_1_start_stop[32] = sel_pos[::-1]
    crossbar_pattern[int(sel_pos[1]), int(sel_pos[0])] = index + 4

crossbar_2_start_stop = {}
for index, sel_pos in enumerate(  # crossbar 2
        [[31.0, 6.0], [28.0, 10.0], [25.0, 14.0], [22.0, 18.0], [19.0, 22.0], [16.0, 26.0], [13.0, 30.0]]):
    if index == 0:
        crossbar_2_start_stop[1] = sel_pos[::-1]
    if index == 6:
        crossbar_2_start_stop[32] = sel_pos[::-1]

    crossbar_pattern[int(sel_pos[1]), int(sel_pos[0])] = index + 4  # incremented by 4 to match with cargo map

# the actual crossbar is defined as a 1x32 array with the attachment staples on the H5 side
single_crossbar_pattern = np.ones((1, 32)) * -1
for index, pos in enumerate([0, 5, 10, 15, 20, 25, 30]):  # as defined by previous script
    single_crossbar_pattern[:, pos] = index + 11

# custom slat for crossbar system
crossbar_slat_1 = Slat('crossbar_slat_1', 0, crossbar_1_start_stop)
crossbar_slat_2 = Slat('crossbar_slat_2', 0, crossbar_2_start_stop)
for i in range(32):
    if single_crossbar_pattern[0, i] != -1:
        cargo_id = crossbar_key[single_crossbar_pattern[0, i]]
        seq = crossbar_plate.get_sequence(i + 1, 5, cargo_id)
        well = crossbar_plate.get_well(i + 1, 5, cargo_id)
        plate = crossbar_plate.get_plate_name(i + 1, 5, cargo_id)
        descriptor = 'Cargo Plate %s, Crossbar Handle %s' % (crossbar_plate.get_plate_name(), cargo_id)
        crossbar_slat_1.set_handle(i + 1, 5, seq, well, plate, descriptor=descriptor)
        crossbar_slat_2.set_handle(i + 1, 5, seq, well, plate, descriptor=descriptor)

########################################
# preparing seed placement
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
corner_seed_array = np.zeros((32, 32))
corner_seed_array[0:16, 0:5] = insertion_seed_array
########################################
# Three total megastructure designs are considered - one for each handle array
design_names = ['standard_array', 'updated_library']

for index, design in enumerate(design_names):
    megastructure = Megastructure(slat_array)
    if design == 'standard_array':
        megastructure.assign_assembly_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
    else:
        megastructure.assign_assembly_handles(handle_array, v2_crisscross_handle_x_plates, v2_crisscross_antihandle_y_plates)

    megastructure.assign_seed_handles(corner_seed_array, combined_seed_plate)
    megastructure.assign_cargo_handles_with_array(crossbar_pattern, crossbar_key, crossbar_plate, layer='bottom')

    megastructure.slats['crossbar_slat_1'] = crossbar_slat_1
    megastructure.slats['crossbar_slat_2'] = crossbar_slat_2

    megastructure.patch_flat_staples(core_plate)

    if index == 0:
        unique_handle_set_layer_1 = set()
        unique_handle_set_layer_2 = set()
        nonspecific_handles = set()

        for slat, slat_data in megastructure.slats.items():
            if 'layer1' in slat:
                for handle_position, handle_data in slat_data.H5_handles.items():
                    if 'Ass.' in handle_data['descriptor']:
                        handle_number = int(handle_data['descriptor'].split(',')[0].split(' ')[-1])
                        unique_handle_set_layer_1.add((handle_position, handle_number))
                        nonspecific_handles.add(handle_number)
            if 'layer2' in slat:
                for handle_position, handle_data in slat_data.H2_handles.items():
                    if 'Ass.' in handle_data['descriptor']:
                        handle_number = int(handle_data['descriptor'].split(',')[0].split(' ')[-1])
                        unique_handle_set_layer_2.add((handle_position, handle_number))

        print(f'Out of 2048 possible handles, {((len(unique_handle_set_layer_1) + len(unique_handle_set_layer_2))/2048)*100:.2f}% will be used for this design.')
        print(f'However, {(len(nonspecific_handles)/32)*100:.2f}% of the unique handle sequences will be used (if ignoring position on slat).')

    colormap = ['#1f77b4', '#ff7f0e', '#ffff00']

    if index == 0:
        #  generates the graphical report for just one design, since both are the same
        megastructure.create_standard_graphical_report(graphics_folder, colormap=colormap)
        megastructure.create_blender_3D_view(graphics_folder, animate_assembly=True, colormap=colormap)
    else:
        megastructure.create_graphical_assembly_handle_view(save_to_folder=graphics_folder,
                                                            colormap=colormap,
                                                            instant_view=False)

    os.rename(os.path.join(graphics_folder, 'handles_layer_1_2.png'),
              os.path.join(graphics_folder, f'assembly_handles_{design}.png'))

    special_vol_plates = {'P3518_MA': int(150 * (500 / 200)),
                          'P3601_MA': int(150 * (500 / 100)),
                          'P3602_MA': int(150 * (500 / 100)),
                          'P3603_MA': int(150 * (500 / 100)),
                          'P3604_MA': int(150 * (500 / 100)),
                          'P3605_MA': int(150 * (500 / 100)),
                          'P3606_MA': int(150 * (500 / 100))}

    specific_plate_wells = copy.copy(plate96_center_pattern)
    specific_plate_wells.extend(['H11', 'H12'])

    specific_plate_wells = [(1, w) for w in specific_plate_wells]

    echo_sheet = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                     destination_plate_name=f'{design}_plate',
                                     default_transfer_volume=150,
                                     output_folder=echo_folder,
                                     unique_transfer_volume_for_plates=special_vol_plates,
                                     manual_plate_well_assignments=specific_plate_wells,
                                     plate_viz_type = 'barcode',
                                     output_filename=f'echo_commands_dbl_crossbar_{design}.csv')

    special_groups = {'Crossbars': ['crossbar_slat_1', 'crossbar_slat_2']}

    prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'{design}_standard_helpers.xlsx'),
                                reference_single_handle_volume=150,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_sheet,
                                peg_groups_per_layer=2,
                                special_slat_groups=special_groups,
                                unique_transfer_volume_plates=special_vol_plates)
