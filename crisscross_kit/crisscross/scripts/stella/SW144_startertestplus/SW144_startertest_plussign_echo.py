import os
from itertools import product

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_cargo_plates, get_cutting_edge_plates
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets

########################################
# NOTES

# Make an 11-step plus sign for testing starter phase (first 3 steps) and the following 8 steps as stepwise growth
# Secondary purification handles are on slats from step 3

########################################

design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW144_startertestplus'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False
export_trench_design = True
target_volume = 120 # nL
example_concentration = 500 # µM
expID = 'SW144'
structure_name = 'starter_plus_sign'

main_plates = get_cutting_edge_plates(100) # This sets the concentration to 100 µM, tho the plate_concentrations.py file still has 500 µM
src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()

########################################
# Make the structures
plus_sign = Megastructure(import_design_file=os.path.join(design_folder, 'plus-11steps_MM3.xlsx'))
plus_sign.patch_placeholder_handles(main_plates + (src_004,))
plus_sign.patch_flat_staples(main_plates[0])

echo_sheet = convert_slats_into_echo_commands(slat_dict=plus_sign.slats,
                                                        destination_plate_name='starter_plus_sign',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=example_concentration,
                                                        center_only_well_pattern=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format(expID, structure_name))

if generate_lab_helpers:
    prepare_all_standard_sheets(plus_sign.slats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format(expID, structure_name)),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=example_concentration,
                                    echo_sheet=None if not generate_echo else echo_sheet,
                                    handle_mix_ratio=10, # setting to 15 to be able to setup the reaction inside the echo plate itself
                                    slat_mixture_volume=100,
                                    peg_concentration=2,
                                    peg_groups_per_layer=2)