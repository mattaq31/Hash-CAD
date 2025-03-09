import os

import numpy as np

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping.plate_constants import seed_plug_plate_center_8064, core_plate_folder
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_plateclass, get_assembly_handle_v2_sample_plates
from scripts.antigen_presenting_cells.capc_pattern_generator import capc_pattern_generator

design_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/FinalCross'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)
experiment_name = 'YXZ001'

core_plate, _, _, _, _, _ = (get_standard_plates(handle_library_v2=True))
crisscross_antihandle_y_plates, crisscross_handle_x_plates = get_assembly_handle_v2_sample_plates()

p8064_seed_plate = get_plateclass('CombinedSeedPlugPlate', seed_plug_plate_center_8064, core_plate_folder)

src_004, _, src_007, _, _ = get_cargo_plates()

generate_echo = True
generate_lab_helpers = True
compute_hamming = True
generate_graphical_report = True

M2 = Megastructure(import_design_file=os.path.join(design_folder, 'full_design_final_with_optimized_hamming.xlsx'))

M2.slats[f'layer1-slat128'].reverse_direction()
M2.slats[f'layer1-slat126'].reverse_direction()
M2.slats[f'layer1-slat124'].reverse_direction()
M2.slats[f'layer1-slat122'].reverse_direction()
M2.slats[f'layer1-slat120'].reverse_direction()
M2.slats[f'layer1-slat118'].reverse_direction()
M2.slats[f'layer1-slat116'].reverse_direction()

final_cargo_placement = np.zeros_like(M2.handle_arrays).squeeze()
final_cargo_placement[47, 0] = 1
final_cargo_placement[45, 0] = 1
final_cargo_placement[43, 0] = 1
final_cargo_placement[41, 0] = 1
final_cargo_placement[39, 0] = 1
final_cargo_placement[37, 0] = 1
final_cargo_placement[35, 0] = 1

cargo_array_pd = capc_pattern_generator('peripheral_dispersed', total_cd3_antigens=192, capc_length=66)
M2.assign_cargo_handles_with_array(cargo_array_pd, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')
M2.assign_cargo_handles_with_array(final_cargo_placement, cargo_key={1: 'SSW041DoublePurification5primetoehold'}, layer='bottom')

M2.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, p8064_seed_plate, src_007, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])

M2.patch_control_handles(core_plate)

if compute_hamming:
    print('Hamming Distance Report:')
    print(multirule_oneshot_hamming(M2.slat_array, M2.handle_arrays,
                                    per_layer_check=True,
                                    report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))

if generate_graphical_report:
    M2.create_standard_graphical_report(os.path.join(design_folder, 'visualization/'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        generate_3d_video=True,
                                        seed_color=(1.0, 1.0, 0.0))

if generate_echo:
    target_volume = 100
    special_vol_plates = {'sw_src007': int(target_volume * (500 / 200)),
                          'sw_src004': int(target_volume * (500 / 200)),
                          'P3621_SSW': int(target_volume * (500 / 200)),
                          'P3518_MA': int(target_volume * (500 / 200)),
                          'P3601_MA': int(target_volume * (500 / 100)),
                          'P3602_MA': int(target_volume * (500 / 100)),
                          'P3603_MA': int(target_volume * (500 / 100)),
                          'P3604_MA': int(target_volume * (500 / 100)),
                          'P3605_MA': int(target_volume * (500 / 100)),
                          'P3606_MA': int(target_volume * (500 / 100))}

    echo_sheet = convert_slats_into_echo_commands(slat_dict=M2.slats,
                                                  destination_plate_name='biocross_plate',
                                                  unique_transfer_volume_for_plates=special_vol_plates,
                                                  default_transfer_volume=target_volume,
                                                  output_folder=echo_folder,
                                                  center_only_well_pattern=True,
                                                  plate_viz_type='barcode',
                                                  output_filename=f'biocross_echo_base_commands.csv')

if generate_lab_helpers:
    prepare_all_standard_sheets(M2.slats, os.path.join(lab_helper_folder, f'{experiment_name}_standard_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=4,
                                unique_transfer_volume_plates=special_vol_plates)
