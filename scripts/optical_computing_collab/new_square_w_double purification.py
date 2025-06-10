import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_assembly_handle_v2_sample_plates


########## CONFIG
# update these depending on user
experiment_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/ColumbiaNewLib'
base_design_import_file = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/ColumbiaNewLib/full_design.xlsx'
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_mar_2025'
base_design_import_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_mar_2025/full_design.xlsx'

echo_folder = os.path.join(experiment_folder, 'echo_commands')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder)
create_dir_if_empty(lab_helper_folder)
regen_graphics = False
generate_echo = True
generate_lab_helpers = True

########## LOADING AND CHECKING DESIGN
megastructure = Megastructure(import_design_file=base_design_import_file)
optimized_hamming_results = multirule_oneshot_hamming(megastructure.slat_array, megastructure.handle_arrays,
                                                      request_substitute_risk_score=True)
print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))
########## PATCHING PLATES
core_plate, _, _, _, _, _, all_8064_seed_plugs = get_standard_plates(handle_library_v2=True)
crisscross_antihandle_y_plates, crisscross_handle_x_plates = get_assembly_handle_v2_sample_plates()

src_004, src_005, src_007, P3518, P3510,_ = get_cargo_plates()

megastructure.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, P3518, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])

megastructure.patch_flat_staples(core_plate)

target_volume = 100 # nl per staple
if generate_echo:
    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                 destination_plate_name='octa_double_purif_plate_1',
                                 default_transfer_volume=target_volume,
                                 output_folder=echo_folder,
                                 center_only_well_pattern=True,
                                 plate_viz_type='barcode',
                                 output_filename=f'new_columbia_pattern_2_step_purif_echo_plate_1.csv')

    echo_sheet_2 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                 destination_plate_name='octa_double_purif_plate_2',
                                 default_transfer_volume=target_volume,
                                 output_folder=echo_folder,
                                 center_only_well_pattern=True,
                                 plate_viz_type='barcode',
                                 output_filename=f'new_columbia_pattern_2_step_purif_echo_plate_2.csv')
if generate_lab_helpers:
    prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'new_columbia_standard_helpers_plate_1.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_1,
                                slat_mixture_volume="max",
                                peg_groups_per_layer=2)

    prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'new_columbia_standard_helpers_plate_2.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_2,
                                slat_mixture_volume="max",
                                peg_groups_per_layer=2)

########## OPTIONAL EXPORTS
if regen_graphics:
    megastructure.create_standard_graphical_report(os.path.join(experiment_folder, 'graphics'))
