import os
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates


########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs'

target_designs = ['hexagon', 'recycling', 'bird']

base_design_import_files = [os.path.join(experiment_folder, f, f'{f}_design.xlsx') for f in target_designs]
regen_graphics = False
generate_echo = True
generate_lab_helpers = True

########## LOADING AND CHECKING DESIGN
for file, design_name in zip(base_design_import_files, target_designs):

    echo_folder = os.path.join(experiment_folder, design_name, 'echo_commands')
    lab_helper_folder = os.path.join(experiment_folder, design_name, 'lab_helper_sheets')
    create_dir_if_empty(echo_folder, lab_helper_folder)
    print('%%%%%%%%%%%%%%%')
    print('ASSESSING DESIGN: %s' % design_name)

    megastructure = Megastructure(import_design_file=file)
    hamming_results = multirule_oneshot_hamming(megastructure.slat_array, megastructure.handle_arrays, request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    ########## PATCHING PLATES
    core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, _, _, _, all_8064_seed_plugs = get_standard_plates(handle_library_v2=True)
    src_004, src_005, src_007, P3518, P3510,_ = get_cargo_plates()

    megastructure.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, P3518, src_004],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])

    megastructure.patch_control_handles(core_plate)

    target_volume = 150 # nl per staple
    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                     destination_plate_name=design_name,
                                     default_transfer_volume=target_volume,
                                     output_folder=echo_folder,
                                     center_only_well_pattern=False,
                                     plate_viz_type='barcode',
                                     output_filename=f'{design_name}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'{design_name}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    peg_groups_per_layer=2 if design_name == 'recycling' else 4)

    ########## OPTIONAL EXPORTS
    if regen_graphics:
        megastructure.create_standard_graphical_report(os.path.join(experiment_folder, design_name, f'{design_name}_graphics'), generate_3d_video=True)
