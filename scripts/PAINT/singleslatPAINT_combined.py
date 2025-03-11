import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

core_plate, _, _, _, _, _, _  = get_standard_plates()
src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()
generate_echo = True
generate_lab_helpers = True

design_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/PAINT/both'
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/PAINT/v1_both'

echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
hamming_folder = os.path.join(design_folder, 'hamming_arrays')
create_dir_if_empty(echo_folder, lab_helper_folder, hamming_folder)
experiment_name = 'YXZ002'

slat_array = np.ones((1,32,1))

M1 = Megastructure(slat_array)
M2 = Megastructure(slat_array)

final_cargo_placement = np.zeros((1,32))

final_cargo_placement[0,0] = 1
final_cargo_placement[0,1] = 1
final_cargo_placement[0,3] = 1
final_cargo_placement[0,7] = 1
final_cargo_placement[0,15] = 1
final_cargo_placement[0,31] = 1

M1.assign_cargo_handles_with_array(final_cargo_placement, cargo_key={1: '9ntpaintp1'}, handle_orientation=5, layer=1)
M2.assign_cargo_handles_with_array(final_cargo_placement, cargo_key={1: '10ntpaintp1'}, handle_orientation=5, layer=1)

M1.patch_placeholder_handles([P3628],['Cargo'])
M2.patch_placeholder_handles([P3628],['Cargo'])

M1.patch_control_handles(core_plate)
M2.patch_control_handles(core_plate)

# awkward dictionary combining code...
combined_slats = {'9nt-paint-slat':M1.slats['layer1-slat1'], '10nt-paint-slat':M2.slats['layer1-slat1']}
combined_slats['9nt-paint-slat'].ID = '9nt-paint-slat'
combined_slats['10nt-paint-slat'].ID = '10nt-paint-slat'

if generate_echo:
    target_volume = 200
    echo_sheet = convert_slats_into_echo_commands(slat_dict=combined_slats,
                                                  destination_plate_name='PAINT_plate',
                                                  default_transfer_volume=target_volume,
                                                  output_folder=echo_folder,
                                                  center_only_well_pattern=True,
                                                  plate_viz_type='barcode',
                                                  output_filename=f'sslat10_echo_base_commands.csv')

if generate_lab_helpers:
    prepare_all_standard_sheets(combined_slats, os.path.join(lab_helper_folder, f'{experiment_name}_standard_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=2)
