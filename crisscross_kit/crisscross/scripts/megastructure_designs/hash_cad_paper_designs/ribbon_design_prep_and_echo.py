import os
import copy

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import simpsons_mixplate_antihandles_maxed, cargo_plate_folder

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/pointy_ribbon'

base_design_import_files = [os.path.join(experiment_folder,'H26', 'pointy_ribbon_seed_and_repeating_unit_combined_H26.xlsx'),
                            os.path.join(experiment_folder, 'H30', 'pointy_ribbon_seed_and_repeating_unit_combined_H30.xlsx')]

regen_graphics = False
generate_echo = True
generate_lab_helpers = True

main_plates = get_cutting_edge_plates(100) # this is the first design that uses the new 100uM working stock concentrations
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

########## LOADING AND CHECKING DESIGN
for design_file in base_design_import_files:
    hamming = design_file.split('_')[-1].split('.')[0]
    echo_folder = os.path.join(experiment_folder, hamming, 'echo_commands')
    lab_helper_folder = os.path.join(experiment_folder, hamming, 'lab_helper_sheets')
    create_dir_if_empty(echo_folder, lab_helper_folder)
    print('%%%%%%%%%%%%%%%')
    megastructure = Megastructure(import_design_file=design_file)
    hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    ########## PATCHING PLATES

    megastructure.patch_placeholder_handles(main_plates + (src_010,))
    megastructure.patch_flat_staples(main_plates[0])
    selected_slats = {}

    for s_id, slat in megastructure.slats.items():
        layer =  slat.layer
        num_id = s_id.split('slat')[-1]

        if layer == 1 and int(num_id) < 17:
            new_id = 'L1_nuc_%s' % num_id
        if layer == 2 and int(num_id) < 13:
            new_id = 'L2_nuc_%s' % num_id
        if layer == 2 and int(num_id) in [33, 34, 35, 36]:
            new_id = 'L2_nuc_vert_%s' % num_id

        if layer == 2 and int(num_id) in range(13, 29):
            new_id = 'L2_G1_%s' % num_id
        if layer == 2 and (int(num_id) in range(29, 33) or int(num_id) in range(41, 53)):
            new_id = 'L2_G2_%s' % num_id
        if layer == 2 and int(num_id) in range(53, 61):
            new_id = 'L2_vert_%s' % num_id

        if layer == 1 and int(num_id) in range(17, 33):
            new_id = 'L1_G1_%s' % num_id
        if layer == 1 and int(num_id) in range(41, 57):
            new_id = 'L1_G2_%s' % num_id

        if layer == 1 and int(num_id) in range(33, 41):
            new_id = 'L1_vert_%s' % num_id

        selected_slats[new_id] = copy.deepcopy(slat)
        selected_slats[new_id].ID = new_id

    target_volume = 125 # nl per staple
    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                        destination_plate_name=f'pointy_ribbon_{hamming}',
                                                        reference_transfer_volume_nl=target_volume,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes= True,
                                                        output_filename=f'pointy_ribbon_{hamming}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'pointy_ribbon_{hamming}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    handle_mix_ratio=12.5, # setting to 15 to be able to setup the reaction inside the echo plate itself
                                    slat_mixture_volume=100,
                                    peg_concentration=3,
                                    peg_groups_per_layer=4)
