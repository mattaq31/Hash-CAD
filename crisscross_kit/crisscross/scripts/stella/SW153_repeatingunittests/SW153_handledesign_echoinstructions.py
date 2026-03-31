import os
import copy
import pandas as pd

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed, cnt_patterning_2

########################################
# NOTES

# Make the 90° repeating units 

########################################

# General stuff

main_plates = get_cutting_edge_plates(200) # New working stocks are at 200 uM TODO - double check this
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW153_repeatingunits_tolerance'
generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

########################################
# SW153
echo_folder = os.path.join(design_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(design_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

### --- Make structures --- ###
print("Making SW153 Square starter and 90° repeating units...")
RU_90 = Megastructure(import_design_file=os.path.join(design_folder_prefix, "SW153_H30squarestarter_repeatblocks_handlesassigned_repeatingonly_MM2_locked_finishedevolving_v2_MM2.xlsx"))
RU_90.patch_placeholder_handles(main_plates + (src_004,))
RU_90.patch_flat_staples(main_plates[0])

########################################
# Prepare echo instructions

# Make duplicates of the repeating units so that there are enough

double_repeatingunitslats = copy.deepcopy(RU_90.slats) # first make a copy of the original
slats_to_duplicate = [f"slat{x}" for x in range(129,160+1)]
# Add slats for repeating unit
for slat_name, slat in RU_90.slats.items():
    parse_slat_name = slat_name.split('-')
    is_phantom = False
    if len(parse_slat_name) > 2:
        if "phantom" in parse_slat_name[2]:
            is_phantom = True
    
    if slat.layer == 2 and parse_slat_name[1] in slats_to_duplicate and not is_phantom: # don't copy phantoms
        double_repeatingunitslats[slat_name + '-2'] = copy.deepcopy(slat)
        double_repeatingunitslats[slat_name + '-2'].ID = slat_name + '-2'
    if slat.layer == 3: # add automatically
        double_repeatingunitslats[slat_name + '-2'] = copy.deepcopy(slat)
        double_repeatingunitslats[slat_name + '-2'].ID = slat_name + '-2'

# 90° repeating unit components
target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW153 echo instructions for 90° repeating units...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=double_repeatingunitslats,
                                                        destination_plate_name='90°_repeatingunits',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        center_only_well_pattern=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW153", '90deg_repeatingunits'))

prepare_all_standard_sheets(double_repeatingunitslats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW153", '90deg_repeatingunits')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)



########################################
# For next time:

# Make the 60° repeating units
# Design the 60° startar such that it uses the 647 fluorophore handle staples

# Here are the fluorescent staples we currently have:
#    position 9, handle 34, fluorophore 647
#    position 23, handle 40, fluorophore 647
#    position 30, handle 58, fluorophore 647
#    position 2, handle 58, fluorophore 532 (not user in this design - may incorporate on the seed in the future)

# So, in total, there are 4 different designs
#   90° starter (80) [SW153]
#   90° repeating units (64 slats) [SW153]
#   60° starter 180 (192 + 96 = 288) [SW154] - bottom layer with and without fluorophores
#   60° one repeating unit (160) [SW154] - with fluorophores

#   60° repeating units (160 * 4 = 640 slats) [SW155] - this may have to wait for a future experiment

########################################