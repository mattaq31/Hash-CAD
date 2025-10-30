import os
import copy
from string import ascii_uppercase

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty, plate96_center_pattern
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed

# WARNING: This file is quite convoluted and contains a lot of twists and turns - both to accommodate the special DB-R slats as well as to accommodate various custom plate formulations
# should use this file as a reference for when streamlining the whole process and prevent it from becoming this complicated again

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/MAD-C13 Chirality with CisTrans'
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

all_components_design = os.path.join(experiment_folder, 'CisTrans all options with assembly handles.xlsx')

########## LOADING DESIGNS
megastructure = Megastructure(import_design_file=all_components_design)

regen_graphics = False
generate_echo = True

main_plates = get_cutting_edge_plates(100) # this is the first design that uses the new 100uM working stock concentrations
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

valency_results = megastructure.get_parasitic_interactions()
print(f'Parasitic interactions - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

if regen_graphics:
    megastructure.create_standard_graphical_report(python_graphics_folder, generate_3d_video=True)

# flipping DB-R slats to be DB-L slats, since we actually only have DB-L hardware slats in the lab currently
# BE WARNED - THE COORDINATES ARE NOT TRANSFERRED SO IF THESE NEED TO BE USED AT ANY POINT THEY WILL BE INCORRECT
for s_id, slat in megastructure.slats.items():
    if slat.slat_type == 'DB-R':
        new_h5_handles = {}
        for original_key, handle_value in slat.H5_handles.items():
            new_h5_handles[33 - original_key] = copy.deepcopy(handle_value)
            slat.placeholder_list.remove(f'handle|{original_key}|h5')
            slat.placeholder_list.append(f'handle|{33 - original_key}|h5')

        new_h2_handles = {}
        for original_key, handle_value in slat.H2_handles.items():
            new_h2_handles[33 - original_key] = copy.deepcopy(handle_value)
            slat.placeholder_list.remove(f'handle|{original_key}|h2')
            slat.placeholder_list.append(f'handle|{33 - original_key}|h2')

        slat.H5_handles = new_h5_handles
        slat.H2_handles = new_h2_handles

megastructure.patch_placeholder_handles(main_plates + (src_004,))
megastructure.patch_flat_staples(main_plates[0]) # this plate contains only flat staples

for s_id, slat in megastructure.slats.items():
    if slat.slat_type == 'DB-L' or slat.slat_type == 'DB-R':
        slat.H2_handles[16]['category'] = 'SKIP'
        slat.H5_handles[16]['category'] = 'SKIP'

# group 1 - 1.5*
# group 2 - 1*
# group 3 - 3* (double 1.5*)
slat_group_1 = {}
slat_group_2 = {}
slat_group_3 = {}

for slat_id, slat in megastructure.slats.items():
    # purple DBs on layer 2 (used for nucleation instead of using a seed) and all the stopgap DBs on layer 3/5: regular 50 µL with 50 nM scaffold
    if slat.layer == 2 and slat.slat_type != 'tube':
        slat_group_2[slat_id] = slat
    if slat.layer == 3 or slat.layer == 5:
        if int(slat_id.split('slat')[-1]) in list(range(17, 49)):
            slat_group_2[slat_id] = slat
        # All teal and yellow slats and DB (so layers 3/5 + 4/6) except the stopgap DBs: 75 µL with 50 nM scaffold
        else:
            slat_group_1[slat_id] = slat

    # All teal and yellow slats and DB (so layers 3/5 + 4/6) except the stopgap DBs: 75 µL with 50 nM scaffold
    if slat.layer in [4, 6]:
        slat_group_1[slat_id] = slat

    # All purple slats (layers 1+2): 150 µL with 50 nM scaffold (duplicates of 75 µL ea)
    if slat.layer in [1, 2] and slat.slat_type == 'tube':
        slat_numeral = int(slat_id.split('slat')[-1])
        if slat_numeral == 16 and slat.layer == 1:
            # ensuring that layer1-slat16 has its full set of handles and has not had its DB-connecting portions knocked out (refer to design file for more info)
            modified_slat = copy.deepcopy(slat)
            modified_slat.H5_handles = megastructure.slats['layer1-slat33'].H5_handles
            slat_group_3[slat_id] = modified_slat
            continue
        if slat_numeral == 33 and slat.layer == 1:
            continue
        if slat.layer == 2 and slat_numeral in list(range(49, 65)):
            inp_slat = copy.deepcopy(slat)
            inp_slat.ID = f'layer2-{slat_numeral - 32}-dup'
            slat_group_3[f'layer2-{slat_numeral - 32}-dup'] = inp_slat
        elif slat.layer == 1 and slat_numeral in list(range(17, 33)):
            if slat_numeral == 32: # also properly duplicates the special slat 16
                slat_group_3[f'layer1-{slat_numeral - 16}-dup'] = copy.deepcopy(slat_group_3['layer1-slat16'])
                continue
            # this way, can make sure that the duplicate also contains the correct seed slat handles too
            inp_slat = copy.deepcopy(megastructure.slats[f'layer1-slat{slat_numeral - 16}'])
            inp_slat.ID = f'layer1-{slat_numeral - 16}-dup'
            slat_group_3[f'layer1-{slat_numeral - 16}-dup'] = inp_slat

        elif slat.layer == 2 and slat_numeral in list(range(1, 17)):
            slat_group_3[slat_id] = slat
        else:
            slat_group_3[slat_id] = slat

if generate_echo:
    target_volume = 75 * 1.5  # nl per staple
    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict={**slat_group_1, **slat_group_3},
                                                    destination_plate_name=f'cis_trans_group_1',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=True,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename=f'cis_trans_db_echo_commands_group_1.csv')

    prepare_all_standard_sheets({**slat_group_1, **slat_group_3}, os.path.join(lab_helper_folder, f'cis_trans_db_experiment_helpers_group_1.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_1,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50 * 1.5,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    target_volume = 75  # nl per staple

    # in an attempt to reduce the use of one plate, manually assign special plate positioning for the extra slats here
    special_manual_plate_positioning = {}
    special_index_count = 0
    col_count = 1
    for index, (slat_id, slat) in enumerate(slat_group_2.items()):
        if index >= len(plate96_center_pattern):
            if special_index_count > 7:
                special_index_count = 0
                col_count += 1
            special_manual_plate_positioning[slat_id] = (1, ascii_uppercase[special_index_count] + f'{col_count}')
            special_index_count += 1
        else:
            special_manual_plate_positioning[slat_id] = (1, plate96_center_pattern[index])


    echo_sheet_2 = convert_slats_into_echo_commands(slat_dict=slat_group_2,
                                                    destination_plate_name=f'cis_trans_db_group_2',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=True,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    manual_plate_well_assignments=special_manual_plate_positioning,
                                                    output_filename=f'cis_trans_db_echo_commands_group_2.csv')

    prepare_all_standard_sheets(slat_group_2, os.path.join(lab_helper_folder, f'cis_trans_db_experiment_helpers_group_2.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_2,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)


# tacking on some additional slats from the hexagon run
print('ADDING EXTRA HEXAGON SLATS FOR ANOTHER PROJECT')
hex_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/CAPCs/version_2_hexagons/designs'
capc = Megastructure(import_design_file=os.path.join(hex_folder, 'peripheral_patches.xlsx'))
valency_results = capc.get_parasitic_interactions()
print(f'Parasitic interactions - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

capc.patch_placeholder_handles(main_plates + (src_010, src_004))
capc.patch_flat_staples(main_plates[0])

# select only slats in layer 1
selected_slats = {}
for c, s in capc.slats.items():
    if s.layer == 1:
        selected_slats[c] = copy.deepcopy(s)

target_volume = 75 * 1.5 # nl per staple

echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                destination_plate_name=f'capc_bottom',
                                                reference_transfer_volume_nl=target_volume,
                                                output_folder=echo_folder,
                                                center_only_well_pattern=False,
                                                plate_viz_type='barcode',
                                                normalize_volumes=True,
                                                output_filename=f'capc_bottom_echo_commands.csv')

prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'capc_bottom_experiment_helpers.xlsx'),
                            reference_single_handle_volume=target_volume,
                            reference_single_handle_concentration=500,
                            echo_sheet=None if not generate_echo else echo_sheet_1,
                            handle_mix_ratio=15,
                            slat_mixture_volume=75,
                            peg_concentration=3,
                            split_core_staple_pools=True,
                            peg_groups_per_layer=4)


