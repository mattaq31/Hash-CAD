import os
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cargo_plates, get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import simpsons_mixplate_antihandles_maxed, cargo_plate_folder


########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/PAINT/hexagon_carpet'
design_name = 'carpet_design_old_system.xlsx'
regen_graphics = True
generate_echo = True
generate_lab_helpers = True

########## LOADING AND CHECKING DESIGN
echo_folder = os.path.join(experiment_folder, 'echo_commands')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helper_sheets')
design_folder = os.path.join(experiment_folder, 'designs')
create_dir_if_empty(echo_folder, lab_helper_folder)

print('%%%%%%%%%%%%%%%')
print('ASSESSING DESIGN: %s' % design_name)

megastructure = Megastructure(import_design_file=os.path.join(design_folder, design_name))
hamming_results = multirule_oneshot_hamming(megastructure.slat_array, megastructure.handle_arrays, request_substitute_risk_score=True)
print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

########## PATCHING PLATES
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, all_8064_seed_plugs = get_cutting_edge_plates()
src_004, src_005, src_007, P3518, P3510,_ = get_cargo_plates()
src_010 = get_plateclass('GenericPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

megastructure.patch_placeholder_handles(
[crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_010, P3518, src_004],
['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])

megastructure.patch_flat_staples(core_plate)
target_volume = 100 # nl per staple (500uM)

if generate_echo:
    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                 destination_plate_name=design_name.split('.')[0],
                                 default_transfer_volume=target_volume,
                                 output_folder=echo_folder,
                                 center_only_well_pattern=False,
                                 plate_viz_type='barcode',
                                 output_filename=f'echo_commands.csv')

if generate_lab_helpers:
    prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'experiment_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_1,
                                peg_groups_per_layer=4)

########## OPTIONAL EXPORTS
if regen_graphics:
    megastructure.create_standard_graphical_report(os.path.join(experiment_folder, f'graphics'), generate_3d_video=True)

    megastructure.create_blender_3D_view(os.path.join(experiment_folder, f'graphics'),
                                         camera_spin=False, correct_slat_entrance_direction=True, colormap='Dark2',
                               cargo_colormap='Set1', seed_color=(1, 0, 0),
                               include_bottom_light=False)


