import os
import numpy as np
import copy

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_plateclass
from plate_mapping import get_cutting_edge_plates, seed_slat_purification_handles
from plate_mapping.plate_constants import simpsons_mixplate_antihandles_maxed, cargo_plate_folder

########################################
# SETUP
main_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/CAPCs/version_2_hexagons'
experiment_name = 'MA024'
echo_folder = os.path.join(main_folder, 'echo_commands')
lab_helper_folder = os.path.join(main_folder, 'lab_helper_sheets')
design_folder = os.path.join(main_folder, 'designs')
graphics_folder = os.path.join(main_folder, 'graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, main_folder, design_folder, graphics_folder)

generate_graphical_report = False
generate_echo = True
generate_lab_helpers = True
regenerate_designs = True
np.random.seed(8)

main_plates = get_cutting_edge_plates(100)
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)
########################################
# DESIGN EDITING
if regenerate_designs:
    M_p = Megastructure(import_design_file=os.path.join(design_folder, 'basic_hexagon.xlsx'))
    M_c = copy.deepcopy(M_p)
    M_r = copy.deepcopy(M_p)

    slat_array = M_p.generate_slat_occupancy_grid()
    cargo_array_peripheral = np.zeros_like(slat_array[...,0])
    cargo_array_center = np.zeros_like(slat_array[...,0])
    cargo_array_random = np.zeros_like(slat_array[...,0])
    bart_total = 6 * 8 * 4 # 48 per patch, 192 total
    edna_total = 6 * 7 * 4 # 42 per patch, 168 total (165 for central patch)

    for (slat_id_start, slat_start_pos) in [(77, 1), (44, 7), (16, 6), (89, 28)]:
        cargo_pos_start = M_p.slats[f'layer2-slat{slat_id_start}'].slat_position_to_coordinate[slat_start_pos]
        for i in range(0, 16, 2):
            # index the range, but skip one in between each index
            cargo_array_peripheral[cargo_pos_start[0] + i, cargo_pos_start[1]: cargo_pos_start[1] + 12] = 1
            if i != 14:
                cargo_array_peripheral[cargo_pos_start[0] + i + 1, cargo_pos_start[1]: cargo_pos_start[1] + 12] = 2

    center_pos_start = M_p.slats[f'layer2-slat{29}'].slat_position_to_coordinate[31]
    for i in range(0, 32, 2):
        cargo_array_center[center_pos_start[0] + i, center_pos_start[1]: center_pos_start[1] + 24] = 1
        if i < 30:
            cargo_array_center[center_pos_start[0] + i + 1, center_pos_start[1]: center_pos_start[1] + 23] = 2

    cargo_array_peripheral[slat_array[...,1] == 0] = 0
    cargo_array_center[slat_array[...,1] == 0] = 0

    random_positions = np.argwhere(slat_array[...,1] > 0)
    np.random.shuffle(random_positions)
    for pos in random_positions[:bart_total]:
        cargo_array_random[pos[0], pos[1]] = 1
    for pos in random_positions[bart_total: bart_total + edna_total]:
        cargo_array_random[pos[0], pos[1]] = 2

    print('Peripheral patch antigens: %s, %s' % (np.sum(cargo_array_peripheral == 1), np.sum(cargo_array_peripheral == 2)))
    print('Central patch antigens: %s, %s' % (np.sum(cargo_array_center == 1), np.sum(cargo_array_center == 2)))
    print('Random antigen placement: %s, %s' % (np.sum(cargo_array_random == 1), np.sum(cargo_array_random == 2)))

    M_p.assign_cargo_handles_with_array(cargo_array_peripheral, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')
    M_c.assign_cargo_handles_with_array(cargo_array_center, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')
    M_r.assign_cargo_handles_with_array(cargo_array_random, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')

    M_p.export_design('peripheral_patches.xlsx', design_folder)
    M_c.export_design('central_patch.xlsx', design_folder)
    M_r.export_design('random_sprinkling.xlsx', design_folder)
########################################
# MEGASTRUCTURE SETUP AND EXPORT
target_designs = ['peripheral_patches', 'central_patch', 'random_sprinkling']
for design in target_designs:
    print('====================')
    print(f'Constructing design: {design}')
    capc = Megastructure(import_design_file=os.path.join(design_folder, f'{design}.xlsx'))
    hamming_results = multirule_oneshot_hamming(capc.generate_slat_occupancy_grid(), capc.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    # ECHO EXPORT
    capc.patch_placeholder_handles(main_plates + (src_010, src_004))
    capc.patch_flat_staples(main_plates[0])

    target_volume = 75 # nl per staple

    # select only slats in layer 2
    selected_slats = {}
    for c, s in capc.slats.items():
        if s.layer == 2:
            selected_slats[c] = copy.deepcopy(s)

    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                        destination_plate_name=f'{design}',
                                                        reference_transfer_volume_nl=target_volume,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=False,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes= True,
                                                        output_filename=f'{design}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'{design}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    handle_mix_ratio=15,
                                    slat_mixture_volume=50,
                                    peg_concentration=3,
                                    split_core_staple_pools=True,
                                    peg_groups_per_layer=4)

    if generate_graphical_report:
        capc.create_standard_graphical_report(os.path.join(graphics_folder, design, f'{design}_graphics'),
                                              filename_prepend=f'{design}_', generate_3d_video=True)

        capc.create_blender_3D_view(os.path.join(graphics_folder, design, f'{design}_graphics'), filename_prepend=f'{design}_',
                                             camera_spin=False, correct_slat_entrance_direction=True, include_bottom_light=False)

# final commands only for the bottom layer (placed separately since we want more of it)
print('====================')
print(f'Preparing bottom slats:')
# select only slats in layer 1
selected_slats = {}
for c, s in capc.slats.items():
    if s.layer == 1:
        selected_slats[c] = copy.deepcopy(s)

target_volume = 120 # nl per staple

if generate_echo:
    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                    destination_plate_name=f'capc_bottom',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=False,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename=f'capc_bottom_echo_commands.csv')

if generate_lab_helpers:
    prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'capc_bottom_experiment_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_1,
                                handle_mix_ratio=15,
                                slat_mixture_volume=(target_volume/75)* 50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=4)
