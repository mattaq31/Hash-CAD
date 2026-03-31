import os
import copy
import pandas as pd

import glob

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed, cnt_patterning_2

########################################
# NOTES

# First halves of SW155 and SW156 - running echo on these together, then echo the second halves later

# 6 different starters for the large scale 90° repeating units assembly
# Starters for the repeat of the SW154 experiment - no fluorophores currently.
#   Make sure to change these from the original code and update the wiki - no 532 fluorophores anywhere

# Note that SW156 handles may be different from the previous kinetics assay, because previous 532 dye spots are no longer restricted to handle 58

########################################
# General stuff

generate_SW155 = False # To skip repeatedly printing this during debugging
generate_SW156 = True 

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix_SW155 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/starters'
output_folder_prefix_SW155 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/part1'

design_folder_prefix_SW156 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'
output_folder_prefix_SW156 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments

########################################
# SW155 1st half (starters only)
echo_folder = os.path.join(output_folder_prefix_SW155, 'echo_commands') # Combine all echo-related materials in the same folder, in SW155
lab_helper_folder = os.path.join(output_folder_prefix_SW155, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

### --- Make structures --- ###

if generate_SW155: # Turn off protocol generation for debugging
    print("Making SW155 Repeating unit starters...")
    #starter_symmetries = [("asymmetrical", 2), ("vmirror", 3), ("hmirror",1), ("180",1), ("2xmirror", 2), ("180circular",1)] # Symmetry type name and number of copies
    starter_symmetries = [("asymmetrical", 1), ("vmirror", 2), ("hmirror", 1), ("180",1), ("2xmirror", 1), ("180circular", 1)] # Symmetry type name and number of copies

    for symmetry, n_copies in starter_symmetries:
        print("Making SW155 starter:", symmetry)
        design_filename = f"SW155_starter_square_{symmetry}.xlsx"
        starter_structure = Megastructure(import_design_file=os.path.join(design_folder_prefix_SW155, design_filename))
        starter_structure.patch_placeholder_handles(main_plates + (src_004,))
        starter_structure.patch_flat_staples(main_plates[0])

        target_volume_SW155 = 150 # 150 and 500 below for a nice max volume
        target_concentration_SW155 = 500 
        for n in range(1, n_copies+1):
            print(f"Writing SW155 starter echo instructions, copy {n}, for {symmetry}...")
            echo_sheet_square = convert_slats_into_echo_commands(slat_dict=starter_structure.slats,
                                                                destination_plate_name="SW155_starter_{}_{}".format(symmetry, n),
                                                                reference_transfer_volume_nl=target_volume_SW155,
                                                                reference_concentration_uM=target_concentration_SW155,
                                                                center_only_well_pattern=True,
                                                                output_folder=echo_folder,
                                                                plate_viz_type='barcode',
                                                                normalize_volumes=True,
                                                                output_filename='{}_starter_{}_echo_copy_{}.csv'.format("SW155", symmetry, n))

            prepare_all_standard_sheets(starter_structure.slats, os.path.join(lab_helper_folder, '{}_starter_{}_protocol_copy_{}.xlsx'.format("SW155", symmetry, n)),
                                    reference_single_handle_volume=target_volume_SW155,
                                    reference_single_handle_concentration=target_concentration_SW155,
                                    echo_sheet=None if not generate_echo else echo_sheet_square,
                                    handle_mix_ratio=10, 
                                    slat_mixture_volume=100,
                                    peg_concentration=2,
                                    peg_groups_per_layer=1)
    

########################################
# SW156 1st half (starters only)

if generate_SW156: # Turn off protocol generation for debugging
    ### --- Make structures --- ###
    print("Making SW156 Hexgrid repeating unit kinetics assay starters...")

    design_filename = "hexagon_units_v4_final.xlsx"
    hex_kinetics = Megastructure(import_design_file=os.path.join(design_folder_prefix_SW156, design_filename))
    hex_kinetics.patch_placeholder_handles(main_plates + (src_004,))
    hex_kinetics.patch_flat_staples(main_plates[0])

    ### --- Organize slats --- ###
    # The same system as before, but we'll only include the 1st hexagon-related slats for now

    # Non-fluorescent slat groupings

    L0G1A = range(233, 248+1) # nucX; make two copies
    L0G1B = list(range(225, 232+1)) + list(range(249,256+1)) # non-nucX; also make two copies
    L0G2 = range(257, 288+1) # only 1 copy - if more are needed, deal with that later
    L0G3 = range(193, 224+1)
    L1G1 = range(33, 64+1)
    L1G2 = range(481, 512+1)
    L1G3 = range(1, 32+1)

    hex_starter_slats = {}
    # Change fluorescent slats in L0G1 and L1G5 to have -532 or -647 suffix in the slat ID
    for slat_key, slat_item in hex_kinetics.slats.items():
        layer_N, slat_N = slat_key.split('-')[0], slat_key.split('-')[1]
        if (layer_N == "layer1" and int(slat_N[4:]) in L0G1A) or \
            (layer_N == "layer1" and int(slat_N[4:]) in L0G1B): # nucX and non-nucX, make 2 copies
            hex_starter_slats[slat_key] = copy.deepcopy(slat_item)
            hex_starter_slats[slat_key].ID = slat_key
            hex_starter_slats[slat_key + "-2"] = copy.deepcopy(slat_item)
            hex_starter_slats[slat_key + "-2"].ID = slat_key + "-2"
        
        elif (layer_N == "layer1" and int(slat_N[4:]) in L0G1B) or \
            (layer_N == "layer1" and int(slat_N[4:]) in L0G2) or \
            (layer_N == "layer1" and int(slat_N[4:]) in L0G3) or \
            (layer_N == "layer2" and int(slat_N[4:]) in L1G1) or \
            (layer_N == "layer2" and int(slat_N[4:]) in L1G2) or \
            (layer_N == "layer2" and int(slat_N[4:]) in L1G3): # all others
            # All other slats, make 1 copy
            hex_starter_slats[slat_key] = copy.deepcopy(slat_item)
            hex_starter_slats[slat_key].ID = slat_key


    # Plate organization
    plate_well_mapping = {}

    # Plate 1
    # L0G1A, copy 1
    for slat_id, well in zip(L0G1A, plate96_centered[:16]):
        plate_well_mapping[f"layer1-slat{slat_id}"] = (1, well)
    # L0G1A, copy 2
    for slat_id, well in zip(L0G1A, plate96_centered[16:32]):
        plate_well_mapping[f"layer1-slat{slat_id}-2"] = (1, well)
    # L0G1B, copy 1
    for slat_id, well in zip(L0G1B, plate96_centered[32:48]):
        plate_well_mapping[f"layer1-slat{slat_id}"] = (1, well)
     # L0G1B, copy 2
    for slat_id, well in zip(L0G1B, plate96_centered[48:]):
        plate_well_mapping[f"layer1-slat{slat_id}-2"] = (1, well)

    # Plate 2
    # L0G2
    for slat_id, well in zip(L0G2, plate96_centered[:32]):
        plate_well_mapping[f"layer1-slat{slat_id}"] = (2, well)
    # L0G3
    for slat_id, well in zip(L0G3, plate96_centered[32:]):
        plate_well_mapping[f"layer1-slat{slat_id}"] = (2, well)

    # Plate 3
    # L1G1
    for slat_id, well in zip(L1G1, plate96_centered[:32]):
        plate_well_mapping[f"layer2-slat{slat_id}"] = (3, well)
    # L1G2
    for slat_id, well in zip(L1G2, plate96_centered[32:]):
        plate_well_mapping[f"layer2-slat{slat_id}"] = (3, well)

    # Plate 4
    # L1G3
    for slat_id, well in zip(L1G3, plate96_centered[:32]):
        plate_well_mapping[f"layer2-slat{slat_id}"] = (4, well)

    print("Writing SW156 hex kinetics starter echo instructions...")

    target_volume_SW156 = 150 # 150 and 500 below for a nice max volume
    target_concentration_SW156 = 500 
    print("Writing SW156 echo instructions for hexgrid kinetics...")
    echo_sheet_square = convert_slats_into_echo_commands(slat_dict=hex_starter_slats,
                                                            destination_plate_name='hexgrid_kinetics_starters',
                                                            reference_transfer_volume_nl=target_volume_SW156,
                                                            reference_concentration_uM=target_concentration_SW156,
                                                            manual_plate_well_assignments=plate_well_mapping,
                                                            output_empty_wells=True,
                                                            output_folder=echo_folder,
                                                            plate_viz_type='barcode',
                                                            normalize_volumes=True,
                                                            output_filename='{}_{}.csv'.format("SW156", 'hexgrid_kinetics_starters'))

    prepare_all_standard_sheets(hex_starter_slats, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW156", 'hexgrid_kinetics_starters')),
                                reference_single_handle_volume=target_volume_SW156,
                                reference_single_handle_concentration=target_concentration_SW156,
                                echo_sheet=None if not generate_echo else echo_sheet_square,
                                handle_mix_ratio=10, 
                                slat_mixture_volume=100,
                                peg_concentration=2,
                                peg_groups_per_layer=4)

########################################
# Combine all echo instructions into 1

def combine_csv_files_with_prefix(folder_path, prefix, output_filename):
    """
    Combine all CSV files in a folder with a specific prefix into a single file.
    Uses the header from the first file and concatenates all data rows.
    """
    # Find all CSV files with the specified prefix
    pattern = os.path.join(folder_path, f"{prefix}*.csv")
    csv_files = sorted(glob.glob(pattern))
    
    if not csv_files:
        print(f"No CSV files found with prefix '{prefix}' in {folder_path}")
        return
    
    print(f"Found {len(csv_files)} file(s) with prefix '{prefix}':")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")
    
    combined_data = []
    header = None
    
    # Read all files
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        
        # Store header from first file
        if header is None:
            header = df.columns.tolist()
        
        # Append all rows to combined data
        combined_data.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(combined_data, ignore_index=True)
    
    # Save combined file
    output_path = os.path.join(folder_path, output_filename)
    combined_df.to_csv(output_path, index=False)
    print(f"\n✓ Combined file saved: {output_filename}")
    print(f"  Total rows: {len(combined_df)}")
    
    return output_path

# Combine all SW155 echo instructions
combine_csv_files_with_prefix(echo_folder, "SW155", "all_echo_instructions_combined_SW155.csv")