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

# Double hexagon growth (Starter Assembly and Step 1 assembly onto Starter)

# Contains fluorescent slats (fluorophore-modified hanldes). One group L0G3 has both fluorescent and non-fluorescent versions.
# Note clearly which slats require manual transfer to add fl∏uorophores and which don't.

# 647 fluorophore slats should be pooled separately during PEG. Non-fluorescent version should be made and pooled with each other.

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW154_hexgrowth_kineticassay'
generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

########################################
# Global variable helpers

plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)]

########################################
# SW154
echo_folder = os.path.join(design_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(design_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

# Fluorescent slats 532 for both assays (position, handle ID, oligo ID)
fluor532_L0G1F_slats = {x : (2, 58, "SSW087") for x in [233, 235, 237, 239, 241, 243, 245, 248]}
L0G1F = range(225, 256+1)

# Fluorescent slats 647 for Assay 1, on bottom layer
fluor647_L0G3F_slats = {221:(23, 40, "SSW099"), 217:(9, 34, "SSW098"), 213:(30, 58, "SSW088"), 209:(9, 34, "SSW098"), \
                        205:(23, 40, "SSW099"), 201:(9, 34, "SSW098"), 197:(23, 40, "SSW099"), 193:(30, 58, "SSW088")}
L0G3F = range(193, 224+1)

# Fluorescent slats 647 for Assay 2, on middle layer
fluor647_L1G5F_slats = {99:(9, 34, "SSW098"), 102:(23, 40, "SSW099"), 107:(30, 58, "SSW088"), 110:(23, 40, "SSW099"), \
                        115:(9, 34, "SSW098"), 118:(23, 40, "SSW099"), 123:(9, 34, "SSW098"), 126:(30, 58, "SSW088")}
L1G5F = range(97, 128+1)

### --- Make structures --- ###
print("Making SW154 Hexgrid components for kinetics assay...")
design_filename = "hexagon_units_v3_final.xlsx"
hex_kinetics = Megastructure(import_design_file=os.path.join(design_folder_prefix, design_filename))
hex_kinetics.patch_placeholder_handles(main_plates + (src_004,))
hex_kinetics.patch_flat_staples(main_plates[0])

########################################
# Prepare echo instructions

# Group all fluorescent slats separately in another plate and separate cleanly
# Duplicate the 647 fluorescent slats for Assay 1 and make one version non-fluorescent (i.e. fully Echo-transferred)

fluor_slats_included = {}
# Change fluorescent slats in L0G1 and L1G5 to have -532 or -647 suffix in the slat ID
for slat_key, slat_item in hex_kinetics.slats.items():
    layer_N, slat_N = slat_key.split('-')[0], slat_key.split('-')[1]
    if layer_N == "layer1" and int(slat_N[4:]) in L0G1F: # Slats in the nucX 532 control group
        fluor_slats_included[slat_key + "-532"] = copy.deepcopy(slat_item)
        fluor_slats_included[slat_key + "-532"].ID = slat_key + "-532"

        if int(slat_N[4:]) in fluor532_L0G1F_slats.keys(): 
            # Need to knock out a handle for manually transferred fluorophores
            for handle_id, handle in slat_item.H5_handles.items():
                if handle_id == fluor532_L0G1F_slats[int(slat_N[4:])][0]:
                    if int(handle["value"]) == fluor532_L0G1F_slats[int(slat_N[4:])][1]:
                        del fluor_slats_included[slat_key + "-532"].H5_handles[handle_id]["plate"]
                        
    elif layer_N == "layer2" and int(slat_N[4:]) in L1G5F: # Slats in the 647 assay 2 group
        fluor_slats_included[slat_key + "-647"] = copy.deepcopy(slat_item)
        fluor_slats_included[slat_key + "-647"].ID = slat_key + "-647"

        if int(slat_N[4:]) in fluor647_L1G5F_slats.keys():
            # Need to knock out a handle for manually transferred fluorophores
            for handle_id, handle in slat_item.H5_handles.items():
                if handle_id == fluor647_L1G5F_slats[int(slat_N[4:])][0]:
                    if int(handle["value"]) == fluor647_L1G5F_slats[int(slat_N[4:])][1]:
                        del fluor_slats_included[slat_key + "-647"].H5_handles[handle_id]["plate"]

    elif layer_N == "layer1" and int(slat_N[4:]) in L0G3F: # Slats in the 647 assay 1 
        # Copy regular version 
        fluor_slats_included[slat_key] = copy.deepcopy(slat_item)
        fluor_slats_included[slat_key].ID = slat_key

        # Copy fluorescent version
        fluor_slats_included[slat_key + "-647"] = copy.deepcopy(slat_item)
        fluor_slats_included[slat_key + "-647"].ID = slat_key + "-647"
        
        if int(slat_N[4:]) in fluor647_L0G3F_slats.keys():
            # Need to knock out a handle for manually transferred fluorophores in the fluorescent version
            for handle_id, handle in slat_item.H5_handles.items():
                if handle_id == fluor647_L0G3F_slats[int(slat_N[4:])][0]:
                    if int(handle["value"]) == fluor647_L0G3F_slats[int(slat_N[4:])][1]:
                        del fluor_slats_included[slat_key + "-647"].H5_handles[handle_id]["plate"]

    else: # normal slat - add to the included dict with the same ID
        fluor_slats_included[slat_key] = copy.deepcopy(slat_item)
        fluor_slats_included[slat_key].ID = slat_key

# Plate organization
plate_well_mapping = {}

# Plate 1
# L0-G1-F
for slat_id, well in zip(L0G1F, plate96_centered[:32]):
    plate_well_mapping[f"layer1-slat{slat_id}-532"] = (1, well)
# L0-G2
for slat_id, well in zip(range(257, 288+1), plate96_centered[32:]):
    plate_well_mapping[f"layer1-slat{slat_id}"] = (1, well)

# Plate 2
# L0-G3 (dark)
for slat_id, well in zip(range(193, 224+1), plate96_centered[:32]):
    plate_well_mapping[f"layer1-slat{slat_id}"] = (2, well)
# L0-G3-F (fluor)
fluor_wells_L0G3 = {34:{"row":"A", "column": 3}, 40:{"row":"B", "column": 3}, 58:{"row":"C", "column": 3}} # increasing counter for which well
# Row A will be for k34, row B for k40, row C for k58
for slat_id, well in zip(L0G3F, plate96_centered[32:]):
    if slat_id in fluor647_L0G3F_slats.keys():
        # Put on plate 7 and skip the original well position
        pos, handle_seq, oligo_id = fluor647_L0G3F_slats[slat_id]
        first_well = fluor_wells_L0G3[handle_seq]["row"] + str(fluor_wells_L0G3[handle_seq]["column"])
        second_well = fluor_wells_L0G3[handle_seq]["row"] + str(fluor_wells_L0G3[handle_seq]["column"]+1)
        plate_well_mapping[f"layer1-slat{slat_id}-647"] = (7, first_well)
        
        # Also make a duplicate of the actual slat
        fluor_slats_included[f"layer1-slat{slat_id}-647-2"] = \
                copy.deepcopy(fluor_slats_included[f"layer1-slat{slat_id}-647"])
        fluor_slats_included[f"layer1-slat{slat_id}-647-2"].ID = f"layer1-slat{slat_id}-647-2"
        
        # Add a plate mapping
        plate_well_mapping[f"layer1-slat{slat_id}-647-2"] = (7, second_well)
        fluor_wells_L0G3[handle_seq]["column"] += 2
    else:
        plate_well_mapping[f"layer1-slat{slat_id}-647"] = (2, well)

# Plate 3
# L1-G1
for slat_id, well in zip(range(33, 64+1), plate96_centered[:32]):
    plate_well_mapping[f"layer2-slat{slat_id}"] = (3, well)
# L1-G2
for slat_id, well in zip(range(481, 512+1), plate96_centered[32:]):
    plate_well_mapping[f"layer2-slat{slat_id}"] = (3, well)

# Plate 4
# L1-G3
for slat_id, well in zip(range(1, 32+1), plate96_centered[:32]):
    plate_well_mapping[f"layer2-slat{slat_id}"] = (4, well)
# L1-G4
for slat_id, well in zip(range(129, 160+1), plate96_centered[32:]):
    plate_well_mapping[f"layer2-slat{slat_id}"] = (4, well)

# Plate 5
# L1-G5-F 
fluor_wells_L1G5 = {34:{"row":"E", "column": 3}, 40:{"row":"F", "column": 3}, 58:{"row":"G", "column": 3}} # increasing counter for which well
# Row E will be for k34, row F for k40, row G for k58
for slat_id, well in zip(range(97, 128+1), plate96_centered[:32]):
    if slat_id in fluor647_L1G5F_slats.keys():
        # Put on plate 7 and skip the original well position
        pos, handle_seq, oligo_id = fluor647_L1G5F_slats[slat_id]
        first_well = fluor_wells_L1G5[handle_seq]["row"] + str(fluor_wells_L1G5[handle_seq]["column"])
        second_well = fluor_wells_L1G5[handle_seq]["row"] + str(fluor_wells_L1G5[handle_seq]["column"]+1)
        plate_well_mapping[f"layer2-slat{slat_id}-647"] = (7, first_well)
        
        # Also make a duplicate of the actual slat
        fluor_slats_included[f"layer2-slat{slat_id}-647-2"] = \
                copy.deepcopy(fluor_slats_included[f"layer2-slat{slat_id}-647"])
        fluor_slats_included[f"layer2-slat{slat_id}-647-2"].ID = f"layer2-slat{slat_id}-647-2"
        
        # Add a plate mapping
        plate_well_mapping[f"layer2-slat{slat_id}-647-2"] = (7, second_well)
        fluor_wells_L1G5[handle_seq]["column"] += 2
    
    else:
        plate_well_mapping[f"layer2-slat{slat_id}-647"] = (5, well)
    
# L2-G1
for slat_id, well in zip(range(33, 64+1), plate96_centered[32:]):
    plate_well_mapping[f"layer3-slat{slat_id}"] = (5, well)

# Plate 6
# L2-G2 
for slat_id, well in zip(range(65, 96+1), plate96_centered[:32]):
    plate_well_mapping[f"layer3-slat{slat_id}"] = (6, well)
# L2-G3
for slat_id, well in zip(range(1, 32+1), plate96_centered[32:]):
    plate_well_mapping[f"layer3-slat{slat_id}"] = (6, well)

target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW154 echo instructions for hexgrid kinetics...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=fluor_slats_included,
                                                        destination_plate_name='hexgrid_kinetics',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        manual_plate_well_assignments=plate_well_mapping,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW154", 'hexgrid_kinetics'))

prepare_all_standard_sheets(fluor_slats_included, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW154", 'hexgrid_kinetics')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

########################################
# Make an excel sheet of manual transfers for fluorophore-modified staples

manual_transfers = []
column_names = ["Component", "Source Oligo Name", "Destination Well", "Transfer Volume", "Destination Plate Name"]
# Note that fluorophore staples are at 100 µM; transfer volume is in units of nL too
# L0-G1-F slats
for slat_id, staple_info in fluor532_L0G1F_slats.items():
    pos, handle_id, oligo_id = staple_info
    plate_n, dest_well = plate_well_mapping[f"layer1-slat{slat_id}-532"]
    manual_instruction = [f"layer1-slat{slat_id}-532_h5_staple_{pos}", oligo_id, \
                            dest_well, target_volume*target_concentration/100, f"hexgrid_kinetics_{plate_n}"]
    manual_transfers.append(manual_instruction)

# L0-G3-F slats
for slat_id, staple_info in fluor647_L0G3F_slats.items():
    pos, handle_id, oligo_id = staple_info  
    plate_n, dest_well = plate_well_mapping[f"layer1-slat{slat_id}-647"]
    manual_instruction = [f"layer1-slat{slat_id}-647_h5_staple_{pos}", oligo_id, \
                            dest_well, target_volume*target_concentration/100, f"hexgrid_kinetics_{plate_n}"]
    manual_transfers.append(manual_instruction)

    # Repeat for the duplicate
    plate_n, dest_well = plate_well_mapping[f"layer1-slat{slat_id}-647-2"]
    manual_instruction = [f"layer1-slat{slat_id}-647-2_h5_staple_{pos}", oligo_id, \
                            dest_well, target_volume*target_concentration/100, f"hexgrid_kinetics_{plate_n}"]
    manual_transfers.append(manual_instruction)

# L1-G5-F slats
for slat_id, staple_info in fluor647_L1G5F_slats.items():
    pos, handle_id, oligo_id = staple_info  
    plate_n, dest_well = plate_well_mapping[f"layer2-slat{slat_id}-647"]
    manual_instruction = [f"layer2-slat{slat_id}-647_h5_staple_{pos}", oligo_id, \
                            dest_well, target_volume*target_concentration/100, f"hexgrid_kinetics_{plate_n}"]
    manual_transfers.append(manual_instruction)

    # Repeat for the duplicate
    plate_n, dest_well = plate_well_mapping[f"layer2-slat{slat_id}-647-2"]
    manual_instruction = [f"layer2-slat{slat_id}-647-2_h5_staple_{pos}", oligo_id, \
                            dest_well, target_volume*target_concentration/100, f"hexgrid_kinetics_{plate_n}"]
    manual_transfers.append(manual_instruction)

manual_df = pd.DataFrame(manual_transfers, columns=column_names)
manual_df.to_csv(os.path.join(echo_folder, \
                                '{}_{}.csv'.format("SW154", 'hexgrid_kinetics_manual_transfers')), index=False)