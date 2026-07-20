import os
import copy
import pandas as pd

import glob

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder

########################################
# NOTES

# Need much more starters to have enough for the kinetics assay, so focusing on echoing those here

# 6 copies of nucX aka L0-G1A - separate echo csv file

# 3 copies of non-nucX aka L0-G1B and all the others for hex starter - second echo csv file

########################################
# General stuff

generate_echo = True 
test_handle_compatibility = True

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'
output_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'

echo_folder = os.path.join(design_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(design_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

########################################
design_filename = "SW156_hexagon_units_v4_final.xlsx" # Need to use the older structure, because handles between layers 1 and 2 may have changed since evolving to include more fluorophores. Also this version still has the pulldown handles
hex_kinetics = Megastructure(import_design_file=os.path.join(design_folder_prefix, design_filename))
hex_kinetics.patch_placeholder_handles(main_plates + (src_004,))
hex_kinetics.patch_flat_staples(main_plates[0])

### --- Organize starter slats --- ###
slat_group_IDs = {}

slat_group_IDs["L0G1A"] = (range(233, 248+1), 6, 1) # nucX, make 6 copies, layer
slat_group_IDs["L0G1B"] = (list(range(225, 232+1)) + list(range(249,256+1)), 3, 1) # non-nucX, make 3 copies
slat_group_IDs["L0G2"] = (range(257, 288+1), 3, 1)
slat_group_IDs["L0G3"] = (range(193, 224+1), 3, 1)

slat_group_IDs["L1G1"] = (range(33, 64+1), 3, 2)
slat_group_IDs["L1G2"] = (range(481, 512+1), 3, 2)
slat_group_IDs["L1G3"] = (range(1, 32+1), 3, 2)

def plate_96well_generator():
    for row in "ABCDEFGH":
        for col in range(1, 13):
            yield f"{row}{col}"

# Separately make nucX
slats_to_make_1 = {}
plate_well_mapping_1 = {}

plate_n = 0
slat_IDs, num_copies, layer_n = slat_group_IDs["L0G1A"]
plate_n_wells = plate_96well_generator()
for copy_n in range(num_copies):
        for slat_ID in slat_IDs:
            og_slat_key = f"layer{layer_n}-slat{slat_ID}"
            new_slat_key = f"ly{layer_n}-sl{slat_ID}-cp{copy_n+1}"
            slats_to_make_1[new_slat_key] = copy.deepcopy(hex_kinetics.slats[og_slat_key])
            slats_to_make_1[new_slat_key].ID = new_slat_key
            plate_well_mapping_1[new_slat_key] = (plate_n+1, next(plate_n_wells)) # plate, well

# The rest of the starter slats
slats_to_make_2 = {}
plate_well_mapping_2 = {}
for plate_n, slat_group in enumerate(["L0G1B", "L0G2", "L0G3", "L1G1", "L1G2", "L1G3"]):
    slat_IDs, num_copies, layer_n = slat_group_IDs[slat_group]
    plate_n_wells = plate_96well_generator()
    for copy_n in range(num_copies):
        for slat_ID in slat_IDs:
            og_slat_key = f"layer{layer_n}-slat{slat_ID}"
            new_slat_key = f"ly{layer_n}-sl{slat_ID}-cp{copy_n+1}"
            slats_to_make_2[new_slat_key] = copy.deepcopy(hex_kinetics.slats[og_slat_key])
            slats_to_make_2[new_slat_key].ID = new_slat_key
            plate_well_mapping_2[new_slat_key] = (plate_n+1, next(plate_n_wells)) # plate, well

########################################
# Prepare the echo instructions for nucX only

target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW156 echo instructions for hexgrid kinetic starters...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=slats_to_make_1,
                                                        destination_plate_name='hexgrid_kinetics_starters_nucXonly',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        manual_plate_well_assignments=plate_well_mapping_1,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW156", 'hexgrid_kinetics_starters_nucXonly'))

prepare_all_standard_sheets(slats_to_make_1, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW156", 'hexgrid_kinetics_starters_nucXonly')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

########################################
# Prepare the echo instructions for all else/non-nucX

target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW156 echo instructions for hexgrid kinetic starters...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=slats_to_make_2,
                                                        destination_plate_name='hexgrid_kinetics_starters_nonnucX',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        manual_plate_well_assignments=plate_well_mapping_2,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW156", 'hexgrid_kinetics_starters_nonnucX'))

prepare_all_standard_sheets(slats_to_make_2, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW156", 'hexgrid_kinetics_starters_nonnucX')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)