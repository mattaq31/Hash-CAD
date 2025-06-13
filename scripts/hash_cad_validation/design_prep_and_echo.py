import os
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cargo_plates, get_cutting_edge_plates


########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs'

target_designs = ['megastar']

base_design_import_files = [os.path.join(experiment_folder, f, f'{f}_design_hashcad_seed.xlsx') for f in target_designs]
regen_graphics = True
generate_echo = False
generate_lab_helpers = False

main_plates = get_cutting_edge_plates()
cargo_plates = get_cargo_plates()

########## LOADING AND CHECKING DESIGN
for file, design_name in zip(base_design_import_files, target_designs):

    echo_folder = os.path.join(experiment_folder, design_name, 'echo_commands')
    lab_helper_folder = os.path.join(experiment_folder, design_name, 'lab_helper_sheets')
    create_dir_if_empty(echo_folder, lab_helper_folder)
    print('%%%%%%%%%%%%%%%')
    print('ASSESSING DESIGN: %s' % design_name)

    megastructure = Megastructure(import_design_file=file)
    hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    ########## PATCHING PLATES
    megastructure.patch_placeholder_handles(main_plates + cargo_plates)
    megastructure.patch_flat_staples(main_plates[0])

    target_volume = 100 # nl per staple
    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                     destination_plate_name=design_name,
                                     reference_transfer_volume_nl=target_volume,
                                     output_folder=echo_folder,
                                     center_only_well_pattern=False,
                                     plate_viz_type='barcode',
                                     output_filename=f'{design_name}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'{design_name}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    peg_concentration=3,
                                    peg_groups_per_layer=2 if (design_name == 'recycling' or design_name == 'lily' or design_name == 'turnstile') else 4)

    ########## OPTIONAL EXPORTS
    if regen_graphics:
        megastructure.create_standard_graphical_report(os.path.join(experiment_folder, design_name, f'{design_name}_graphics'), filename_prepend=f'{design_name}_', generate_3d_video=True)

        megastructure.create_blender_3D_view(os.path.join(experiment_folder, design_name, f'{design_name}_graphics'), filename_prepend=f'{design_name}_',
                                             camera_spin=False, correct_slat_entrance_direction=True, include_bottom_light=False)

        if design_name == 'bird': # animation creation
            custom_animation_dict = {}

            groups = [['layer2-slat%s' % x for x in range(145, 161)],
                      ['layer3-slat%s' % x for x in range(1, 33)],
                      ['layer2-slat%s' % x for x in range(49, 65)],
                      ['layer4-slat%s' % x for x in range(1, 33)],
                      ['layer5-slat%s' % x for x in range(1, 17)] + ['layer5-slat%s' % x for x in range(129, 145)],
                      ['layer2-slat%s' % x for x in range(1, 17)] + ['layer5-slat%s' % x for x in range(65, 81)],
                      ['layer1-slat%s' % x for x in range(261, 276)] + ['layer1-slat%s' % x for x in range(277, 278)] + ['layer6-slat%s' % x for x in range(33, 41)] + ['layer6-slat%s' % x for x in range(42, 48)] + ['layer6-slat%s' % x for x in range(49, 51)],
                      ['layer4-slat%s' % x for x in range(49, 65)] + ['layer3-slat%s' % x for x in range(113, 129)],
                      ['layer2-slat%s' % x for x in range(113, 129)] + ['layer5-slat%s' % x for x in range(97, 113)],
                      ['layer4-slat%s' % x for x in range(81, 97)] + ['layer3-slat%s' % x for x in range(129, 145)],
                      ['layer2-slat%s' % x for x in range(129, 145)] + ['layer5-slat%s' % x for x in range(113, 129)],
                      ['layer1-slat%s' % x for x in range(205, 229)] + ['layer6-slat%s' % x for x in range(1, 25)],
                      ]
            for order, group in enumerate(groups):
                for slat in group:
                    custom_animation_dict[slat] = order

            megastructure.create_blender_3D_view(
                                      os.path.join(experiment_folder, design_name, f'{design_name}_graphics', 'animation'),
                                      animate_assembly=True,
                                      correct_slat_entrance_direction=True,
                                      custom_assembly_groups=custom_animation_dict,
                                      animation_type='translate',
                                      camera_spin=True)

