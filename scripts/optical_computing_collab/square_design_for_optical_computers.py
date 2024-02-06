import numpy as np
import os
from crisscross.graphics.megastructures import generate_patterned_square_cco
from crisscross.core_functions.plate_handling import read_dna_plate_mapping, generate_new_plate_from_slat_handle_df
from crisscross.core_functions.slats import generate_standard_square_slats, \
    generate_handle_set_and_optimize, attach_cargo_handles_to_slats
from crisscross.helper_functions.standard_sequences import simpsons_anti, simpsons
from crisscross.helper_functions.plate_maps import slat_core, seed_core, plate_folder


# quick script to generate a new plate of cargo strands for the optical computer voxel attachment
if __name__ == '__main__':

    output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_feb_2024'

    # get plate sequences
    core_slat_plate = read_dna_plate_mapping(os.path.join(plate_folder, slat_core + '.xlsx'))
    core_seed_plate = read_dna_plate_mapping(os.path.join(plate_folder, seed_core + '.xlsx'))

    # generate standard square array
    np.random.seed(8)
    base_array, x_slats, y_slats = generate_standard_square_slats(32)

    # optimize handles
    handle_array = generate_handle_set_and_optimize(base_array, x_slats, y_slats, unique_sequences=32,
                                                    min_hamming=28, max_rounds=5)

    # prepares cargo pattern
    cargo_map = {1: simpsons_anti['Bart'], 2: simpsons_anti['Edna'], 3: simpsons_anti['Flanders']}
    cargo_pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
    cargo_df = attach_cargo_handles_to_slats(cargo_pattern, cargo_map, core_slat_plate)

    # prepares biotin pattern (full attachment to allow for later adjustment)
    biotin_map = {3: simpsons_anti['Flanders']}  # biotins added to the 3' end (but not added directly here)
    biotin_pattern = generate_patterned_square_cco('biotin_patterning')
    biotin_df = attach_cargo_handles_to_slats(biotin_pattern, cargo_map, core_slat_plate)

    # combines all patterns and adds the extra biotin strand
    full_attachment_df = cargo_df.join(biotin_df)
    full_attachment_df.columns = ['antiBart', 'antiEdna', 'antiFlanders']
    full_attachment_df.loc['EXTRA'] = {'antiBart': np.nan, 'antiEdna': np.nan, 'antiFlanders': '/5Biosg/ttt' + simpsons['Flanders']}  # extra strand to attach to all cargo locations

    # creates a name dataframe (optional) TODO: this is a bit convoluted and can muddle the nans part - how to simplify?
    names_df = full_attachment_df.copy()
    names_df['antiBart'] = 'antiBart_handle_' + names_df.index.astype(str)
    names_df['antiEdna'] = 'antiEdna_handle_' + names_df.index.astype(str)
    names_df['antiFlanders'] = 'antiFlanders_handle_' + names_df.index.astype(str)
    names_df['antiFlanders']['EXTRA'] = "Flanders_5'_biotin"

    print('Total new sequences required: %s' % full_attachment_df.count().sum())

    # exports sequences to a new plate
    generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder, 'new_cargo_strands.xlsx',
                                           names_df=names_df, data_type='2d_excel', plate_size=384)
    generate_new_plate_from_slat_handle_df(full_attachment_df, output_folder, 'idt_order_new_cargo_strands.xlsx',
                                           names_df=names_df, data_type='IDT_order', plate_size=384)



# NEXT STEPS:
# Implement echo output system
# prepare seed socket implementation
# add sequences for 7nt handles
# Add crossbar - DONE
# add biotins to crossbar -
# re-check everything
