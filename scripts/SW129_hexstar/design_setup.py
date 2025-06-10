import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking/SW129_hexstar'
base_design_import_files = [os.path.join(experiment_folder, f) for f in
                            ['SW129_hexstar_design_32.xlsx', 'SW129_hexstar_design_64.xlsx']]
shorthand_names = ['32_handle_hexstar', '64_handle_hexstar']

echo_folder = os.path.join(experiment_folder, 'echo_commands')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

regen_graphics = False
generate_echo = False
generate_lab_helpers = False

########## LOADING AND CHECKING DESIGN
for file, design_name in zip(base_design_import_files, shorthand_names):
    print('%%%%%%%%%%%%%%%')
    print('ASSESSING DESIGN: %s' % file.split('/')[-1])
    megastructure = Megastructure(import_design_file=file)
    hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(),
                                                request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'],
                                                                              hamming_results['Substitute Risk']))
    ########## PATCHING PLATES
    core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, _, _, _, all_8064_seed_plugs = get_standard_plates(
        handle_library_v2=True)

    src_004, src_005, src_007, P3518, P3510, _ = get_cargo_plates()

    megastructure.patch_placeholder_handles([crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, P3518, src_004])

    megastructure.patch_flat_staples(core_plate)

    target_volume = 150  # nl per staple
    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                                        destination_plate_name=design_name,
                                                        reference_transfer_volume_nl=target_volume,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'{design_name}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(megastructure.slats,
                                    os.path.join(lab_helper_folder, f'{design_name}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    peg_concentration=3,
                                    peg_groups_per_layer=2)

    ########## OPTIONAL EXPORTS
    if regen_graphics:
        megastructure.create_standard_graphical_report(os.path.join(experiment_folder, f'{design_name}_graphics'),
                                                       generate_3d_video=True)
        megastructure.create_blender_3D_view(os.path.join(experiment_folder, f'{design_name}_graphics'),
                                             camera_spin=False, correct_slat_entrance_direction=True,
                                             include_bottom_light=False)
