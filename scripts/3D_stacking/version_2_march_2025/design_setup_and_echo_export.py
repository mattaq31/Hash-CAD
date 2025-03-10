import os
import numpy as np

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_assembly_handle_v2_sample_plates
from scripts.antigen_presenting_cells.capc_pattern_generator import capc_pattern_generator

########################################
# SETUP
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking/version_2'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
np.random.seed(8)

core_plate, _, _, _, _, _, combined_seed_plate_p8064 = get_standard_plates()
crisscross_antihandle_y_plates, crisscross_handle_x_plates = get_assembly_handle_v2_sample_plates()

src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()
########################################
# MEGASTRUCTURE
M1 = Megastructure(import_design_file=os.path.join(design_folder, 'designs/Type2_square_megastructure.xlsx'))

M1.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate_p8064, src_007, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])
M1.patch_control_handles(core_plate)

########################################
# ECHO
single_handle_volume = 100
if generate_echo:
    echo_sheet = convert_slats_into_echo_commands(slat_dict=M1.slats,
                                                  destination_plate_name='capc_plate',
                                                  default_transfer_volume=single_handle_volume,
                                                  output_folder=echo_folder,
                                                  center_only_well_pattern=True,
                                                  plate_viz_type='barcode',
                                                  output_filename=f'capc_echo_base_commands.csv')
########################################
# LAB PROCESSING
if generate_lab_helpers:
    prepare_all_standard_sheets(M1.slats, os.path.join(lab_helper_folder, f'standard_helpers.xlsx'),
                                reference_single_handle_volume=single_handle_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=2)
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
