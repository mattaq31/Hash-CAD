import os
import numpy as np

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates
from scripts.antigen_presenting_cells.capc_pattern_generator import capc_pattern_generator

########################################
# SETUP
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/CAPCs/version_1_peripheral'
experiment_name = 'MA017'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = False
generate_trench_graphics = True
generate_animation = False
generate_echo = False
generate_lab_helpers = False
compute_hamming = False
export_design = False

np.random.seed(8)

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
src_004, src_005, src_007, P3518 = get_cargo_plates()
########################################
# MEGASTRUCTURE
M1 = Megastructure(import_design_file=os.path.join(design_folder, 'evolved_design.xlsx'))
cargo_array_pd = capc_pattern_generator('peripheral_dispersed', total_cd3_antigens=192, capc_length=66)
M1.assign_cargo_handles_with_array(cargo_array_pd, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')

M1.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate, src_007, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])
M1.patch_control_handles(core_plate)

if export_design:
    M1.export_design('final_design.xlsx', design_folder)
########################################
# ECHO
special_vol_plates = {'sw_src007': int(150 * (500 / 200)), 'sw_src004': int(150 * (500 / 200))}

# sw_src007
# sw_src004
# new handle library (6)
# sw_src002
# new seed plate - 3621

if generate_echo:
    echo_sheet = convert_slats_into_echo_commands(slat_dict=M1.slats,
                                                  destination_plate_name='capc_plate',
                                                  unique_transfer_volume_for_plates=special_vol_plates,
                                                  default_transfer_volume=150,
                                                  output_folder=echo_folder,
                                                  center_only_well_pattern=True,
                                                  plate_viz_type='barcode',
                                                  output_filename=f'capc_echo_base_commands.csv')
########################################
# LAB PROCESSING

special_groups = {'Horizontal-Trench': ['layer1-slat119', 'layer1-slat120', 'layer1-slat183', 'layer1-slat184'],
                  'Vertical-Trench': ['layer2-slat59', 'layer2-slat60', 'layer2-slat26', 'layer2-slat27']}

if generate_lab_helpers:
    prepare_all_standard_sheets(M1.slats, os.path.join(lab_helper_folder, f'{experiment_name}_standard_helpers.xlsx'),
                                reference_single_handle_volume=150,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=4,
                                special_slat_groups=special_groups,
                                unique_transfer_volume_plates=special_vol_plates)
########################################
# REPORTS
if compute_hamming:
    print('Hamming Distance Report:')
    print(multirule_oneshot_hamming(M1.slat_array, M1.handle_arrays,
                                    per_layer_check=True,
                                    report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))

if generate_graphical_report:
    M1.create_standard_graphical_report(os.path.join(design_folder, 'visualization/'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        generate_3d_video=True,
                                        seed_color=(1.0, 1.0, 0.0))
########################################
if generate_animation:
    # 3D ANIMATION
    # Preparing animation order for slats
    # have to prepare these manually as the stagger is screwing up with the automatic detection system.
    # The animation direction detector is also being turned off due to this issue.
    # TODO: changing the direction of the slats so that they don't phase through other slats is still required for this kind of design.
    custom_animation_dict = {}

    groups = [['layer1-slat%s' % x for x in range(98, 114)],
              ['layer2-slat%s' % x for x in range(17, 33)],
              ['layer1-slat%s' % x for x in range(130, 156)],
              ['layer2-slat%s' % x for x in range(33, 49)],
              ['layer1-slat%s' % x for x in range(162, 177)],
              ['layer2-slat%s' % x for x in range(82, 98)],
              ['layer1-slat%s' % x for x in range(177, 194)],
              ['layer2-slat%s' % x for x in range(66, 82)],
              ['layer1-slat%s' % x for x in range(146, 162)],
              ['layer2-slat%s' % x for x in range(50, 67)],
              ['layer1-slat%s' % x for x in range(114, 130)],
              ['layer2-slat%s' % x for x in range(1, 17)],
              ]
    for order, group in enumerate(groups):
        for slat in group:
            custom_animation_dict[slat] = order

    M1.create_blender_3D_view(os.path.join(design_folder, 'visualization/'),
                              colormap='Set1',
                              cargo_colormap='Dark2',
                              animate_assembly=True,
                              seed_color=(1.0, 1.0, 0.0),
                              custom_assembly_groups=custom_animation_dict,
                              animation_type='translate',
                              camera_spin=True)

if generate_trench_graphics:
    special_groups = {'Horizontal-Trench': ['layer1-slat119', 'layer1-slat120', 'layer1-slat183', 'layer1-slat184'],
                      'Vertical-Trench': ['layer2-slat59', 'layer2-slat60', 'layer2-slat26', 'layer2-slat27']}
    del M1.slats['layer1-slat119']
    del M1.slats['layer1-slat120']
    del M1.slats['layer1-slat183']
    del M1.slats['layer1-slat184']
    
    del M1.slats['layer2-slat59']
    del M1.slats['layer2-slat60']
    del M1.slats['layer2-slat26']
    del M1.slats['layer2-slat27']

    M1.create_standard_graphical_report(os.path.join(design_folder, 'trench_visualization/'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        generate_3d_video=True,
                                        seed_color=(1.0, 1.0, 0.0))
