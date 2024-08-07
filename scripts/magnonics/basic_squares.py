# Our collaborators only need undecororated megastructures to start off (they will be coating them with their magnetic material)
# This file simply generates the requested plain squares, of which one also has a crossbar support.
import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize, multi_rule_hamming
from crisscross.core_functions.slats import Slat
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import octahedron_patterning_v1, cargo_plate_folder, plate96
from crisscross.plate_mapping import get_plateclass, get_standard_plates

########################################
# script setup
base_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/magnonics/basic_squares'
graphics_folder = os.path.join(base_folder, 'all_graphics')
temp_folder = os.path.join(base_folder, 'temp_testing_graphics')

echo_folder = os.path.join(base_folder, 'echo_commands')
hamming_folder = os.path.join(base_folder, 'hamming_arrays')
create_dir_if_empty(base_folder, graphics_folder, temp_folder)

np.random.seed(8)
read_randomised_handle_from_file = True
handle_array_file = 'randomised_handle_array.npy'
reduced_handle_array_file = '16_handle_hamming_27.npy'
best_array_file = 'true_mighty_29_square.npy'
optim_rounds = 5

########################################
# crossbar definitions
crossbar_linkages = ['Homer', 'Krusty', 'Lisa', 'Marge', 'Patty', 'Quimby', 'Smithers']

crossbar_key = {**{i + 11: f'{crossbar_linkages[i]}-10mer' for i in range(7)},
                **{i + 4: f'anti{crossbar_linkages[i]}-10mer' for i in range(7)}}
########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
crossbar_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
########################################
# Shape generation and crisscross handle optimisation
slat_array, _ = generate_standard_square_slats(32)
# handle reading/generation

reduced_handle_array = np.load(os.path.join(hamming_folder, reduced_handle_array_file))
best_array = np.load(os.path.join(hamming_folder, best_array_file))

optimized_hamming_results = multi_rule_hamming(slat_array, best_array, request_substitute_risk_score=True)
reduced_handle_set_hamming_results = multi_rule_hamming(slat_array, reduced_handle_array, request_substitute_risk_score=True)
print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))
print('Hamming distance from reduced-handle array: %s, Duplication Risk: %s' % (reduced_handle_set_hamming_results['Universal'], reduced_handle_set_hamming_results['Substitute Risk']))

if read_randomised_handle_from_file:
    random_handle_array = np.load(os.path.join(hamming_folder, handle_array_file))
    result = multi_rule_hamming(slat_array, random_handle_array, request_substitute_risk_score=True)
    print('Hamming distance from file-loaded random design: %s, Duplication Risk: %s' % (result['Universal'], result['Substitute Risk']))
else:
    random_handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, split_sequence_handles=True, max_rounds=optim_rounds)
    np.save(os.path.join(hamming_folder, 'randomised_array.npy'), random_handle_array)

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
design_names = ['reduced_handle_array', 'best_array', 'random_handle_array']

for index, h_array in enumerate([reduced_handle_array, best_array, random_handle_array]):
    megastructure = Megastructure(slat_array)
    megastructure.assign_crisscross_handles(h_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
    megastructure.assign_seed_handles(corner_seed_array, seed_plate)
    megastructure.assign_cargo_handles_with_array(crossbar_pattern, crossbar_key, crossbar_plate, layer='bottom')
    megastructure.slats['crossbar_slat_1'] = crossbar_slat_1
    megastructure.slats['crossbar_slat_2'] = crossbar_slat_2
    megastructure.patch_control_handles(core_plate)

    colormap = ['#1f77b4', '#ff7f0e', '#ffff00']
    if index == 0:
        #  generates the graphical report for just one design, since they are all the same
        megastructure.create_standard_graphical_report(graphics_folder, colormap=colormap)
        megastructure.create_blender_3D_view(graphics_folder, animate_assembly=True, colormap=colormap)
    else:
        megastructure.create_graphical_assembly_handle_view(save_to_folder=graphics_folder,
                                                            colormap=colormap,
                                                            instant_view=False)

    os.rename(os.path.join(graphics_folder, 'handles_layer_1_2.png'), os.path.join(graphics_folder, f'assembly_handles_{design_names[index]}.png'))

    specific_plate_wells = plate96[0:32] + plate96[36:36+32] + plate96[72:74]  # different groups are split into different rows for convenience

    convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                     destination_plate_name='magnonics_square_plate',
                                     specific_plate_wells=specific_plate_wells, transfer_volume=75,
                                     output_folder=echo_folder,
                                     unique_transfer_volume_for_plates={'P3518_MA': int(75*(500/200))},
                                     output_filename=f'echo_commands_dbl_crossbar_{design_names[index]}_v2.csv')
