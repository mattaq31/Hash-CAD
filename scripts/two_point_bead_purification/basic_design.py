# this design implements a two-point bead purification system, which allows the megastructure to be purified using beads twice
import numpy as np
import pandas as pd
import os

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.core_functions.slat_design import generate_standard_square_slats, \
    attach_cargo_handles_to_core_sequences
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize, multi_rule_hamming
from crisscross.helper_functions.standard_sequences import simpsons_anti, simpsons
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import (octahedron_patterning_v1, cargo_plate_folder)
from crisscross.plate_mapping import get_plateclass, get_standard_plates

########################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/two_point_bead_purification/square_design_test'

create_dir_if_empty(output_folder)
np.random.seed(8)
read_handles_from_file = True
########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
crossbar_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
########################################
# Shape generation and crisscross handle optimisation
slat_array, _ = generate_standard_square_slats(32)
# optimize handles
if read_handles_from_file:
    handle_array = np.load(os.path.join(output_folder, 'true_mighty_29_square.npy'))
    result = multi_rule_hamming(slat_array, handle_array)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, max_rounds=3)
    np.savetxt(os.path.join(output_folder, 'optimized_handle_array.csv'), handle_array.squeeze().astype(np.int32),
               delimiter=',',
               fmt='%i')
########################################
# preparing handles for the purification slats

anchor_placement_array = np.zeros((32, 32))  # sequences will be placed on either end of the final set of slats
anchor_placement_array[16::2, 0] = 1
anchor_placement_array[16::2, 31] = 1


def combine_anchor_sequences(anchor_array, mega_anchor, design_id):
    # function to quickly combine sequences together for different designs
    anchor_df_h2 = attach_cargo_handles_to_core_sequences(anchor_array,
                                                          {1: mega_anchor},
                                                          core_plate, slat_type='X',
                                                          handle_side=2)

    anchor_df_h2['Name'] = 'Anchor-Wiggum_Flanders-' + anchor_df_h2['Slat Pos. ID'].astype(str) + '-H2-' + design_id
    anchor_df_h2['Description'] = 'Anchor Sequence (Wiggum Core, 10-base Flanders Toehold) on Slat Handle ' + \
                                  anchor_df_h2[
                                      'Slat Pos. ID'].astype(str) + ', H2, with design ID ' + design_id
    anchor_df_h5 = attach_cargo_handles_to_core_sequences(anchor_placement_array,
                                                          {1: mega_anchor},
                                                          core_plate, slat_type='X',
                                                          handle_side=5)

    anchor_df_h5['Name'] = 'Anchor-Wiggum_Flanders-' + anchor_df_h5['Slat Pos. ID'].astype(str) + '-H5-' + design_id
    anchor_df_h5['Description'] = 'Anchor Sequence (Wiggum Core, 10-base Flanders Toehold) on Slat Handle ' + \
                                  anchor_df_h5[
                                      'Slat Pos. ID'].astype(str) + ', H5, with design ID ' + design_id

    full_df = pd.concat((anchor_df_h2, anchor_df_h5))
    return full_df


# version 1 - toehold on 3' end of megastructure handle (facing outwards)
anchor_sequence_megastructure = simpsons_anti['Wiggum']
toehold_sequence = simpsons_anti['Flanders'][0:10]
anchor_sequence_megastructure_v1 = anchor_sequence_megastructure + toehold_sequence
anchor_sequence_bead = '/5Biosg/tttt' + simpsons['Wiggum']  # will not be attached to megastructure
invader_v1 = simpsons['Flanders'][-10:] + simpsons['Wiggum']  # will be used to cleave the megastructure off from the beads

# version 2 - toehold on 5' end of megastructure handle (facing inwards)
anchor_sequence_megastructure_v2 = toehold_sequence + anchor_sequence_megastructure
invader_v2 = simpsons['Wiggum'] + simpsons['Flanders'][-10:]   # will be used to cleave the megastructure off from the beads

# preparing non megastructure sequences
invader_dict_v1 = {'Name': ['Invader-Flanders_Wiggum-5prime'],
                'Description': [
                    'Invader sequence for cleaving purification slats.  '
                    'The core part contains the Wiggum sequence, while the toehold (on the 5 prime end) contains 10 bases from the Flanders sequence.'],
                'Sequence': [invader_v1]}

invader_dict_v2 = {'Name': ['Invader-Flanders_Wiggum-3prime'],
                'Description': [
                    'Invader sequence for cleaving purification slats.  '
                    'The core part contains the Wiggum sequence, while the toehold (on the 3 prime end) contains 10 bases from the Flanders sequence.'],
                'Sequence': [invader_v2]}

anchor_bead_dict = {'Name': ['Biotin-Bead-Wiggum'],
                    'Description': ['Biotinylated bead anchor sequence containing the full Wiggum sequence.'],
                    'Sequence': [anchor_sequence_bead]}

additional_dicts = [anchor_bead_dict, invader_dict_v1, invader_dict_v2]

# preparing megastructure sequences
mega_anchors_df_v1 = combine_anchor_sequences(anchor_placement_array, anchor_sequence_megastructure_v1, design_id='outer_toehold')
mega_anchors_df_v2 = combine_anchor_sequences(anchor_placement_array, anchor_sequence_megastructure_v2, design_id='inner_toehold')

# combining everything together
full_df = pd.concat((mega_anchors_df_v1, mega_anchors_df_v2))
for individual_seq_dict in additional_dicts:
    full_df = pd.concat((full_df, pd.DataFrame(individual_seq_dict)), ignore_index=True)

idt_plate = generate_new_plate_from_slat_handle_df(full_df, output_folder,
                                                   'idt_anchor_sequence_order.xlsx',
                                                   data_type='IDT_order',
                                                   plate_size=384)

########################################
# preparing seed placement
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
corner_seed_array = np.zeros((32, 32))
corner_seed_array[0:16, 0:5] = insertion_seed_array
########################################
megastructure = Megastructure(slat_array)
megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
megastructure.assign_seed_handles(corner_seed_array, seed_plate)
megastructure.assign_cargo_handles_with_array(anchor_placement_array, cargo_key={1: 'Purification Anchor'},
                                              layer='bottom')
# megastructure.create_standard_graphical_report(output_folder, colormap='Set1', cargo_colormap='Dark2')
