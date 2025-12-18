#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 16:52:31 2025

@author: juliefinkel
"""

import os
import pandas as pd
import numpy as np
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import cargo_plate_folder, simpsons_mixplate_antihandles_maxed


# update these depending on user
# experiment_folder = '/Users/juliefinkel/Documents/Projects_postdoc/CrissCross/Sierpinski_triangle_designs/Gadgets_design/Count_8'
# design_file = '/Users/juliefinkel/Documents/Projects_postdoc/CrissCross/Sierpinski_triangle_designs/Gadgets_design/Count_8/20251217-Sierpinski_for_echo_final.xlsx'
# no_handles_file = '/Users/juliefinkel/Documents/Projects_postdoc/CrissCross/Sierpinski_triangle_designs/Gadgets_design/Count_8/20251217_Sierpinski_latestfinal.xlsx'

experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/JF003_Sierpinski_triangle/echo_prep_dec_18'
design_file = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/JF003_Sierpinski_triangle/echo_prep_dec_18/designs/20251217-Sierpinski_for_echo_final.xlsx'
no_handles_file = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/JF003_Sierpinski_triangle/echo_prep_dec_18/designs/sierpinski_no_handles.xlsx'

echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

megastructure = Megastructure(import_design_file=no_handles_file)

# read in handles from design file
design_df = pd.read_excel(design_file, sheet_name=None, header=None)
layer_count = 0

for i, key in enumerate(design_df.keys()):
    if 'slat_layer_' in key:
        layer_count += 1
handle_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], layer_count - 1))

for i in range(layer_count):
    if i != layer_count - 1:
        handle_array[..., i] = design_df['handle_interface_%s' % (i + 1)].values


for key, slat in megastructure.slats.items():
    sides = []
    if slat.layer == 1:
        sides.append('top')
    elif slat.layer == len(megastructure.layer_palette):
        sides.append('bottom')
    else:
        sides.extend(['top', 'bottom'])

    for slat_position_index in range(slat.max_length):
        coords = slat.slat_position_to_coordinate[slat_position_index + 1]
        for side in sides:
            slat_side = megastructure.layer_palette[slat.layer][side]
            if side == 'top':
                handle_val = int(handle_array[coords[0], coords[1], slat.layer-1])
                sel_plates = None
                category = 'ANTIHANDLE'
            else:
                handle_val = int(handle_array[coords[0], coords[1], slat.layer-2])
                sel_plates = None
                category = 'HANDLE'
            if handle_val > 0:
                megastructure.assign_handle_to_slat(slat, slat_position_index + 1, slat_side, str(handle_val), 'ASSEMBLY_%s' % category, 'Assembly|%s|%s' % (category.capitalize(), handle_val), sel_plates, suppress_warnings=False)

regen_graphics = False
generate_echo = True

main_plates = get_cutting_edge_plates(200)
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

valency_results = megastructure.get_parasitic_interactions(
    remove_duplicates_in_layers=[(3, 'antihandles')],)
print(f'Sierpinski core - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')


megastructure.patch_placeholder_handles(main_plates + (src_010,))
megastructure.patch_flat_staples(main_plates[0])

# removes duplicate slats
slat_set = set()
accepted_slats = {}
for slat_id, slat in megastructure.slats.items():
    handle_list = []
    for pos, handle in slat.H2_handles.items():
        handle_list.append(handle['descriptor'])
    for pos, handle in slat.H5_handles.items():
        handle_list.append(handle['descriptor'])
    handle_list_tuple = tuple(handle_list) # a slat is defined by a list of all its handles in sequence

    if handle_list_tuple not in slat_set:
        slat_set.add(handle_list_tuple)
        accepted_slats[slat_id] = slat

if regen_graphics:
    megastructure.create_standard_graphical_report(python_graphics_folder, filename_prepend='sierpinski_pos_', generate_3d_video=True)

if generate_echo:
    target_volume = 75 # nl per staple

    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=accepted_slats,
                                                    destination_plate_name='Sierpinski',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=False,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename='sierpinski_echo.csv')

    prepare_all_standard_sheets(accepted_slats, os.path.join(lab_helper_folder, 'sierpinski_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_sheet_1,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=8)
