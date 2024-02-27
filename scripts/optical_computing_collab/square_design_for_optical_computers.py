import numpy as np
import pandas as pd
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.core_functions.slat_design import (generate_standard_square_slats, generate_handle_set_and_optimize,
                                                   attach_cargo_handles_to_core_sequences, calculate_slat_hamming)
from crisscross.core_functions.slats import Slat
from crisscross.graphics.megastructures import generate_patterned_square_cco
from crisscross.helper_functions.standard_sequences import simpsons_anti, simpsons
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_handle_plates,
                                                         seed_plug_plate_corner, octahedron_patterning_v1,
                                                         cargo_plate_folder, nelson_quimby_antihandles,
                                                         h2_biotin_direct)
from crisscross.plate_mapping import get_plateclass

########################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_feb_2024'

np.random.seed(8)
read_handles_from_file = True
read_cargo_patterns_from_file = True
########################################

########################################
# cargo definitions
cargo_1 = 'Bart'
cargo_2 = 'Edna'
cargo_biotin = 'Nelson'
crossbar_linkages = ['Homer', 'Krusty', 'Lisa', 'Marge', 'Patty', 'Quimby', 'Smithers']

# mapping sequences to numbers
crossbar_anti_map = {i + 4: simpsons_anti[crossbar_linkages[i]][:10] for i in range(7)}
crossbar_map = {i + 11: simpsons[crossbar_linkages[i]][-10:] for i in
                range(7)}  # due to reverse complement system, need to take sequence from back
cargo_map = {1: simpsons_anti[cargo_1], 2: simpsons_anti[cargo_2], 3: simpsons_anti[cargo_biotin]}

# mapping names to numbers
crossbar_anti_names = {i + 4: f'10mer-anti{crossbar_linkages[i]}' for i in range(7)}
crossbar_names = {i + 11: f'10mer-{crossbar_linkages[i]}' for i in range(7)}
cargo_names = {1: f'anti{cargo_1}', 2: f'anti{cargo_2}', 3: f'anti{cargo_biotin}'}
cargo_names = {**cargo_names, **crossbar_anti_names, **crossbar_names}
########################################

########################################
# Plate sequences
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
crisscross_y_plates = get_plateclass('CrisscrossHandlePlates', crisscross_handle_plates[3:], core_plate_folder)
crisscross_x_plates = get_plateclass('CrisscrossHandlePlates', crisscross_handle_plates[0:3], core_plate_folder)
seed_plate = get_plateclass('SeedPlugPlate', seed_plug_plate_corner, core_plate_folder)
########################################

########################################
# Shape generation and crisscross handle optimisation
slat_array, x_slats, y_slats = generate_standard_square_slats(32)
# optimize handles
if read_handles_from_file:
    handle_array = np.loadtxt(os.path.join(output_folder, 'optimized_handle_array.csv'), delimiter=',').astype(
        np.float32)
    _, _, res = calculate_slat_hamming(slat_array, handle_array, x_slats, y_slats, unique_sequences=32)
    print('Hamming distance from file-loaded design: %s' % np.min(res))
else:
    handle_array = generate_handle_set_and_optimize(slat_array, x_slats, y_slats, unique_sequences=32,
                                                    min_hamming=29, max_rounds=300)
    np.savetxt(os.path.join(output_folder, 'optimized_handle_array.csv'), handle_array.astype(np.int32), delimiter=',',
               fmt='%i')
########################################

########################################
# prepares cargo pattern
cargo_pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
cdf = attach_cargo_handles_to_core_sequences(cargo_pattern, cargo_map, core_plate, slat_type='Y', handle_side=2)
cdf.sort_values(by=['Cargo ID', 'Slat Pos. ID'], inplace=True)
cdf['Category'] = cdf['Cargo ID']
cdf['Handle Side'] = 'h2'

# prepares biotin pattern (full attachment to allow for later adjustment) - not required, Stella already has strands
# biotin_pattern = np.ones((32, 32)) * 3
# biotin_df = attach_cargo_handles_to_core_sequences(biotin_pattern, cargo_map, core_plate, slat_type='X', handle_side=2)
# biotin_df['Category'] = 3
# biotin_df['Handle Side'] = 'h2'
########################################

########################################
# prepares crossbar attachment pattern (pre-made in another script)
crossbar_pattern = np.zeros((32, 32))

for index, sel_pos in enumerate(  # crossbar 1
        [[21.0, 2.0], [18.0, 6.0], [15.0, 10.0], [12.0, 14.0], [9.0, 18.0], [6.0, 22.0], [3.0, 26.0]]):
    crossbar_pattern[int(sel_pos[1]), int(sel_pos[0])] = index + 4

for index, sel_pos in enumerate(  # crossbar 2
        [[31.0, 6.0], [28.0, 10.0], [25.0, 14.0], [22.0, 18.0], [19.0, 22.0], [16.0, 26.0], [13.0, 30.0]]):
    crossbar_pattern[int(sel_pos[1]), int(sel_pos[0])] = index + 4  # incremented by 4 to match with cargo map

crossbar_df = attach_cargo_handles_to_core_sequences(crossbar_pattern, crossbar_anti_map, core_plate, slat_type='X',
                                                     handle_side=2)
crossbar_df['Category'] = 4
crossbar_df['Handle Side'] = 'h2'
crossbar_df.sort_values(by=['Slat Pos. ID'], inplace=True)

# the actual crossbar is defined as a 1x32 array with the attachment staples on the H5 side and biotin staples on the H2 side
single_crossbar_pattern = np.ones((1, 32)) * -1
for index, pos in enumerate([0, 5, 10, 15, 20, 25, 30]):  # as defined by previous script
    single_crossbar_pattern[:, pos] = index + 11

single_crossbar_df = attach_cargo_handles_to_core_sequences(single_crossbar_pattern, crossbar_map, core_plate,
                                                            slat_type='X', handle_side=5)
single_crossbar_df['Category'] = 5
single_crossbar_df['Handle Side'] = 'h5'
########################################

########################################
# combines all patterns, add names and adds the extra biotin anchor strand
full_attachment_df = pd.concat((cdf, crossbar_df, single_crossbar_df))

full_attachment_df.replace({'Cargo ID': cargo_names}, inplace=True)
full_attachment_df['Name'] = full_attachment_df['Cargo ID'] + '_' + full_attachment_df[
    'Handle Side'] + '_cargo_handle_' + full_attachment_df['Slat Pos. ID'].astype(str)
full_attachment_df['Description'] = full_attachment_df['Handle Side'] + ' attachment for slat position ' + \
                                    full_attachment_df[
                                        'Slat Pos. ID'].astype(str) + ', with the ' + full_attachment_df[
                                        'Cargo ID'] + ' cargo strand.'
full_attachment_df.loc[-1] = [f'Biotin-{cargo_biotin}', '/5Biosg/ttt' + simpsons[cargo_biotin], -1, 6, 'N/A',
                              'biotin_anchor',
                              f'Complement for anti{cargo_biotin}, with biotin attached.']  # extra strand to attach to all cargo locations

print('Total new sequences required: %s' % len(full_attachment_df))
########################################

########################################
# generates new cargo plate or reads from file
if read_cargo_patterns_from_file:
    cargo_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1, cargo_plate_folder)
else:
    # exports sequences to a new plate
    generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder, 'new_cargo_strands.xlsx',
                                           restart_row_by_column='Category', data_type='2d_excel', plate_size=384)
    idt_plate = generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder,
                                                       'idt_order_new_cargo_strands.xlsx',
                                                       restart_row_by_column='Category', data_type='IDT_order',
                                                       plate_size=384)
    idt_plate.columns = ['well', 'name', 'sequence', 'description']
    cargo_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1,
                                 output_folder,
                                 pre_read_plate_dfs=[idt_plate])

nelson_plate = get_plateclass('AntiNelsonQuimbyPlate', nelson_quimby_antihandles,
                              cargo_plate_folder)
biotin_plate = get_plateclass('DirectBiotinPlate', h2_biotin_direct,
                              cargo_plate_folder)
########################################

########################################
# Generation of Echo Commands TODO: currently not in a function - how can I combine everything into a function without lots of fumbling around?

all_slats = {}
for x in x_slats:  # prepares slat classes in advance
    all_slats['X%s' % int(x)] = Slat('core_x_%s' % int(x), 'X')
for y in y_slats:
    all_slats['Y%s' % int(y)] = Slat('core_y_%s' % int(y), 'Y')

# TODO: this cannot be extended to non-square shapes in its current form!  Probably best to add position ID to slat array too
# basic crisscross and cargo handle assignment
for i in range(slat_array.shape[0]):
    for j in range(slat_array.shape[1]):

        x_cargo_val = crossbar_pattern[i, j]
        y_cargo_val = cargo_pattern[i, j]
        handle_val = handle_array[i, j]
        si = i + 1  # slats/handles are 1-indexed
        sj = j + 1

        # H5 assignment
        if handle_val == -1:  # no handle, just a blank staple
            sel_x_plate = core_plate
            sel_y_plate = core_plate
            handle_val = 0  # TODO: can this inconsistency be fixed?
        else:
            sel_x_plate = crisscross_x_plates
            sel_y_plate = crisscross_y_plates

        all_slats['Y%s' % sj].set_handle(si, 5,
                                         sel_y_plate.get_sequence(si, 5, handle_val),
                                         sel_y_plate.get_well(si, 5, handle_val),
                                         sel_y_plate.get_plate_name(si, 5, handle_val))
        all_slats['X%s' % si].set_handle(sj, 5,
                                         sel_x_plate.get_sequence(sj, 5, handle_val),
                                         sel_x_plate.get_well(sj, 5, handle_val),
                                         sel_x_plate.get_plate_name(sj, 5, handle_val))

        # H2 assignment
        if not isinstance(seed_plate.get_sequence(sj, 2, si), str):  # checks to see if the seed is present in this specific X location
            if x_cargo_val > 0:
                sel_x_plate = cargo_plate
                x_h2_id = x_cargo_val
            else:
                sel_x_plate = core_plate
                x_h2_id = 0
        else:
            sel_x_plate = seed_plate
            x_h2_id = si

        if y_cargo_val > 0:  # no cargo
            sel_y_plate = cargo_plate
            y_h2_id = y_cargo_val
        else:
            sel_y_plate = core_plate
            y_h2_id = 0

        all_slats['Y%s' % sj].set_handle(si, 2,
                                         sel_y_plate.get_sequence(si, 2, y_h2_id),
                                         sel_y_plate.get_well(si, 2, y_h2_id),
                                         sel_y_plate.get_plate_name())
        all_slats['X%s' % si].set_handle(sj, 2,
                                         sel_x_plate.get_sequence(sj, 2, x_h2_id),
                                         sel_x_plate.get_well(sj, 2, x_h2_id),
                                         sel_x_plate.get_plate_name())

# TODO: check transfer volume
crossbar_slat = Slat('crossbar_slat', 'X')
for i in range(32):
    if single_crossbar_pattern[0, i] == -1:
        sel_plate = core_plate
        cargo_id = 0
    else:
        sel_plate = cargo_plate
        cargo_id = single_crossbar_pattern[0, i]
    crossbar_slat.set_handle(i + 1, 5, sel_plate.get_sequence(i + 1, 5, cargo_id),
                             sel_plate.get_well(i + 1, 5, cargo_id), sel_plate.get_plate_name(i + 1, 5, cargo_id))

    # full biotin layer (anti-Nelson)
    crossbar_slat.set_handle(i + 1, 2,
                             nelson_plate.get_sequence(i + 1, 2, 'Nelson'),
                             nelson_plate.get_well(i + 1, 2, 'Nelson'),
                             nelson_plate.get_plate_name(i + 1, 2, 'Nelson'))

all_slats['crossbar'] = crossbar_slat
# final generation of commands
convert_slats_into_echo_commands(all_slats, 'optical_base_plate', output_folder, 'all_echo_commands_with_crossbars.csv')
########################################
# alternate design 1: nelson-biotin on the underside, with no crossbars
biotin_underside_pattern = np.zeros_like(crossbar_pattern)
biotin_underside_pattern[0, :] = 3
biotin_underside_pattern[-1, :] = 3

all_slats = {}
for x in x_slats:  # prepares slat classes in advance
    all_slats['X%s' % int(x)] = Slat('core_x_%s' % int(x), 'X')
for y in y_slats:
    all_slats['Y%s' % int(y)] = Slat('core_y_%s' % int(y), 'Y')

# TODO: this cannot be extended to non-square shapes in its current form!  Probably best to add position ID to slat array too
# basic crisscross and cargo handle assignment
for i in range(slat_array.shape[0]):
    for j in range(slat_array.shape[1]):

        x_cargo_val = biotin_underside_pattern[i, j]
        if x_cargo_val == 3:
            x_cargo_val = 'Nelson'
        y_cargo_val = cargo_pattern[i, j]
        handle_val = handle_array[i, j]
        si = i + 1  # slats/handles are 1-indexed
        sj = j + 1

        # H5 assignment
        if handle_val == -1:  # no handle, just a blank staple
            sel_x_plate = core_plate
            sel_y_plate = core_plate
            handle_val = 0  # TODO: can this inconsistency be fixed?
        else:
            sel_x_plate = crisscross_x_plates
            sel_y_plate = crisscross_y_plates

        all_slats['Y%s' % sj].set_handle(si, 5,
                                         sel_y_plate.get_sequence(si, 5, handle_val),
                                         sel_y_plate.get_well(si, 5, handle_val),
                                         sel_y_plate.get_plate_name(si, 5, handle_val))
        all_slats['X%s' % si].set_handle(sj, 5,
                                         sel_x_plate.get_sequence(sj, 5, handle_val),
                                         sel_x_plate.get_well(sj, 5, handle_val),
                                         sel_x_plate.get_plate_name(sj, 5, handle_val))

        # H2 assignment
        if not isinstance(seed_plate.get_sequence(sj, 2, si), str):  # checks to see if the seed is present in this specific X location
            if x_cargo_val != 0:
                sel_x_plate = nelson_plate
                x_h2_id = x_cargo_val
            else:
                sel_x_plate = core_plate
                x_h2_id = 0
        else:
            sel_x_plate = seed_plate
            x_h2_id = si

        if y_cargo_val > 0:  # no cargo
            sel_y_plate = cargo_plate
            y_h2_id = y_cargo_val
        else:
            sel_y_plate = core_plate
            y_h2_id = 0

        all_slats['Y%s' % sj].set_handle(si, 2,
                                         sel_y_plate.get_sequence(si, 2, y_h2_id),
                                         sel_y_plate.get_well(si, 2, y_h2_id),
                                         sel_y_plate.get_plate_name())
        all_slats['X%s' % si].set_handle(sj, 2,
                                         sel_x_plate.get_sequence(sj, 2, x_h2_id),
                                         sel_x_plate.get_well(sj, 2, x_h2_id),
                                         sel_x_plate.get_plate_name())

convert_slats_into_echo_commands(all_slats, 'optical_base_plate', output_folder, 'all_echo_commands_biotin_nelson_no_crossbars.csv')
########################################
# alternate design 2: direct biotins on the underside, no crossbars
biotin_underside_pattern = np.zeros_like(crossbar_pattern)
biotin_underside_pattern[:, 0] = 3
biotin_underside_pattern[:, -1] = 3

all_slats = {}
for x in x_slats:  # prepares slat classes in advance
    all_slats['X%s' % int(x)] = Slat('core_x_%s' % int(x), 'X')
for y in y_slats:
    all_slats['Y%s' % int(y)] = Slat('core_y_%s' % int(y), 'Y')

# TODO: this cannot be extended to non-square shapes in its current form!  Probably best to add position ID to slat array too
# basic crisscross and cargo handle assignment
for i in range(slat_array.shape[0]):
    for j in range(slat_array.shape[1]):

        x_cargo_val = biotin_underside_pattern[i, j]
        if x_cargo_val == 3:
            x_cargo_val = 'biotin'
        y_cargo_val = cargo_pattern[i, j]
        handle_val = handle_array[i, j]
        si = i + 1  # slats/handles are 1-indexed
        sj = j + 1

        # H5 assignment
        if handle_val == -1:  # no handle, just a blank staple
            sel_x_plate = core_plate
            sel_y_plate = core_plate
            handle_val = 0  # TODO: can this inconsistency be fixed?
        else:
            sel_x_plate = crisscross_x_plates
            sel_y_plate = crisscross_y_plates

        all_slats['Y%s' % sj].set_handle(si, 5,
                                         sel_y_plate.get_sequence(si, 5, handle_val),
                                         sel_y_plate.get_well(si, 5, handle_val),
                                         sel_y_plate.get_plate_name(si, 5, handle_val))
        all_slats['X%s' % si].set_handle(sj, 5,
                                         sel_x_plate.get_sequence(sj, 5, handle_val),
                                         sel_x_plate.get_well(sj, 5, handle_val),
                                         sel_x_plate.get_plate_name(sj, 5, handle_val))

        # H2 assignment
        if not isinstance(seed_plate.get_sequence(sj, 2, si), str):  # checks to see if the seed is present in this specific X location
            if x_cargo_val != 0:
                sel_x_plate = biotin_plate
                x_h2_id = x_cargo_val
            else:
                sel_x_plate = core_plate
                x_h2_id = 0
        else:
            sel_x_plate = seed_plate
            x_h2_id = si

        if y_cargo_val > 0:  # no cargo
            sel_y_plate = cargo_plate
            y_h2_id = y_cargo_val
        else:
            sel_y_plate = core_plate
            y_h2_id = 0

        all_slats['Y%s' % sj].set_handle(si, 2,
                                         sel_y_plate.get_sequence(si, 2, y_h2_id),
                                         sel_y_plate.get_well(si, 2, y_h2_id),
                                         sel_y_plate.get_plate_name())
        all_slats['X%s' % si].set_handle(sj, 2,
                                         sel_x_plate.get_sequence(sj, 2, x_h2_id),
                                         sel_x_plate.get_well(sj, 2, x_h2_id),
                                         sel_x_plate.get_plate_name())

convert_slats_into_echo_commands(all_slats, 'optical_base_plate', output_folder, 'all_echo_commands_direct_biotin_no_crossbars.csv')
