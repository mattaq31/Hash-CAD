import os
import copy
import pandas as pd

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder

########################################
# NOTES

# Make 2 copies at 125 µL each of Asymmetric starters for both 2, and 3 designs for RU and bead loss experiments (SW162). W and Y still have plenty of V-mirror left from SW155

# Make varying copies of standard 90 deg RU directions for solid-phase assembly

########################################
# General stuff

generate_echo = True 
test_handle_compatibility = True

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_file_starter = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/starters/SW155_starter_square_asymmetrical.xlsx'
design_file_RU90 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/repeatingunits/SW155_repeatingunits_all_domainsincluded.xlsx'
output_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW168_SW162_90deg23WYS8_beadloss'

n_copies_starters = 2 # everything at 150 nL
n_copies_RU90 = {"right":5, "left":6, "up":5, "down":4} 

echo_folder = os.path.join(output_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(output_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

########################################
# Pool all slats into one echo file

def standard_96well_plate_generator():
    for row in "ABCDEFGH":
        for col in range(1, 13):
            yield f"{row}{col}"

def centered_96well_plate_generator():
    for row in "ABCDEFGH":
        for col in range(3, 11):
            yield f"{row}{col}"

slats_to_make = {}
plate_well_mapping = {} # (plate_number, well)

# Starter slats
starter_structure = Megastructure(import_design_file=design_file_starter)
starter_structure.patch_placeholder_handles(main_plates + (src_004,))
starter_structure.patch_flat_staples(main_plates[0])

starter_slat_IDs = {} # organized by layer
starter_slat_IDs[1] = [(1, x) for x in range(1,32+1)]
starter_slat_IDs[1] = [(1, x) for x in range(1,32+1)]

for n in range(1, n_copies_starters+1):
    centered_plate_wells = centered_96well_plate_generator() # Fresh plate for each copy
    for layer in [1,2]:
        for id in range(1,32+1):
            old_slat_key = "layer{}-slat{}".format(layer, id)
            new_slat_key = "layer{}-slat{}-c{}".format(layer, id, n) 
            slats_to_make[new_slat_key] = copy.deepcopy(starter_structure.slats[old_slat_key])
            slats_to_make[new_slat_key].ID = new_slat_key # Overwrite the original ID with the new one
            plate_well_mapping[new_slat_key] = (n, next(centered_plate_wells)) # assign to centered wells on each plate

# Repeating unit slats
reg_repeating_units = Megastructure(import_design_file=design_file_RU90)
reg_repeating_units.patch_placeholder_handles(main_plates + (src_004,))
reg_repeating_units.patch_flat_staples(main_plates[0])

# Group by slats
RU_slat_IDs = {}
RU_slat_IDs["right"] = [(2, x) for x in range(1,16+1)] # (layer, slat_ID), red
RU_slat_IDs["left"] = [(2, x) for x in range(17,32+1)] # yellow
RU_slat_IDs["up"] = [(1, x) for x in range(1,16+1)] # blue
RU_slat_IDs["down"] = [(1, x) for x in range(17,32+1)] # green

for n_plate, RU in enumerate(["right", "left", "up", "down"]):
    # Make the same number of copies as indicated, so loop around this N times
    standard_plate_wells = standard_96well_plate_generator() # Fresh plate for each RU direction
    for n_copy in range(1, n_copies_RU90[RU] + 1): 
        for n_slatnumber, (layer, id) in enumerate(RU_slat_IDs[RU]):
            old_slat_key = "layer{}-slat{}".format(layer, id)
            new_slat_key = "l{}-s{}-{}-c{}".format(layer, id, RU, n_copy) 
            slats_to_make[new_slat_key] = copy.deepcopy(reg_repeating_units.slats[old_slat_key])
            slats_to_make[new_slat_key].ID = new_slat_key # Overwrite the original ID with the new one
            plate_well_mapping[new_slat_key] = (n_plate+3, next(standard_plate_wells)) 

########################################
# Prepare the echo instructions
target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW168 echo instructions for asymmetrical starter and repeating units...")
echo_sheet = convert_slats_into_echo_commands(slat_dict=slats_to_make,
                                                        destination_plate_name='asymm-starter_RU90',
                                                        manual_plate_well_assignments=plate_well_mapping,
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW168", 'asymmstarter_RU90_echo'))

prepare_all_standard_sheets(slats_to_make, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW168", 'asymmstarter_RU90_helper')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)