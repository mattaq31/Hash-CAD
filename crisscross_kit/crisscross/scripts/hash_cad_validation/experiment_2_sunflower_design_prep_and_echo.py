import os
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass, \
    crisscross_h5_handle_plates, assembly_handle_plate_folder, crisscross_h2_handle_plates
from crisscross.plate_mapping.plate_constants import simpsons_mixplate_antihandles_maxed, cargo_plate_folder

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/exp_2_sunflowers'

target_versions = ['v0_with_gnps', 'v1', 'v2', 'v3', 'v4', 'v5']

base_design_import_files = [os.path.join(experiment_folder, v, f'{v}_design.xlsx') for v in target_versions]
regen_graphics = False
generate_echo = True
generate_lab_helpers = True

main_plates = get_cutting_edge_plates(100) # this is the first design that uses the new 100uM working stock concentrations
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

old_antihandle_plates = get_plateclass('HashCadPlate',
                                       crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                       assembly_handle_plate_folder)

old_handle_plates = get_plateclass('HashCadPlate',
                                   crisscross_h5_handle_plates[0:3],
                                   assembly_handle_plate_folder)

########## LOADING AND CHECKING DESIGN
for file, version_name in zip(base_design_import_files, target_versions):

    echo_folder = os.path.join(experiment_folder, version_name, 'echo_commands')
    lab_helper_folder = os.path.join(experiment_folder, version_name, 'lab_helper_sheets')
    create_dir_if_empty(echo_folder, lab_helper_folder)
    print('%%%%%%%%%%%%%%%')
    print('ASSESSING DESIGN: %s' % version_name)

    megastructure = Megastructure(import_design_file=file)
    hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    ########## PATCHING PLATES
    if version_name == 'v3':
        megastructure.patch_placeholder_handles([old_antihandle_plates, old_handle_plates, main_plates[3]] + [src_010])
    else:
        megastructure.patch_placeholder_handles(main_plates + (src_010,))

    megastructure.patch_flat_staples(main_plates[0])

    if version_name == 'v0_with_gnps':
        selected_slats = {}
        for slat_id in range(20, 34):
            name = f'layer2-slat{slat_id}'
            selected_slats[name] = megastructure.slats[name]
        selected_slats['layer3-slat16'] = megastructure.slats['layer3-slat16']
    else:
        selected_slats = megastructure.slats

    target_volume = 75 # nl per staple
    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                        destination_plate_name=f'{version_name}_sunflower',
                                                        reference_transfer_volume_nl=target_volume,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=False,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes= True if version_name!= 'v3' else False,
                                                        output_filename=f'{version_name}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'{version_name}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    handle_mix_ratio=15, # setting to 15 to be able to setup the reaction inside the echo plate itself
                                    peg_concentration=3,
                                    peg_groups_per_layer=2)

    ########## OPTIONAL EXPORTS
    if regen_graphics:
        megastructure.create_standard_graphical_report(os.path.join(experiment_folder, version_name, f'{version_name}_graphics'), filename_prepend=f'{version_name}_', generate_3d_video=True)
        megastructure.create_blender_3D_view(os.path.join(experiment_folder, version_name, f'{version_name}_graphics'), filename_prepend=f'{version_name}_',
                                             camera_spin=False, correct_slat_entrance_direction=True, include_bottom_light=False)
