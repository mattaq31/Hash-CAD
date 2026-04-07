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

# Make 2 structures:
#    Simple square with H29 array and SSW041 on non-seed slats
#    Long Snake design from SW143 with corresponding array for a max similarity of 4 (H28)
# Both use the k64 handle set

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) # New working stocks are at 200 uM TODO - double check this
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW152_postassembly_purification'
generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

########################################
# SW152
echo_folder = os.path.join(design_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(design_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

### --- Make structures --- ###
print("Making SW152 Square Megastructure...")
std_square = Megastructure(import_design_file=os.path.join(design_folder_prefix, 'square_purehandle1_design_k64_h3.xlsx'))
std_square.patch_placeholder_handles(main_plates + (src_004,))
std_square.patch_flat_staples(main_plates[0])

print("Making SW152 Long Snake Megastructure...")
long_snake = Megastructure(import_design_file=os.path.join(design_folder_prefix, 'longsnake_purehandle1_k64_h4.xlsx'))
long_snake.patch_placeholder_handles(main_plates + (src_004,))
long_snake.patch_flat_staples(main_plates[0])

########################################
# Prepare echo instructions, for SW143 independently, then put SW146 and SW149 on the same plate

# Square
target_volume = 75
target_concentration = 400 # 400
print("Writing SW152 echo instructions for Square...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=std_square.slats,
                                                        destination_plate_name='purehandle1_square',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        center_only_well_pattern=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW152", 'purehandle1_square'))

prepare_all_standard_sheets(std_square.slats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW152", 'purehandle1_square')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

print("Writing SW152 echo instructions for Long Snake...")
# Only need to remake the Y slats TODO

longsnake_yslats = {}
for slat_name, slat in long_snake.slats.items():
    if slat.layer == 2:
        longsnake_yslats[slat_name] = copy.deepcopy(slat)
        longsnake_yslats[slat_name].ID = slat_name 

echo_sheet_longsnake = convert_slats_into_echo_commands(slat_dict=longsnake_yslats,
                                                        destination_plate_name='purehandle1_longsnake',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        center_only_well_pattern=False,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW152", 'purehandle1_longsnake'))

prepare_all_standard_sheets(longsnake_yslats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW152", 'purehandle1_longsnake')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_longsnake,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

# Combine all echo instructions
design_files_to_combine = [os.path.join(echo_folder, 'SW152_purehandle1_square.csv'),
                           os.path.join(echo_folder, 'SW152_purehandle1_longsnake.csv')]

# read in each csv file, combine together and then save to a new output file
combined_csv = pd.concat([pd.read_csv(f) for f in design_files_to_combine])

combined_csv.to_csv(os.path.join(echo_folder, "SW152_combined_echo.csv"), index=False)