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

# Preparing echo instructions via the scripting library bc the app won't let me select and precisely mark
# fluorescent staples and positions for several slats!!!

# Make two copies of each starter for SW166, should come out to 4 full plates total 

# Don't include the 4th layer

########################################
# General stuff

generate_echo = True 
test_handle_compatibility = True

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW166_new_60starters'
output_folder_prefix = design_folder_prefix

#square_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW166_new_60starters/SW166_squarefirst_parallelogram_fluors.xlsx'
#ribbon_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW166_new_60starters/SW166_ribbonfirst_parallelogram_fluors.xlsx'

square_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW166_new_60starters/SW166_squarefirst_parallelogram_fluors_pos9and30.xlsx'
ribbon_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW166_new_60starters/SW166_ribbonfirst_parallelogram_fluors_pos9and30.xlsx'

echo_folder = os.path.join(design_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(design_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

n_copies = 2

########################################
# Specify fluorophore positions - this is the version using all 3 fluorophore positions
# Both are on layer 2
#ribbon_fluor_positions = {1:(30, 58, "SSW088"), 7:(30, 58, "SSW088"), 13:(30, 58, "SSW088"), 19:(30, 58, "SSW088"), 25:(30, 58, "SSW088"), \
#                          3:(23, 40, "SSW099"), 9:(23, 40, "SSW099"), 15:(23, 40, "SSW099"), 21:(23, 40, "SSW099"), 27:(23, 40, "SSW099"), \
#                          5:(9, 34, "SSW098"), 11:(9, 34, "SSW098"), 17:(9, 34, "SSW098"), 23:(9, 34, "SSW098"), 29:(9, 34, "SSW098")}

#square_fluor_positions = {33:(30, 58, "SSW088"), 37:(30, 58, "SSW088"), 43:(30, 58, "SSW088"), 49:(30, 58, "SSW088"), \
#                          35:(23, 40, "SSW099"), 39:(23, 40, "SSW099"), 45:(23, 40, "SSW099"), 51:(23, 40, "SSW099"), 55:(23, 40, "SSW099"), \
#                          41:(9, 34, "SSW098"), 47:(9, 34, "SSW098"), 53:(9, 34, "SSW098"), 57:(9, 34, "SSW098"), 60:(9, 34, "SSW098"), 63:(9, 34, "SSW098")}

########################################
# Specify fluorophore positions - this is the version using only positions 9 and 30 due to stock shortages
# Both are on layer 2
ribbon_fluor_positions = {}
for n in range(8):
    slat_id = n * 4 + 1
    ribbon_fluor_positions[slat_id] = (30, 58, "SSW088")
for n in range(7):
    slat_id = n * 4 + 3
    ribbon_fluor_positions[slat_id] = (9, 34, "SSW098")

square_fluor_positions = {}
for n in range(8):
    slat_id = n * 2 + 35
    square_fluor_positions[slat_id] = (30, 58, "SSW088")
for n in range(7):
    slat_id = n * 4 + 40
    square_fluor_positions[slat_id] = (9, 34, "SSW098")

########################################
# Load in megastructure design and fill staples for ribbon-first parallelogram
ribbon_parallelogram = Megastructure(import_design_file=ribbon_design_file)
ribbon_parallelogram.patch_placeholder_handles(main_plates + (src_004,))
ribbon_parallelogram.patch_flat_staples(main_plates[0])

all_slats = {}

# Ribbon parallelogram
for n in range(n_copies):
    for slat_key, slat_item in ribbon_parallelogram.slats.items():
        layer_N, slat_N = slat_key.split('-')[0], slat_key.split('-')[1]
        slat_id = int(slat_N[4:])

        if layer_N != "layer4": 
            if layer_N == "layer2" and slat_id in ribbon_fluor_positions:  # make a copy first
                new_slat_key = f"R-L{layer_N[-1]}-S{slat_id}-647-C{n+1}"
                all_slats[new_slat_key] = copy.deepcopy(slat_item)
                all_slats[new_slat_key].ID = new_slat_key

                # Pop out fluorescent staples to force manual transfer in the slats dictionary
                for handle_id, handle in slat_item.H5_handles.items():
                        staple_pos, staple_handle, _ = ribbon_fluor_positions[slat_id]
                        if handle_id == staple_pos and int(handle["value"]) == staple_handle: # double check
                            del all_slats[new_slat_key].H5_handles[handle_id]["plate"]

            else:
                new_slat_key = f"R-L{layer_N[-1]}-S{slat_id}-C{n+1}"
                all_slats[new_slat_key] = copy.deepcopy(slat_item)
                all_slats[new_slat_key].ID = new_slat_key

########################################
# Load in megastructure design and fill staples for square-first parallelogram
square_parallelogram = Megastructure(import_design_file=square_design_file)
square_parallelogram.patch_placeholder_handles(main_plates + (src_004,))
square_parallelogram.patch_flat_staples(main_plates[0])

# Square parallelogram
for n in range(n_copies):
    for slat_key, slat_item in square_parallelogram.slats.items():
        layer_N, slat_N = slat_key.split('-')[0], slat_key.split('-')[1]
        slat_id = int(slat_N[4:])

        if layer_N != "layer4": 
            if layer_N == "layer2" and (slat_id in square_fluor_positions):  # make a copy first
                new_slat_key = f"S-L{layer_N[-1]}-S{slat_id}-647-C{n+1}"
                all_slats[new_slat_key] = copy.deepcopy(slat_item)
                all_slats[new_slat_key].ID = new_slat_key

                # Pop out fluorescent staples to force manual transfer in the slats dictionary
                for handle_id, handle in slat_item.H5_handles.items():
                        staple_pos, staple_handle, _ = square_fluor_positions[slat_id]
                        if handle_id == staple_pos and int(handle["value"]) == staple_handle: # double check
                            del all_slats[new_slat_key].H5_handles[handle_id]["plate"]

            else:
                new_slat_key = f"S-L{layer_N[-1]}-S{slat_id}-C{n+1}"
                all_slats[new_slat_key] = copy.deepcopy(slat_item)
                all_slats[new_slat_key].ID = new_slat_key

########################################
# Prepare the echo instructions

target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW166 echo instructions for 60° new starters...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=all_slats,
                                                        destination_plate_name='parallelogram_starters',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW166", 'parallelogram_starters'))

prepare_all_standard_sheets(all_slats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW166", 'parallelogram_starters')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

########################################
# Prepare a pipetting instruction list for fluorescent staples. Don't move the slat positions so that we only have 4 dest plates
# TODO

manual_transfers = echo_sheet_square[echo_sheet_square["Source Plate Name"] == "MANUAL TRANSFER"]

printed_manual_instructions = [] # name, position, handle, Oligo ID, Destination Plate, Destination Well, Volume 
for _, row in manual_transfers.iterrows():
    oligo_info = row['Component'].split('-')
    slat_id = int(oligo_info[2][1:])
    design_type = oligo_info[0]

    if design_type == "S": # follow square pipetting instructions
        staple_pos, staple_handle, oligo_ID = square_fluor_positions[slat_id]
    elif design_type == "R": # follow ribbon pipetting instructions
        staple_pos, staple_handle, oligo_ID = ribbon_fluor_positions[slat_id]

    printed_manual_instructions.append([row['Component'], staple_pos, staple_handle, oligo_ID, \
                                        row['Destination Plate Name'], row['Destination Well'], 500])
    # Instead of using row['Transfer Volume'] just hard code in 500 nL bc it's a bit lower than 100 µM and should have been at 200 µM anyway
        
manual_instructions_df = pd.DataFrame(printed_manual_instructions, columns=["Component", "Staple Position", "Staple Handle", "Oligo ID", "Destination Plate Name", "Destination Well", "Transfer Volume"])
manual_instructions_df.to_csv(os.path.join(echo_folder, 'SW166_manual_transfer_instructions.csv'))

for oligo_id, total_vol in manual_instructions_df.groupby("Oligo ID")["Transfer Volume"].sum().items():
    print(f"{oligo_id} - {total_vol:.1f} nL used in total ({total_vol * 1.2:.1f} nL given 20% buffer)")