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

# Second halves of SW155 and SW156 - RU units and slats for the fluorescence assay. A few notes:

# Quickly tally up the RU slat consumption for the planned designs to make sure you're making enough with this echo run 
#   (if volume is too large, may consider running the same echo run for RU again on a different day)
# Also estimate the slats needed for the kinetics assay. Will probably need to remake everything except L0-G1B 
#   (but might even need more of that too)
# Don't forget to "knock out" the fluorescent staple spots for SW156 fluorescent slats
########################################

# General stuff

generate_SW155 = True
generate_SW156 = True 

main_plates = get_cutting_edge_plates(200) 
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

design_folder_prefix_SW155 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/repeatingunits'
output_folder_prefix_SW155 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/part2'

design_folder_prefix_SW156 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'
output_folder_prefix_SW156 = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2'

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

# Global variable helpers
plate96_centered = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(3,11)] # centered plate variable for easy well assignments
plate96 = [f"{row}{col}" for row in 'ABCDEFGH' for col in range(1,13)] # full plate variable for easy well assignments

########################################
# SW155 2nd half (repeating units)

if generate_SW155:

    # Each RU is assigned to its own plate, and since PEG would just pool everything together, this should be pretty 
    # straightforward. No need to center them, just one copy after the other

    RU_names = ["right", "left", "up", "down", "hbridge", "vbridge", "seal"]

    amount_to_make_SW155 = {} # RU_name: (target volume, number of copies)
    amount_to_make_SW155["right"] = (150, 6)
    amount_to_make_SW155["left"] = (150, 5)
    amount_to_make_SW155["up"] = (150, 6)
    amount_to_make_SW155["down"] = (150, 3)

    # the special RUs are used only once, don't need much - can put these on the same plate and use a centered well layout
    amount_to_make_SW155["hbridge"] = (75, 1)
    amount_to_make_SW155["vbridge"] = (75, 1)
    amount_to_make_SW155["seal"] = (75, 1)

    ########################################
    # SW155 RUs
    echo_folder = os.path.join(output_folder_prefix_SW155, 'echo_commands') # Combine all echo-related materials in the same folder, in SW155
    lab_helper_folder = os.path.join(output_folder_prefix_SW155, 'lab_helper_sheets')
    create_dir_if_empty(echo_folder, lab_helper_folder)

    # Pull design from file
    design_filename = "SW155_repeatingunits_all_domainsincluded.xlsx"
    all_repeating_units = Megastructure(import_design_file=os.path.join(design_folder_prefix_SW155, design_filename))
    all_repeating_units.patch_placeholder_handles(main_plates + (src_004,))
    all_repeating_units.patch_flat_staples(main_plates[0])

    # Group by slats
    RU_slat_IDs = {}
    RU_slat_IDs["right"] = [(2, x) for x in range(1,16+1)] # (layer, slat_ID), red
    RU_slat_IDs["left"] = [(2, x) for x in range(17,32+1)] # yellow
    RU_slat_IDs["up"] = [(1, x) for x in range(1,16+1)] # blue
    RU_slat_IDs["down"] = [(1, x) for x in range(17,32+1)] # green

    RU_slat_IDs["hbridge"] = [(2, x) for x in range(49, 64+1)] # orange
    RU_slat_IDs["vbridge"] = [(1, x) for x in range(33, 48+1)] # cyan
    RU_slat_IDs["seal"] = [(2, x) for x in range(33, 48+1)] # purple

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

    # Special units (centered plate, all 3 on same plate) - echo instructions made separately bc they are prepared at half the volume
    current_n_copy = -1
    plate_well_mapping_special = {} # (plate_number, well)
    RU_slats_special = {} 
    for RU in RU_names[-3:]:
        for n_copy in range(amount_to_make_SW155[RU][1]):
            current_n_copy += 1
            for n_slatnumber, (layer, id) in enumerate(RU_slat_IDs[RU]):
                old_slat_key = "layer{}-slat{}".format(layer, id)
                new_slat_key = "layer{}-slat{}-{}-copy{}".format(layer, id, RU, n_copy+1)
                RU_slats_special[new_slat_key] = copy.deepcopy(all_repeating_units.slats[old_slat_key])
                RU_slats_special[new_slat_key].ID = new_slat_key
                plate_well_mapping_special[new_slat_key] = (1, plate96_centered[current_n_copy*16+n_slatnumber])
        
    ########################################
    # Prepare echo commands for regular and special RUs
    target_volume_SW155_regular = 150 # 150 and 500 below for a nice max volume
    target_volume_SW155_special = 75 
    target_concentration_SW155 = 500 

    print("Writing SW155 echo instructions for the repeating units...")
    echo_sheet_square = convert_slats_into_echo_commands(slat_dict=RU_slats,
                                                            destination_plate_name='repeating_units_slats_regular',
                                                            reference_transfer_volume_nl=target_volume_SW155_regular,
                                                            reference_concentration_uM=target_concentration_SW155,
                                                            manual_plate_well_assignments=plate_well_mapping,
                                                            output_empty_wells=True,
                                                            output_folder=echo_folder,
                                                            plate_viz_type='barcode',
                                                            normalize_volumes=True,
                                                            output_filename='{}_{}_echo.csv'.format("SW155", 'repeating_units_slats_regular'))

    prepare_all_standard_sheets(RU_slats, os.path.join(lab_helper_folder, '{}_{}_labhelper.xlsx'.format("SW155", 'repeating_units_slats_regular')),
                                reference_single_handle_volume=target_volume_SW155_regular,
                                reference_single_handle_concentration=target_concentration_SW155,
                                echo_sheet=None if not generate_echo else echo_sheet_square,
                                handle_mix_ratio=10, 
                                slat_mixture_volume=125,
                                peg_concentration=2,
                                peg_groups_per_layer=4)
    
    # Special RUs prepared at half the volume
    echo_sheet_square = convert_slats_into_echo_commands(slat_dict=RU_slats_special,
                                                            destination_plate_name='repeating_units_slats_special',
                                                            reference_transfer_volume_nl=target_volume_SW155_special,
                                                            reference_concentration_uM=target_concentration_SW155,
                                                            manual_plate_well_assignments=plate_well_mapping_special,
                                                            output_empty_wells=True,
                                                            output_folder=echo_folder,
                                                            plate_viz_type='barcode',
                                                            normalize_volumes=True,
                                                            output_filename='{}_{}_echo.csv'.format("SW155", 'repeating_units_slats_special'))

    prepare_all_standard_sheets(RU_slats_special, os.path.join(lab_helper_folder, '{}_{}_labhelper.xlsx'.format("SW155", 'repeating_units_slats_special')),
                                reference_single_handle_volume=target_volume_SW155_special,
                                reference_single_handle_concentration=target_concentration_SW155,
                                echo_sheet=None if not generate_echo else echo_sheet_square,
                                handle_mix_ratio=10, 
                                slat_mixture_volume=60,
                                peg_concentration=2,
                                peg_groups_per_layer=4)

########################################
# SW156 2nd half (fluorescent assay slats)
# TODO put on another file

# First, check that the new slats are indeed compatible with the starters
starter_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2/SW156_hexagon_units_v4_final.xlsx'
assay2_fluorslats_design_file = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW156_hexgrowth_kineticassay_trial2/SW156_assay2_30fluors_samenucX-domain1_evolved.xlsx'

starter_mega = Megastructure(import_design_file=starter_design_file)
starter_mega.patch_placeholder_handles(main_plates + (src_004,))
starter_mega.patch_flat_staples(main_plates[0])

assay2_mega = Megastructure(import_design_file=assay2_fluorslats_design_file)
assay2_mega.patch_placeholder_handles(main_plates + (src_004,))
assay2_mega.patch_flat_staples(main_plates[0])

nucX_slats = [(1, x) for x in range(233,248+1)]
domain1_slats = [(2, x) for x in range(481,512+1)]

# Side by side comparison
for (layer, id) in nucX_slats:
    slat_key = "layer{}-slat{}".format(layer, id)
    if starter_mega.slats[slat_key] != assay2_mega.slats[slat_key]:
        print("Mismatch found in slat {}:".format(slat_key))
        
        starter_h2_handles = []
        assay2_h2_handles = []
        print("  Comparing h2 handles...")
        for pos in range(1,33):
            starter_h2 = starter_mega.slats[slat_key].H2_handles[pos]
            assay2_h2 = assay2_mega.slats[slat_key].H2_handles[pos]
            starter_h2_handles.append(starter_h2["value"])
            assay2_h2_handles.append(assay2_h2["value"])
            if starter_h2 != assay2_h2:
                print("    H2 Handle position {}: starter {}, assay2 {}".format(pos, starter_h2, assay2_h2))

        starter_h5_handles = []
        assay2_h5_handles = []
        print("  Comparing h5 handles...")
        for pos in range(1,33):
            starter_h5 = starter_mega.slats[slat_key].H5_handles[pos]
            assay2_h5 = assay2_mega.slats[slat_key].H5_handles[pos]
            starter_h5_handles.append(starter_h5["value"])
            assay2_h5_handles.append(assay2_h5["value"])
            if starter_h5 != assay2_h5:
                print("    H5 Handle position {}: starter {}, assay2 {}".format(pos, starter_h5, assay2_h5))
        print("\n")
    else:
        continue

# TODO: separately group Assay 1 slats and Assay 2 slats, also specify which handles are manual transfers
# Double check that enough slats are made

# TODO: prepare a list of manual transfers like last time - note that these are at 100 µM
print("foobar")

# TODO: add all csv files, specifying the locations