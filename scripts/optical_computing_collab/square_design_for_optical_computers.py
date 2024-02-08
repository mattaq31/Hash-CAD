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

    crossbar_anti_map = {i: simpsons_anti[crossbar_linkages[i]][:10] for i in range(7)}
    crossbar_map = {i: simpsons[crossbar_linkages[i]][-10:] for i in range(7)}  # due to reverse complement system, need to take sequence from back

    cargo_map = {1: simpsons_anti[cargo_1], 2: simpsons_anti[cargo_2], 3: simpsons_anti[cargo_biotin]}
    cargo_names = {1: f'anti{cargo_1}', 2: f'anti{cargo_2}', 3: f'anti{cargo_biotin}'}

    output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_feb_2024'

    # get plate sequences
    core_slat_plate = read_dna_plate_mapping(os.path.join(plate_folder, slat_core + '.xlsx'))
    core_seed_plate = read_dna_plate_mapping(os.path.join(plate_folder, seed_core + '.xlsx'))

    # generate standard square array
    np.random.seed(8)
    slat_array, x_slats, y_slats = generate_standard_square_slats(32)

    # optimize handles
    handle_array = generate_handle_set_and_optimize(slat_array, x_slats, y_slats, unique_sequences=32,
                                                    min_hamming=28, max_rounds=1)

    # prepares cargo pattern
    cargo_pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
    cargo_df = attach_cargo_handles_to_slats(cargo_pattern, cargo_map, core_slat_plate, slat_type='y')

    # prepares biotin pattern (full attachment to allow for later adjustment)
    biotin_pattern = np.ones((32, 32)) * 3
    biotin_df = attach_cargo_handles_to_slats(biotin_pattern, cargo_map, core_slat_plate, slat_type='x')

    # combines all patterns, add names and adds the extra biotin anchor strand
    full_attachment_df = pd.concat((cargo_df, biotin_df))
    full_attachment_df.replace({'Cargo ID': cargo_names}, inplace=True)
    full_attachment_df['Name'] = full_attachment_df['Cargo ID'] + '_h2_cargo_handle_' + full_attachment_df['Slat Pos. ID'].astype(
        str)
    full_attachment_df['Description'] = 'H2 attachment for slat position ' + full_attachment_df[
        'Slat Pos. ID'].astype(str) + ', with the ' + full_attachment_df['Cargo ID'] + ' cargo strand.'
    full_attachment_df.loc[-1] = [f'Biotin-{cargo_biotin}', '/5Biosg/ttt' + simpsons[cargo_biotin], -1, 'biotin_anchor',
                                  f'Complement for anti{cargo_biotin}, with biotin attached.']  # extra strand to attach to all cargo locations

    print('Total new sequences required: %s' % len(full_attachment_df))

    # exports sequences to a new plate
    generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder, 'new_cargo_strands.xlsx',
                                           restart_row_by_column='Cargo ID', data_type='2d_excel', plate_size=384)
    idt_plate = generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder,
                                                       'idt_order_new_cargo_strands.xlsx',
                                                       restart_row_by_column='Cargo ID', data_type='IDT_order',
                                                       plate_size=384)

    # v1, biotins directly attached to x-slats - adjust the empty array as necessary to add more biotin handles
    combined_echo_df = collate_design_print_echo_commands(slat_array, x_slats, y_slats, handle_array, np.zeros((32, 32)),
                                                          cargo_pattern,
                                                          cargo_names, idt_plate, 'optical_slats',
                                                          output_folder, 'all_echo_commands.csv')
    # v2, crossbars attached to x-slats, with biotins attached to the crossbars
    # TODO: add function for this + new function for including crossbar in echo handling

# What's required for the crossbar(s)?
# positions of handles (check crossbar code for placement - perhaps can create a 32x32 array too?) - CREATE 32x32 ARRAY WITH POSITIONS OF THESE HANDLES
# sequence to use for the 7 crossbar positions (should it be identical for both or completely unique?) - USE 7 SIMPSONS SEQUENCES
# add an extra 2 slats as the crossbars, making sure to add the biotins to the bottom of each.  How to do this?  perhaps a new function that prints out an individual slat? - NEW FUNCTION NEEDED

# NEXT STEPS:
# prepare seed socket implementation - DONE
# prepare new sequences for the crossbar attachment - IN PROGRESS
# Implement echo output system - DONE
# add sequences for 7nt handles - DONE
# Add crossbar - DONE
# re-check everything
