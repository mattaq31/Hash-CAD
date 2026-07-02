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

# I have enough of the asymmetric starter, so just producing more of the repeating units for SW159

# Will just make 6 copies of everything since they will be used up in future experiments

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/repeatingunits'
output_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW159_asymmetric_repeatingunits'

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

########################################
# Prepare repeating units (standard 4 directions)

RU_names = ["right", "left", "up", "down"]

amount_to_make_SW155 = {} # RU_name: (target volume, number of copies)
amount_to_make_SW155["right"] = (150, 6)
amount_to_make_SW155["left"] = (150, 6)
amount_to_make_SW155["up"] = (150, 6)
amount_to_make_SW155["down"] = (150, 6)

echo_folder = os.path.join(output_folder_prefix, 'echo_commands') # Combine all echo-related materials in the same folder, in SW155
lab_helper_folder = os.path.join(output_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

design_filename = "SW155_repeatingunits_all_domainsincluded.xlsx"
all_repeating_units = Megastructure(import_design_file=os.path.join(design_folder_prefix, design_filename))
all_repeating_units.patch_placeholder_handles(main_plates + (src_004,))
all_repeating_units.patch_flat_staples(main_plates[0])

# Group by slats
RU_slat_IDs = {}
RU_slat_IDs["right"] = [(2, x) for x in range(1,16+1)] # (layer, slat_ID), red
RU_slat_IDs["left"] = [(2, x) for x in range(17,32+1)] # yellow
RU_slat_IDs["up"] = [(1, x) for x in range(1,16+1)] # blue
RU_slat_IDs["down"] = [(1, x) for x in range(17,32+1)] # green

# Regular units (i.e. 1st 4) get their own plate each, and use the full 96-well layout
plate_well_mapping = {} # (plate_number, well)
RU_slats = {} # not grouped by RU, bc the slat_id should identify them

for n_plate, RU in enumerate(RU_names[:4]):
    # Make the same number of copies as indicated, so loop around this N times
    for n_copy in range(amount_to_make_SW155[RU][1]): 
        for n_slatnumber, (layer, id) in enumerate(RU_slat_IDs[RU]):
            old_slat_key = "layer{}-slat{}".format(layer, id)
            new_slat_key = "layer{}-slat{}-{}-copy{}".format(layer, id, RU, n_copy+1) 
            RU_slats[new_slat_key] = copy.deepcopy(all_repeating_units.slats[old_slat_key])
            RU_slats[new_slat_key].ID = new_slat_key # Overwrite the original ID with the new one
            plate_well_mapping[new_slat_key] = (n_plate+1, plate96[n_copy*16+n_slatnumber])

########################################
# Prepare echo commands for regular and special RUs
target_volume_regular = 150 # 150 and 500 below for a nice max volume
target_volume_special = 75 
target_concentration = 500 

print("Writing SW159 echo instructions for the repeating units...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=RU_slats,
                                                    destination_plate_name='repeating_units_slats_regular',
                                                    reference_transfer_volume_nl=target_volume_regular,
                                                    reference_concentration_uM=target_concentration,
                                                    manual_plate_well_assignments=plate_well_mapping,
                                                    output_empty_wells=True,
                                                    output_folder=echo_folder,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename='{}_{}_echo.csv'.format("SW159", 'repeating_units_slats_regular'))

prepare_all_standard_sheets(RU_slats, os.path.join(lab_helper_folder, '{}_{}_labhelper.xlsx'.format("SW159", 'repeating_units_slats_regular')),
                            reference_single_handle_volume=target_volume_regular,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=125,
                            peg_concentration=2,
                            peg_groups_per_layer=2)