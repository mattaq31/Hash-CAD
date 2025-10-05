import os
import numpy as np

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_assembly_handle_v2_sample_plates

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

src_004, _, src_007, _, _, _ = get_cargo_plates()
########################################
# MEGASTRUCTURE
M1 = Megastructure(import_design_file=os.path.join(design_folder, 'designs/Type1_square_megastructure.xlsx'))
M2 = Megastructure(import_design_file=os.path.join(design_folder, 'designs/Type2_square_megastructure.xlsx'))

M1.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate_p8064, src_007, src_004])
M1.patch_flat_staples(core_plate)

M2.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate_p8064, src_007, src_004])
M2.patch_flat_staples(core_plate)

########################################
# REPORTS
if compute_hamming:
    print('Hamming Distance Report for T1:')
    print(multirule_oneshot_hamming(M1.generate_slat_occupancy_grid(), M1.generate_assembly_handle_grid(),
                                    per_layer_check=True,
                                    report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
    print('--')
    print('Hamming Distance Report for T2:')
    print(multirule_oneshot_hamming(M2.generate_slat_occupancy_grid(), M2.generate_assembly_handle_grid(),
                                    per_layer_check=True,
                                    report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))

if generate_graphical_report:
    M1.create_standard_graphical_report(os.path.join(design_folder, 'visualization_square_type_1/'),
                                        generate_3d_video=True)

    M2.create_standard_graphical_report(os.path.join(design_folder, 'visualization_square_type_2/'),
                                        generate_3d_video=True)

########################################
print('----')
# ECHO
single_handle_volume = 100
if generate_echo:

    # Only layer 2 and 3 slats are 'real', layers 1 and 4 are meant to simulate the interface with the other tile type
    real_slats_M1 = {}
    for key, slat in M1.slats.items():
        if slat.layer == 2 or slat.layer == 3:
            real_slats_M1[key] = slat

    real_slats_M2 = {}
    for key, slat in M2.slats.items():
        if slat.layer == 2 or slat.layer == 3:
            real_slats_M2[key] = slat

    print('Generating echo command sheets for T1:')
    echo_sheet_M1 = convert_slats_into_echo_commands(slat_dict=real_slats_M1,
                                                     destination_plate_name='type1_stairway_plate',
                                                     reference_transfer_volume_nl=single_handle_volume,
                                                     output_folder=echo_folder,
                                                     center_only_well_pattern=True,
                                                     plate_viz_type='barcode',
                                                     output_filename=f'type_1_square_echo_commands.csv')
    print('--')
    print('Generating echo command sheets for T2:')

    echo_sheet_M2 = convert_slats_into_echo_commands(slat_dict=real_slats_M2,
                                                     destination_plate_name='type2_stairway_plate',
                                                     reference_transfer_volume_nl=single_handle_volume,
                                                     output_folder=echo_folder,
                                                     center_only_well_pattern=True,
                                                     plate_viz_type='barcode',
                                                     output_filename=f'type_2_square_echo_commands.csv')
print('----')
########################################
# LAB PROCESSING
if generate_lab_helpers:
    print('Generating helper sheets for T1:')
    prepare_all_standard_sheets(real_slats_M1, os.path.join(lab_helper_folder, f'standard_helpers_type_1_stairway.xlsx'),
                                reference_single_handle_volume=single_handle_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_M1,
                                slat_mixture_volume="max",
                                peg_groups_per_layer=2)
    print('--')
    print('Generating helper sheets for T2:')
    prepare_all_standard_sheets(real_slats_M2, os.path.join(lab_helper_folder, f'standard_helpers_type_2_stairway.xlsx'),
                                reference_single_handle_volume=single_handle_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_M2,
                                slat_mixture_volume="max",
                                peg_groups_per_layer=2)
