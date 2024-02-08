import numpy as np
import os
import pandas as pd
from crisscross.graphics.megastructures import generate_patterned_square_cco
from crisscross.core_functions.plate_handling import read_dna_plate_mapping, generate_new_plate_from_slat_handle_df
from crisscross.core_functions.slats import generate_standard_square_slats, \
    generate_handle_set_and_optimize, attach_cargo_handles_to_slats
from crisscross.helper_functions.standard_sequences import simpsons_anti, simpsons
from crisscross.helper_functions.plate_maps import slat_core, seed_core, plate_folder
from crisscross.core_functions.megastructure_composition import collate_design_print_echo_commands

# script to generate a new plate of cargo strands for the optical computer voxel attachment
if __name__ == '__main__':
    # cargo definitions
    cargo_1 = 'Bart'
    cargo_2 = 'Edna'
    cargo_biotin = 'Nelson'
    crossbar_linkages = ['Homer', 'Krusty', 'Lisa', 'Marge', 'Patty', 'Quimby', 'Smithers']

    crossbar_anti_map = {i+4: simpsons_anti[crossbar_linkages[i]][:10] for i in range(7)}
    crossbar_map = {i+11: simpsons[crossbar_linkages[i]][-10:] for i in range(7)}  # due to reverse complement system, need to take sequence from back

    crossbar_anti_names = {i+4: f'10mer-anti{crossbar_linkages[i]}' for i in range(7)}
    crossbar_names = {i+11: f'10mer-{crossbar_linkages[i]}' for i in range(7)}

    cargo_map = {1: simpsons_anti[cargo_1], 2: simpsons_anti[cargo_2], 3: simpsons_anti[cargo_biotin]}
    cargo_names = {1: f'anti{cargo_1}', 2: f'anti{cargo_2}', 3: f'anti{cargo_biotin}'}
    cargo_names = {**cargo_names, **crossbar_anti_names, **crossbar_names}

    output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_feb_2024'

    # get plate sequences
    core_slat_plate = read_dna_plate_mapping(os.path.join(plate_folder, slat_core + '.xlsx'))
    core_seed_plate = read_dna_plate_mapping(os.path.join(plate_folder, seed_core + '.xlsx'))

    # generate standard square array
    np.random.seed(8)
    slat_array, x_slats, y_slats = generate_standard_square_slats(32)

    # optimize handles
    handle_array = generate_handle_set_and_optimize(slat_array, x_slats, y_slats, unique_sequences=32,
                                                    min_hamming=28, max_rounds=300)

    # prepares cargo pattern
    cargo_pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
    cargo_df = attach_cargo_handles_to_slats(cargo_pattern, cargo_map, core_slat_plate, slat_type='y')
    cargo_df.sort_values(by=['Cargo ID'], inplace=True)
    cargo_df['Category'] = cargo_df['Cargo ID']
    cargo_df['Handle Side'] = 'h2'

    # prepares biotin pattern (full attachment to allow for later adjustment)
    biotin_pattern = np.ones((32, 32)) * 3
    biotin_df = attach_cargo_handles_to_slats(biotin_pattern, cargo_map, core_slat_plate, slat_type='x')
    biotin_df['Category'] = 3
    biotin_df['Handle Side'] = 'h2'

    # prepares crossbar attachment pattern (pre-made in another script)
    crossbar_pattern = np.zeros((32, 32))
    for index, sel_pos in enumerate([[21.0, 2.0], [18.0, 6.0], [15.0, 10.0], [12.0, 14.0], [9.0, 18.0], [6.0, 22.0], [3.0, 26.0]]):
        crossbar_pattern[int(sel_pos[1]), int(sel_pos[0])] = index + 4

    for index, sel_pos in enumerate([[31.0, 6.0], [28.0, 10.0], [25.0, 14.0], [22.0, 18.0], [19.0, 22.0], [16.0, 26.0], [13.0, 30.0]]):
        crossbar_pattern[int(sel_pos[1]), int(sel_pos[0])] = index + 4

    crossbar_df = attach_cargo_handles_to_slats(crossbar_pattern, crossbar_anti_map, core_slat_plate, slat_type='x')
    crossbar_df['Category'] = 4
    crossbar_df['Handle Side'] = 'h2'

    # single crossbar prep
    single_crossbar_pattern = np.ones((1, 32)) * -1
    for index, pos in enumerate([0, 5, 10, 15, 20, 25, 30]):
        single_crossbar_pattern[:, pos] = index + 11

    single_crossbar_df = attach_cargo_handles_to_slats(single_crossbar_pattern, crossbar_map, core_slat_plate, slat_type='x', handle_side='h5')
    single_crossbar_df['Category'] = 5
    single_crossbar_df['Handle Side'] = 'h5'

    # combines all patterns, add names and adds the extra biotin anchor strand
    full_attachment_df = pd.concat((cargo_df, biotin_df, crossbar_df, single_crossbar_df))
    full_attachment_df.replace({'Cargo ID': cargo_names}, inplace=True)
    full_attachment_df['Name'] = full_attachment_df['Cargo ID'] + '_' + full_attachment_df['Handle Side'] + '_cargo_handle_' + full_attachment_df['Slat Pos. ID'].astype(str)
    full_attachment_df['Description'] = full_attachment_df['Handle Side'] + ' attachment for slat position ' + full_attachment_df[
        'Slat Pos. ID'].astype(str) + ', with the ' + full_attachment_df['Cargo ID'] + ' cargo strand.'
    full_attachment_df.loc[-1] = [f'Biotin-{cargo_biotin}', '/5Biosg/ttt' + simpsons[cargo_biotin], -1, 6, 'N/A', 'biotin_anchor',
                                  f'Complement for anti{cargo_biotin}, with biotin attached.']  # extra strand to attach to all cargo locations

    print('Total new sequences required: %s' % len(full_attachment_df))

    # exports sequences to a new plate
    generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder, 'new_cargo_strands.xlsx',
                                           restart_row_by_column='Category', data_type='2d_excel', plate_size=384)
    idt_plate = generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder,
                                                       'idt_order_new_cargo_strands.xlsx',
                                                       restart_row_by_column='Category', data_type='IDT_order',
                                                       plate_size=384)

    # v1, x-slats empty
    combined_echo_df = collate_design_print_echo_commands(slat_array, x_slats, y_slats, handle_array, np.zeros((32, 32)),
                                                          cargo_pattern,
                                                          cargo_names, idt_plate, 'optical_slats',
                                                          output_folder, 'all_echo_commands_blank_bottom.csv')
    # v2, biotins directly attached to x-slats
    combined_echo_df = collate_design_print_echo_commands(slat_array, x_slats, y_slats, handle_array, biotin_pattern,
                                                          cargo_pattern,
                                                          cargo_names, idt_plate, 'optical_slats',
                                                          output_folder, 'all_echo_commands_biotin_bottom.csv')
    # v3, crossbars (with biotin) attached to x-slats
    combined_echo_df = collate_design_print_echo_commands(slat_array, x_slats, y_slats, handle_array, crossbar_pattern,
                                                          cargo_pattern,
                                                          cargo_names, idt_plate, 'optical_slats',
                                                          output_folder, 'all_echo_commands_crossbar_bottom.csv')

    # single crossbar - biotins on the H2 side and crossbar handles on the H5 side
    crossbar_array = np.zeros((1, 32, 2))
    crossbar_array[:, :, 0] = 1
    handle_array = np.ones((1, 32)) * -1
    combined_echo_df = collate_design_print_echo_commands(crossbar_array, [1], [], single_crossbar_pattern, np.zeros((1, 32)) * 3,
                                                          np.zeros((1, 32)),
                                                          cargo_names, idt_plate, 'optical_slats',
                                                          output_folder, 'all_echo_commands_single_crossbar.csv',
                                                          include_seed=False, cargo_bearing_h5=True)

# What's required for the crossbar(s)?
# positions of handles (check crossbar code for placement - perhaps can create a 32x32 array too?) - CREATE 32x32 ARRAY WITH POSITIONS OF THESE HANDLES - DONE
# sequence to use for the 7 crossbar positions (should it be identical for both or completely unique?) - USE 7 SIMPSONS SEQUENCES - DONE
# add an extra 2 slats as the crossbars, making sure to add the biotins to the bottom of each.  How to do this?  perhaps a new function that prints out an individual slat? - NEW FUNCTION NEEDED

# NEXT STEPS:
# prepare seed socket implementation - DONE
# prepare new sequences for the crossbar attachment - DONE
# Implement echo output system - DONE
# add sequences for 7nt handles - DONE
# Add crossbar - DONE
# re-check everything
# before preparing echo protocol, significantly increase the iterations for hamming optimisation...
