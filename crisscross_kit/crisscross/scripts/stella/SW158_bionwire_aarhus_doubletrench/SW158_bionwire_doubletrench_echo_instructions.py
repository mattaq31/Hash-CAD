import os
import copy
import pandas as pd

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed, cnt_patterning

########################################
# NOTES

# SW158 - Double trench solution binding for GNW design, for Mandy's paper on colocalization of 2 GNWs

# Standard structure, assembly process should be done in two steps

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
P3510 = get_plateclass('HashCadPlate', cnt_patterning, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW158_BioNWire_twotrench_rectangle'
output_folder_prefix = design_folder_prefix

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments

########################################
# Build the megastructure

echo_folder = os.path.join(output_folder_prefix, 'echo_commands') # Combine all echo-related materials in the same folder, in SW155
lab_helper_folder = os.path.join(output_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

design_filename = "20260323_bionwire_doubletrench.xlsx"
aarhus_doubletrench = Megastructure(import_design_file=os.path.join(design_folder_prefix, design_filename))
aarhus_doubletrench.patch_placeholder_handles(main_plates + (src_004, P3510,)) # P3510 = cnt_patterning
aarhus_doubletrench.patch_flat_staples(main_plates[0])

########################################
# Making the echo instructions

target_volume = 75 # 150 and 500 below for a nice max volume ### TODO - is this enough?
target_concentration = 500 
print("Writing SW158 echo instructions for BioNWire double-trench rectangles for Aarhus...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=aarhus_doubletrench.slats,
                                                        destination_plate_name='bionwire_doubletrench',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW158", 'bionwire_aarhus_doubletrench'))

prepare_all_standard_sheets(aarhus_doubletrench.slats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW158", 'bionwire_aarhus_doubletrench_protocols')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

########################################
# Combine all echo instructions into one file

# TODO: combine all echo instruction files