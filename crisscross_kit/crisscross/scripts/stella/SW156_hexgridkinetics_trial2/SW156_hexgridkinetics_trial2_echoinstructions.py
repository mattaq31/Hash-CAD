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

# Second half of SW156, includes the fluorescent slats

# More fluorophores were added than in SW154, so the handle assignments have changed since. There are now a total of 30 fluorophores per assay i.e. per structure

# Make sure to make a version of the first hexagon's slats that are not fluorescent

########################################
# General stuff

generate_echo = True 
test_handle_compatibility = True

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'
output_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'

echo_folder = os.path.join(design_folder_prefix, 'echo_commands')
lab_helper_folder = os.path.join(design_folder_prefix, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

########################################
# First, check that the new slats are indeed compatible with the starters
starter_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2/SW156_hexagon_units_v4_final.xlsx'
assay2_fluorslats_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2/SW156_assay2_30fluors_samenucX-domain1_evolved.xlsx'

if test_handle_compatibility:
    starter_mega = Megastructure(import_design_file=starter_design_file)
    starter_mega.patch_placeholder_handles(main_plates + (src_004,))
    starter_mega.patch_flat_staples(main_plates[0])

    assay2_mega = Megastructure(import_design_file=assay2_fluorslats_design_file)
    assay2_mega.patch_placeholder_handles(main_plates + (src_004,))
    assay2_mega.patch_flat_staples(main_plates[0])

    nucX_slats = [(1, x) for x in range(233,248+1)]
    domain1_slats = [(2, x) for x in range(481,512+1)] # domain onto which the second hexagon unit attaches

    # Side by side comparison - to make sure the starters are compatible with the new slat design
    for (layer, id) in nucX_slats:
        slat_key = "layer{}-slat{}".format(layer, id)
        if starter_mega.slats[slat_key] != assay2_mega.slats[slat_key]:
            
            starter_h2_handles = []
            assay2_h2_handles = []
            for pos in range(1,33):
                starter_h2 = starter_mega.slats[slat_key].H2_handles[pos]
                assay2_h2 = assay2_mega.slats[slat_key].H2_handles[pos]
                starter_h2_handles.append(starter_h2["value"])
                assay2_h2_handles.append(assay2_h2["value"])
                #if starter_h2 != assay2_h2:
                #    print("    H2 Handle position {}: starter {}, assay2 {}".format(pos, starter_h2, assay2_h2))
            if starter_h2_handles != assay2_h2_handles:
                print("    H2 handle values mismatch in layer{}-slat{}: starter {}, assay2 {}".format(layer, id, starter_h2_handles, assay2_h2_handles))

            starter_h5_handles = []
            assay2_h5_handles = []
            for pos in range(1,33):
                starter_h5 = starter_mega.slats[slat_key].H5_handles[pos]
                assay2_h5 = assay2_mega.slats[slat_key].H5_handles[pos]
                starter_h5_handles.append(starter_h5["value"])
                assay2_h5_handles.append(assay2_h5["value"])
                #if starter_h5 != assay2_h5:
                #    print("    H5 Handle position {}: starter {}, assay2 {}".format(pos, starter_h5, assay2_h5))
            if starter_h5_handles != assay2_h5_handles:
                print("    H5 handle values mismatch in layer{}-slat{}: starter {}, assay2 {}".format(layer, id, starter_h5_handles, assay2_h5_handles))
            
            print("\n")
        else:
            continue

########################################
# List special fluorescent slats for easier grouping later

all_groups = ["L0G1A", "L0G1B", "L0G2F", "L0G3F", "L1G1", "L1G2", "L1G3", "L1G4F", "L1G5F", "L2G1", "L2G2", "L2G3"] 
# Every group (except L0G1A, which is no longer needed) is made once, always as the fluorescent version since the starters are already made with the dark slats
# Also don't need 2x purification handles since that was already on the hex starter

# Indicate the slats with fluorophores by slat groupings (position, handle ID, oligo ID)
fluorescent_slat_staples_by_group = {} # slats with fluorophores
fluorescent_slat_group_IDs = {} # all slats regardless of fluorophores
make_n_copies = 1 # change if needed

# Fluorescent slats 647 for Assay 1, on bottom layer
fluorescent_slat_staples_by_group["L0G3F"] = \
                        {220:(9, 34, "SSW098"), 214:(9, 34, "SSW098"), 208:(9, 34, "SSW098"), 202:(9, 34, "SSW098"), 196:(9, 34, "SSW098"), \
                        222:(23, 40, "SSW099"), 216:(23, 40, "SSW099"), 210:(23, 40, "SSW099"), 204:(23, 40, "SSW099"), 198:(23, 40, "SSW099"), \
                        224:(30, 58, "SSW088"), 218:(30, 58, "SSW088"), 212:(30, 58, "SSW088"), 206:(30, 58, "SSW088"), 200:(30, 58, "SSW088")}
fluorescent_slat_group_IDs["L0G3F"] = range(193, 224+1)

fluorescent_slat_staples_by_group["L0G2F"] = \
                         {259:(9, 34, "SSW098"), 265:(9, 34, "SSW098"), 271:(9, 34, "SSW098"), 277:(9, 34, "SSW098"), 283:(9, 34, "SSW098"), \
                        261:(23, 40, "SSW099"), 267:(23, 40, "SSW099"), 273:(23, 40, "SSW099"), 279:(23, 40, "SSW099"), 285:(23, 40, "SSW099"), \
                        257:(30, 58, "SSW088"), 263:(30, 58, "SSW088"), 269:(30, 58, "SSW088"), 275:(30, 58, "SSW088"), 281:(30, 58, "SSW088")}
fluorescent_slat_group_IDs["L0G2F"] = range(257, 288+1)

# Fluorescent slats 647 for Assay 2, on middle layer
fluorescent_slat_staples_by_group["L1G5F"] = \
                        {99:(9, 34, "SSW098"), 105:(9, 34, "SSW098"), 111:(9, 34, "SSW098"), 117:(9, 34, "SSW098"), 123:(9, 34, "SSW098"), \
                        101:(23, 40, "SSW099"), 107:(23, 40, "SSW099"), 113:(23, 40, "SSW099"), 119:(23, 40, "SSW099"), 125:(23, 40, "SSW099"), \
                        97:(30, 58, "SSW088"), 103:(30, 58, "SSW088"), 109:(30, 58, "SSW088"), 115:(30, 58, "SSW088"), 121:(30, 58, "SSW088")}
fluorescent_slat_group_IDs["L1G5F"] = range(97, 128+1)

fluorescent_slat_staples_by_group["L1G4F"] = \
                        {133:(9, 34, "SSW098"), 139:(9, 34, "SSW098"), 145:(9, 34, "SSW098"), 151:(9, 34, "SSW098"), 157:(9, 34, "SSW098"), \
                        131:(23, 40, "SSW099"), 137:(23, 40, "SSW099"), 143:(23, 40, "SSW099"), 149:(23, 40, "SSW099"), 155:(23, 40, "SSW099"), \
                        129:(30, 58, "SSW088"), 135:(30, 58, "SSW088"), 141:(30, 58, "SSW088"), 147:(30, 58, "SSW088"), 153:(30, 58, "SSW088")}
fluorescent_slat_group_IDs["L1G4F"] = range(129, 160+1)

# L0-G1 needs to be treated more carefully - don't need more of L0-G1A, but should make more of L0-G1B
fluorescent_slat_group_IDs["L0G1A"] = range(233, 248+1)
fluorescent_slat_group_IDs["L0G1B"] = list(range(225, 232+1)) + list(range(249, 256+1))

# Dark slat indices
fluorescent_slat_group_IDs["L1G1"] = range(33, 64+1)
fluorescent_slat_group_IDs["L1G2"] = range(481, 512+1)
fluorescent_slat_group_IDs["L1G3"] = range(1, 32+1)

fluorescent_slat_group_IDs["L2G1"] = range(33, 64+1)
fluorescent_slat_group_IDs["L2G2"] = range(65, 96+1)
fluorescent_slat_group_IDs["L2G3"] = range(1, 32+1)

########################################
# Initialize the megastructure and make copies of certain slat groups for fluorescent/dark versions
print("Initializing SW156 Hexgrid megastructure...")
hex_kinetics = Megastructure(import_design_file=assay2_fluorslats_design_file)
hex_kinetics.patch_placeholder_handles(main_plates + (src_004,))
hex_kinetics.patch_flat_staples(main_plates[0])

fluor_slats_included = {}
# Change fluorescent slats in L0G1 and L1G5 to have -532 or -647 suffix in the slat ID
for slat_key, slat_item in hex_kinetics.slats.items():
    layer_N, slat_N = slat_key.split('-')[0], slat_key.split('-')[1]
    slat_id = int(slat_N[4:])

    if layer_N == "layer1" and (slat_id in fluorescent_slat_group_IDs["L0G3F"] or \
                                slat_id in fluorescent_slat_group_IDs["L0G2F"]): # Slats with 647 in assay 1 - the L0G3F or L0G2F groups. 

        for n in range(make_n_copies):
            # Fluorescent version only, since the starter already used the dark version
            
            if slat_id in fluorescent_slat_staples_by_group["L0G3F"].keys():
                # Is fluorescent - tag it with 647 and make a copy
                new_slat_key = slat_key + f"-647-{n+1}"
                fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
                fluor_slats_included[new_slat_key].ID = new_slat_key

                # Need to knock out a handle for manually transferred fluorophores in the fluorescent version
                for handle_id, handle in slat_item.H5_handles.items():
                    staple_pos, staple_handle, _ = fluorescent_slat_staples_by_group["L0G3F"][slat_id]
                    if handle_id == staple_pos and int(handle["value"]) == staple_handle:
                        del fluor_slats_included[new_slat_key].H5_handles[handle_id]["plate"]
            
            elif slat_id in fluorescent_slat_staples_by_group["L0G2F"].keys():
                # Is fluorescent - tag it with 647 and make a copy
                new_slat_key = slat_key + f"-647-{n+1}"
                fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
                fluor_slats_included[new_slat_key].ID = new_slat_key

                # Need to knock out a handle for manually transferred fluorophores in the fluorescent version
                for handle_id, handle in slat_item.H5_handles.items():
                    staple_pos, staple_handle, _ = fluorescent_slat_staples_by_group["L0G2F"][slat_id]
                    if handle_id == staple_pos and int(handle["value"]) == staple_handle:
                        del fluor_slats_included[new_slat_key].H5_handles[handle_id]["plate"]
            
            else:
                # Normal slat no fluorescence
                new_slat_key = slat_key + f"-{n+1}"
                fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
                fluor_slats_included[new_slat_key].ID = new_slat_key

    elif layer_N == "layer2" and (slat_id in fluorescent_slat_group_IDs["L1G5F"] or \
                                  slat_id in fluorescent_slat_group_IDs["L1G4F"]): 
        for n in range(make_n_copies):
            # Slats with 647 in assay 2 - the L1G4F or L1G5F groups. Only need to make fluorescent versions, no regulars

            if slat_id in fluorescent_slat_staples_by_group["L1G5F"].keys():
                # Fluorescent slat - tag it with 647 and make a copy
                new_slat_key = slat_key + f"-647-{n+1}"
                fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
                fluor_slats_included[new_slat_key].ID = new_slat_key

                # Need to knock out a handle for manually transferred fluorophores in the fluorescent version
                for handle_id, handle in slat_item.H5_handles.items():
                    staple_pos, staple_handle, _ = fluorescent_slat_staples_by_group["L1G5F"][slat_id]
                    if handle_id == staple_pos and int(handle["value"]) == staple_handle:
                        del fluor_slats_included[new_slat_key].H5_handles[handle_id]["plate"]

            elif slat_id in fluorescent_slat_staples_by_group["L1G4F"].keys():
                # Fluorescent slat - tag it with 647 and make a copy
                new_slat_key = slat_key + f"-647-{n+1}"
                fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
                fluor_slats_included[new_slat_key].ID = new_slat_key

                # Need to knock out a handle for manually transferred fluorophores in the fluorescent version
                for handle_id, handle in slat_item.H5_handles.items():
                    staple_pos, staple_handle, _ = fluorescent_slat_staples_by_group["L1G4F"][slat_id]
                    if handle_id == staple_pos and int(handle["value"]) == staple_handle:
                        del fluor_slats_included[new_slat_key].H5_handles[handle_id]["plate"]

            else:
                # Normal slat no fluorescence
                new_slat_key = slat_key + f"-{n+1}"
                fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
                fluor_slats_included[new_slat_key].ID = new_slat_key

    elif layer_N == "layer1" and slat_id in fluorescent_slat_group_IDs["L0G1A"]:
        # NucX slats - can skip because we already made enough starter, probably
        continue

    else: # normal slats, including L0G1B slats, get included
        for n in range(make_n_copies):
            new_slat_key = slat_key + f"-{n+1}"
            fluor_slats_included[new_slat_key] = copy.deepcopy(slat_item)
            fluor_slats_included[new_slat_key].ID = new_slat_key


########################################
# Map slats such that PEG is straightforward

# Since each slat is used just once, and the max slat concentration is 10 nM, just 1 copy is enough. Arrange slats such that 3 groups share a plate

def plate4_well_generator(zone):
    odd_rows  = "ACEG"
    even_rows = "BDFH"

    if zone == 34: # fluorescent handle ID
        for row in odd_rows:
            for col in range(1, 6):
                yield f"{row}{col}"
    elif zone ==40:
        for row in odd_rows:
            for col in range(7, 12):
                yield f"{row}{col}"
    elif zone == 58:
        for row in even_rows:
            for col in range(1, 6):
                yield f"{row}{col}"
    else:
        raise ValueError(f"zone must be 34, 40, or 58, got {zone}")
    
def plate1_L0G1B_well_generator():
    for row in "BDFH":
        for col in range(9, 13):
            yield f"{row}{col}"

def standard_96well_plate_generator():
    for row in "ABCDEFGH":
        for col in range(1, 13):
            yield f"{row}{col}"

# Plate organization
plate_well_mapping = {}
fluor_plate_info = {} # well: (group, staple_name)

for n in range(make_n_copies):
    # Plate 1 - L0-G1B (rows A & B) on the last four wells of B, D, F, H
    plate1_wells_L0G1B = plate1_L0G1B_well_generator()
    for slat_id in fluorescent_slat_group_IDs["L0G1B"]:
        slat_key = f"layer1-slat{slat_id}-{n+1}"
        next_well = next(plate1_wells_L0G1B)
        plate_well_mapping[slat_key] = (1+n*4, next_well) # plate, well

    # Plate 1 & 4 - L0-G2F (row A & B), L0-G3F (row C & D), L1-G4 (etc.), L1-G5 full 96-well plate. Remove the fluorescent slats to the final SW156 plate and collapse the blank space.
    # Each group gets two rows, leaves the rest of the row empty
    plate4_wells_k34 = plate4_well_generator(34)
    plate4_wells_k40 = plate4_well_generator(40)
    plate4_wells_k58 = plate4_well_generator(58)
    for i, group in enumerate(["L0G2F", "L0G3F", "L1G4F", "L1G5F"]):
        dark_slat_count = 0
        for slat_id in fluorescent_slat_group_IDs[group]: 
            if slat_id in fluorescent_slat_staples_by_group[group]:
                # Pop out to the final plate, defined as plate 5 here
                pos, handle_seq, oligo_id = fluorescent_slat_staples_by_group[group][slat_id]

                # Add only to the specific zones defined for 34 (SSW098), 40 (SSW099), and 58 (SSW088)
                if handle_seq == 34:
                    destination_well = next(plate4_wells_k34)
                elif handle_seq == 40:
                    destination_well = next(plate4_wells_k40)
                elif handle_seq == 58:  
                    destination_well = next(plate4_wells_k58)

                fluor_plate_info[destination_well] = (group, oligo_id)
                plate_well_mapping[f"layer{int(group[1])+1}-slat{slat_id}-647-{n+1}"] = (n*5 + 4, destination_well) # plate, well
            else:
                slat_key = f"layer{int(group[1])+1}-slat{slat_id}-{n+1}"
                dark_slat_well = plate96[i*24 + dark_slat_count]
                plate_well_mapping[slat_key] = (1+n*4, dark_slat_well)
                dark_slat_count += 1

    # Plate 2 & 3 - L1-G1, L1-G2, L1-G3 in a standard 96-well plate
    plate2_groups = ["L1G1", "L1G2", "L1G3"]
    plate3_groups = ["L2G1", "L2G2", "L2G3"]
    for plate_n, groups in zip([2, 3], [plate2_groups, plate3_groups]):
        standard_plate_wells = standard_96well_plate_generator()
        for i, group in enumerate(groups):
            for slat_id in fluorescent_slat_group_IDs[group]: 
                slat_key = f"layer{int(group[1])+1}-slat{slat_id}-{n+1}"
                plate_well_mapping[slat_key] = (n*4 + plate_n, next(standard_plate_wells)) # plate, well
    
########################################
# Prepare the echo instructions

target_volume = 150 # 150 and 500 below for a nice max volume
target_concentration = 500 
print("Writing SW156 echo instructions for hexgrid kinetics...")
echo_sheet_square = convert_slats_into_echo_commands(slat_dict=fluor_slats_included,
                                                        destination_plate_name='hexgrid_kinetics',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=target_concentration,
                                                        manual_plate_well_assignments=plate_well_mapping,
                                                        output_empty_wells=True,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW156", 'hexgrid_kinetics'))

prepare_all_standard_sheets(fluor_slats_included, os.path.join(lab_helper_folder, '{}_{}.xlsx'.format("SW156", 'hexgrid_kinetics')),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=target_concentration,
                            echo_sheet=None if not generate_echo else echo_sheet_square,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)


########################################
# Prepare manual pipetting instructions for the fluorophores