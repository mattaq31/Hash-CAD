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

# SW164 - This is for troubleshooting the strange slat folding as observed in SW160. There will be just 4 copies of the first slat
# of each RU, plus a "flat" no-handle 6hb slat, with all h2/h5 staples pooled by the echo.
# Target volume should be as high as possible (to 20 µL per well final volume) so that I can test 2 x 2 conditions (2 PCR machines x 2 core staple tubes)

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix_RUs_flatslat = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW164_slatfoldingtroubleshooting'
output_folder_prefix = design_folder_prefix_RUs_flatslat 

# RUs + flatslat design is a copy of the one for SW155, but with a flat slat added to layer 3
generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

rows = 'ABCDEFGH'
cols_centered = range(3,11)

########################################
# Prepare repeating units (standard 4 directions)

echo_folder = os.path.join(output_folder_prefix, 'echo_commands') # Combine all echo-related materials in the same folder, in SW155
lab_helper_folder = os.path.join(output_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

design_filename = "SW164_RU_flat_troubleshooting.xlsx"
all_slats_to_make = Megastructure(import_design_file=os.path.join(design_folder_prefix_RUs_flatslat, design_filename))
all_slats_to_make.patch_placeholder_handles(main_plates + (src_004,))
all_slats_to_make.patch_flat_staples(main_plates[0])

# Group by slats
n_copies = 4
all_slat_IDs = [(2, 1), (2, 17), (1, 1), (1, 17), (3, 1)] # (layer, slat_ID) in order of right, left, up, down, flat
slat_names = ["right", "left", "up", "down", "flat"]

# Regular units (i.e. 1st 4) get their own plate each, and use the full 96-well layout
plate_well_mapping = {} # (plate_number, well) 
RU_slats = {} # not grouped by RU, bc the slat_id should identify them

for i, (layer, id) in enumerate(all_slat_IDs):
    # Make the same number of copies as indicated, so loop around this N times
    for n_copy in range(n_copies): 
        old_slat_key = "layer{}-slat{}".format(layer, id)
        new_slat_key = "layer{}-slat{}-{}-copy{}".format(layer, id, slat_names[n_copy], n_copy+1) 
        RU_slats[new_slat_key] = copy.deepcopy(all_slats_to_make.slats[old_slat_key])
        RU_slats[new_slat_key].ID = new_slat_key # Overwrite the original ID with the new one
        plate_well_mapping[new_slat_key] = (1, rows[n_copy] + str(cols_centered[i]))

########################################
# Prepare echo commands for regular and special RUs
target_volume_regular = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 

print("Writing SW163 echo instructions for troubleshooting slat folding...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=RU_slats,
                                                    destination_plate_name='troubleshooting_slats',
                                                    reference_transfer_volume_nl=target_volume_regular,
                                                    reference_concentration_uM=target_concentration,
                                                    manual_plate_well_assignments=plate_well_mapping,
                                                    output_empty_wells=True,
                                                    output_folder=echo_folder,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename='{}_{}_echo.csv'.format("SW160", 'troubleshooting_slats'))

prepare_all_standard_sheets(RU_slats, os.path.join(lab_helper_folder, '{}_{}_labhelper.xlsx'.format("SW163", 'troubleshooting_slats')),
                            reference_single_handle_volume=target_volume_regular,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=125,
                            peg_concentration=2,
                            peg_groups_per_layer=2)

