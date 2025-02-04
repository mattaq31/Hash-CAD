import os
import numpy as np

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

design_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/FinalCross'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)
experiment_name = 'YXZ001'


core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()

src_004, src_005, src_007, P3518, P3510 = get_cargo_plates()

special_vol_plates = {'sw_src007': int(150 * (500 / 200)), 'sw_src004': int(150 * (500 / 200))}

generate_echo = True
generate_lab_helpers = True
compute_hamming = False
generate_graphical_report = True

M2 = Megastructure(import_design_file=os.path.join(design_folder, 'full_design_finalnewlib.xlsx'))

M2.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate, src_007, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])

M2.patch_control_handles(core_plate)

if generate_graphical_report:
    M2.create_standard_graphical_report(os.path.join(design_folder, 'visualization/'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        generate_3d_video=True,
                                        seed_color=(1.0, 1.0, 0.0))

if generate_echo:
    echo_sheet = convert_slats_into_echo_commands(slat_dict=M2.slats,
                                                  destination_plate_name='biocross_plate',
                                                  unique_transfer_volume_for_plates=special_vol_plates,
                                                  default_transfer_volume=150,
                                                  output_folder=echo_folder,
                                                  center_only_well_pattern=True,
                                                  plate_viz_type='barcode',
                                                  output_filename=f'biocross_echo_base_commands.csv')
if generate_lab_helpers:
    prepare_all_standard_sheets(M2.slats, os.path.join(lab_helper_folder, f'{experiment_name}_standard_helpers.xlsx'),
                                default_staple_volume=150,
                                default_staple_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=4,
                                unique_transfer_volume_plates=special_vol_plates)