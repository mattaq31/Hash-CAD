import os
import copy
import pandas as pd

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed, cnt_patterning

def flip_mega(megastructure):
    ########################################
    # A) Flip the layers (reverse layer order so top layer becomes layer 1, etc.)

    num_layers = len(megastructure.layer_palette)

    # Rebuild layer_palette with reversed layer numbering and swapped top/bottom orientations
    new_layer_palette = {}
    for old_layer_num, layer_info in megastructure.layer_palette.items():
        new_layer_num = num_layers + 1 - old_layer_num
        new_layer_palette[new_layer_num] = {
            'color': layer_info['color'],
            'ID': layer_info['ID'],
            'top': layer_info['bottom'],  # what was bottom is now top (structure is flipped)
            'bottom': layer_info['top'],  # what was top is now bottom
        }
    megastructure.layer_palette = new_layer_palette

    # Rebuild slats dict with updated layer numbers and keys
    new_slats = {}
    for slat_key, slat in megastructure.slats.items():
        old_layer = slat.layer
        new_layer = num_layers + 1 - old_layer
        slat.layer = new_layer
        slat.layer_color = megastructure.layer_palette[new_layer]['color']

        # Update the slat key to reflect the new layer number
        new_key = slat_key.replace(f'layer{old_layer}-', f'layer{new_layer}-')
        slat.ID = new_key
        new_slats[new_key] = slat
    megastructure.slats = new_slats

    # Flip the original_slat_array along the layer axis
    if hasattr(megastructure, 'original_slat_array') and megastructure.original_slat_array is not None:
        megastructure.original_slat_array = megastructure.original_slat_array[:, :, ::-1]

    # B) Swap assembly handle <-> antihandle categories (not cargo or seeds)
    for slat in megastructure.slats.values():
        for handle_dict in (slat.H2_handles, slat.H5_handles):
            for handle in handle_dict.values():
                if handle.get('category') == 'ASSEMBLY_HANDLE':
                    handle['category'] = 'ASSEMBLY_ANTIHANDLE'
                elif handle.get('category') == 'ASSEMBLY_ANTIHANDLE':
                    handle['category'] = 'ASSEMBLY_HANDLE'

    print(f"Flipped {num_layers} layers and swapped assembly handle/antihandle categories on all slats.")


########################################
# NOTES

# SW158 - Double trench solution binding for GNW design, for Mandy's paper on colocalization of 2 GNWs

# Standard structure, assembly process should be done in two steps

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
P3510 = get_plateclass('HashCadPlate', cnt_patterning, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/BioNWire/SW158_BioNWire_twotrench_rectangle'
#design_folder_prefix = '/Users/matt/Desktop'

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

flip_mega(aarhus_doubletrench) # FLIP DONE HERE

aarhus_doubletrench.patch_placeholder_handles(main_plates + (src_004, P3510,)) # P3510 = cnt_patterning
aarhus_doubletrench.patch_flat_staples(main_plates[0])

########################################
# Making the echo instructions

target_volume = 100 # 150 and 500 below for a nice max volume ### TODO - is this enough?
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
                            slat_mixture_volume=75,
                            peg_concentration=2,
                            peg_groups_per_layer=2)

########################################
# Combine all echo instructions into one file

all_echo_files = ['/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Matthew/echo_run_april_1_2026/fluoro_square/sq_36_fluoro_echo.csv', \
                  '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Matthew/echo_run_april_1_2026/jaewon_square/jaewon_fluoroX_echo.csv', \
                  '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Matthew/echo_run_april_1_2026/plus_sign/capc_v3_echo.csv', \
                  '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW158_BioNWire_twotrench_rectangle/echo_commands/SW158_bionwire_aarhus_doubletrench.csv']

combined_df = pd.concat([pd.read_csv(f) for f in all_echo_files], ignore_index=True)
combined_output_path = os.path.join(echo_folder, '20260401_echo_instructions_all.csv')
combined_df.to_csv(combined_output_path, index=False)
print(f"Combined echo instructions written to {combined_output_path}")
