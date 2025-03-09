import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats, generate_patterned_square_cco
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.core_functions.slats import Slat
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping.plate_constants import octahedron_patterning_v1, cargo_plate_folder, simpsons_mixplate_antihandles
from crisscross.plate_mapping import get_plateclass, get_standard_plates


########################################
# script setup
base_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_aug_2024'
graphics_folder = os.path.join(base_folder, 'all_graphics')
echo_folder = os.path.join(base_folder, 'echo_commands')
hamming_folder = os.path.join(base_folder, 'hamming_arrays')
handle_array_file = 'true_mighty_29_square.npy'
old_handle_array_file = 'old_handle_array_feb_2024.csv'

create_dir_if_empty(base_folder, graphics_folder, hamming_folder, echo_folder)
np.random.seed(8)
regen_graphics = False
########################################
# crossbar definitions
crossbar_linkages = ['Homer', 'Krusty', 'Lisa', 'Marge', 'Patty', 'Quimby', 'Smithers']
crossbar_key = {**{i + 11: f'{crossbar_linkages[i]}-10mer' for i in range(7)},
                **{i + 4: f'anti{crossbar_linkages[i]}-10mer' for i in range(7)}}
# cargo definitions
cargo_1 = 'Bart'
cargo_2 = 'Edna'
cargo_names = {1: f'anti{cargo_1}', 2: f'anti{cargo_2}'}
########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
crossbar_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
src_007_plate = get_plateclass('GenericPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
########################################
# Shape generation and crisscross handle optimisation
slat_array, _ = generate_standard_square_slats(32)
# handle reading/generation
handle_array = np.load(os.path.join(hamming_folder, handle_array_file))
old_handle_array = np.loadtxt(os.path.join(hamming_folder, old_handle_array_file), delimiter=',').astype(np.float32)
old_handle_array = old_handle_array[..., np.newaxis]

optimized_hamming_results = multirule_precise_hamming(slat_array, handle_array, request_substitute_risk_score=True)
print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (
optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))

old_hamming_results = multirule_precise_hamming(slat_array, old_handle_array, request_substitute_risk_score=True)
print('Hamming distance from old array: %s, Duplication Risk: %s' % (
old_hamming_results['Universal'], old_hamming_results['Substitute Risk']))
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

# octahedra pattern
octa_pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
########################################
# preparing seed placement
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
corner_seed_array = np.zeros((32, 32))
corner_seed_array[0:16, 0:5] = insertion_seed_array
########################################
# preparing y-slats only since we already have x slats
megastructure = Megastructure(slat_array)
megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
megastructure.assign_seed_handles(corner_seed_array, seed_plate)
megastructure.assign_cargo_handles_with_array(crossbar_pattern, crossbar_key, crossbar_plate, layer='bottom')
megastructure.assign_cargo_handles_with_array(octa_pattern, cargo_names, src_007_plate, layer='top')
megastructure.slats['crossbar_slat_1'] = crossbar_slat_1
megastructure.slats['crossbar_slat_2'] = crossbar_slat_2

megastructure.patch_control_handles(core_plate)

megastructure.export_design('full_design.xlsx', base_folder)

colormap = ['#1f77b4', '#ff7f0e', '#ffff00']
if regen_graphics:
    megastructure.create_standard_graphical_report(graphics_folder, colormap=colormap)
    megastructure.create_blender_3D_view(graphics_folder, animate_assembly=True, colormap=colormap)

y_slat_dict = {}

for key, slat in megastructure.slats.items():
    if 'layer2' in key:
        y_slat_dict[key] = slat

convert_slats_into_echo_commands(slat_dict=y_slat_dict,
                                 destination_plate_name='new_octa_plate',
                                 center_only_well_pattern=True, default_transfer_volume=150,
                                 output_folder=echo_folder,
                                 unique_transfer_volume_for_plates={'sw_src007': int(150 * (500 / 200))},
                                 output_filename=f'octa_pattern_H29_y_slats_only_echo.csv')
########################################
# preparing x-slats only to use with the remainder slats from the old design
m_old = Megastructure(slat_array)
m_old.assign_crisscross_handles(old_handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
m_old.assign_seed_handles(corner_seed_array, seed_plate)
m_old.assign_cargo_handles_with_array(crossbar_pattern, crossbar_key, crossbar_plate, layer='bottom')
m_old.assign_cargo_handles_with_array(octa_pattern, cargo_names, src_007_plate, layer='top')
m_old.slats['crossbar_slat_1'] = crossbar_slat_1
m_old.slats['crossbar_slat_2'] = crossbar_slat_2
m_old.patch_control_handles(core_plate)

x_slat_dict = {}
for key, slat in m_old.slats.items():
    if 'layer1' in key:
        if int(key.split('-')[-1].split('slat')[-1]) < 17:
            x_slat_dict[key] = slat

convert_slats_into_echo_commands(slat_dict=x_slat_dict,
                                 destination_plate_name='new_octa_plate',
                                 center_only_well_pattern=True, default_transfer_volume=75,
                                 output_folder=echo_folder,
                                 unique_transfer_volume_for_plates={'P3518_MA': int(75 * (500 / 200))},
                                 output_filename=f'old_octa_x1_slats_only_echo.csv')
# combined
convert_slats_into_echo_commands(slat_dict={**x_slat_dict, **y_slat_dict},
                                 destination_plate_name='new_octa_plate',
                                 center_only_well_pattern=True, default_transfer_volume=150,
                                 output_folder=echo_folder,
                                 unique_transfer_volume_for_plates={'P3518_MA': int(75 * (500 / 200)),
                                                                    'sw_src007': int(150 * (500 / 200))},
                                 output_filename=f'combined_new_slats_for_HC.csv')
