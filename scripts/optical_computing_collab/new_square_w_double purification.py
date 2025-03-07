import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.slats import Slat
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions.plate_constants import plate96_center_pattern
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates


########## CONFIG
experiment_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/ColumbiaNewLib'
base_design_import_file = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/ColumbiaNewLib/full_design.xlsx'
echo_folder = os.path.join(experiment_folder, 'echo_commands')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder)
create_dir_if_empty(lab_helper_folder)
regen_graphics = False
export_design = True
generate_echo = True
generate_lab_helpers = True

########## LOADING AND CHECKING DESIGN
megastructure = Megastructure(import_design_file=base_design_import_file)
optimized_hamming_results = multirule_oneshot_hamming(megastructure.slat_array, megastructure.handle_arrays,
                                                      request_substitute_risk_score=True)
print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))
########## PATCHING PLATES
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, _, _, _,all_8064_seed_plugs = get_standard_plates(handle_library_v2=True)
src_004, src_005, src_007, P3518, P3510,_ = get_cargo_plates()

megastructure.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, P3518, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])

megastructure.patch_control_handles(core_plate)

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


    echo_sheet = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                 destination_plate_name='octa_double_purif_plate',
                                 unique_transfer_volume_for_plates= special_vol_plates,
                                 default_transfer_volume=target_volume,
                                 output_folder=echo_folder,
                                 plate_viz_type='barcode',
                                 output_filename=f'new_columbia_pattern_2_step_purif_echo.csv')
if generate_lab_helpers:
    prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'new_columbia_standard_helpers.xlsx'),
                                default_staple_volume=target_volume,
                                default_staple_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=4,
                                unique_transfer_volume_plates=special_vol_plates)

########## OPTIONAL EXPORTS
if regen_graphics:
    megastructure.create_standard_graphical_report(os.path.join(experiment_folder, 'graphics'))
if export_design:
    megastructure.export_design('new_full_design.xlsx', experiment_folder)

