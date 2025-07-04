import copy
from itertools import product

from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_plateclass
import os
from crisscross.plate_mapping.plate_constants import (flat_staple_plate_folder, crisscross_h5_handle_plates,
                                                      assembly_handle_plate_folder, plate384,
                                                      crisscross_h2_handle_plates, slat_core,
                                                      crisscross_not_ordered_h2_handle_plates)
from collections import defaultdict
import pandas as pd
from string import ascii_uppercase

# These plates contain all the sequences for the current assembly handle system (just for comparison purposes)
crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                assembly_handle_plate_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])

crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                            crisscross_h5_handle_plates[0:3],
                                            assembly_handle_plate_folder, plate_slat_sides=[5, 5, 5])

crisscross_handle_x_h2_plates = get_plateclass('CrisscrossHandlePlates',
                                               crisscross_not_ordered_h2_handle_plates,
                                               os.path.join(assembly_handle_plate_folder, 'not ordered'),
                                               plate_slat_sides=[5, 5, 5])

# reads in Katzi's sequences
with open(os.path.join('.', 'TT_no_crosscheck96to104_64_sequence_pairs_flipped.txt'), 'r') as f:
    new_raw_handles = [line.strip() for line in f]
    new_handles = [i.split('\t')[0] for i in new_raw_handles]
    new_antihandles = [i.split('\t')[1] for i in new_raw_handles]

# read in and separate core H2/H5 sequences
core_plate = get_plateclass('ControlPlate', slat_core, flat_staple_plate_folder)
new_plates = defaultdict(list)
core_h2_sequences = [core_plate.sequences[i + 1, 2, 0] for i in range(32)]
core_h5_sequences = [core_plate.sequences[i + 1, 5, 0] for i in range(32)]

# prepare naming scheme
slat_side_labels = ['H5', 'H2']
handle_type_labels = ['handles', 'antihandles']
post_nominal = 'MA_CCV2'
plate_number_start = 3649
seq_set_size = 32
set_count = len(new_handles) // seq_set_size
plate_size = len(plate384)

# arrange combinations here since William will only be ordering a subset of plates at the beginning
all_plate_combos = list(product(slat_side_labels, handle_type_labels))
all_plate_combos = [all_plate_combos[0]] + [all_plate_combos [-1]] + [all_plate_combos[1]] + [all_plate_combos[2]]

for helix_side, handle_type in all_plate_combos:

    # library split into two sets of 32 sequences to facilitate ordering
    for set in range(set_count):
        # extract sequences according to selected combinations
        if handle_type == 'handles':
            set_sequences = new_handles[set * seq_set_size:(set + 1) * seq_set_size]
        else:
            set_sequences = new_antihandles[set * seq_set_size:(set + 1) * seq_set_size]
        if helix_side == 'H5':
            core_set_sequences = core_h5_sequences
        else:
            core_set_sequences = core_h2_sequences

        orig_plate_start = copy.copy(plate_number_start)
        plate_pos_id = 1
        # iterate through all possible helix positions and library sequences
        for helix_position in range(len(core_set_sequences)):
            for seq_num, seq in enumerate(set_sequences):
                # consistent plate naming scheme
                plate_name = f'P{plate_number_start}_MA_{helix_side}_{handle_type}_S{set + 1}{ascii_uppercase[plate_number_start - orig_plate_start]}'

                # william won't be ordering these first
                if (helix_side == 'H5' and handle_type == 'antihandles') or (helix_side == 'H2' and handle_type == 'handles'):
                    plate_name = plate_name.replace(plate_name.split('_')[0], 'PNOT-ORDERED')

                # actual sequence composed of core handle, tt and the library 7-mer
                final_seq = core_set_sequences[helix_position] + 'tt' + seq
                descriptor = 'KZ Assembly %s %d, on core seq %d of 6hb %s' % (
                handle_type[:-1], (set * seq_set_size) + seq_num + 1, helix_position, helix_side)

                # naming scheme matches old system (unfortunately, slat is 0-based while library is 1-based)
                name = 'KZ_%s_%s_n%s_k%s' % (
                helix_side, handle_type[:-1], helix_position, (set * seq_set_size) + seq_num + 1)

                new_plates[plate_name].append([final_seq, descriptor, name])

                # updates plate when reaching threshold of 384
                plate_pos_id += 1
                if plate_pos_id == plate_size + 1:
                    plate_number_start += 1
                    plate_pos_id = 1

        plate_number_start += 1

# converts each plate into an output file for reading and ordering
output_dir = os.path.join('/Users/matt/Desktop', 'new_plates')
create_dir_if_empty(output_dir)
for key, val in new_plates.items():
    plate = pd.DataFrame(val, columns=['Sequence', 'Name', 'Description'])
    generate_new_plate_from_slat_handle_df(plate, '/Users/matt/Desktop/new_plates', '%s.xlsx' % key,
                                           data_type='2d_excel')
    if 'NOT-ORDERED' not in key:
        generate_new_plate_from_slat_handle_df(plate, '/Users/matt/Desktop/new_plates', 'IDT_ORDER_%s.xlsx' % key,
                                               data_type='IDT_order', plate_name = key.split('_')[0])
        generate_new_plate_from_slat_handle_df(plate, '/Users/matt/Desktop/new_plates', 'IDT_ORDER_SCRAMBLED_%s.xlsx' % key,
                                               data_type='IDT_order', scramble_names=True, plate_name = key.split('_')[0])

# quickly checks to see if dataframe integrity is maintained with plate loading system
crisscross_handle_plates = get_plateclass('CrisscrossHandlePlates',
                                          list(new_plates.keys())[0:6] + list(new_plates.keys())[12:18],
                                          output_dir,
                                          plate_slat_sides=[5] * 6 + [2] * 6)

crisscross_antihandle_plates = get_plateclass('CrisscrossHandlePlates',
                                              list(new_plates.keys())[6:12] + list(new_plates.keys())[18:],
                                              output_dir,
                                              plate_slat_sides=[5] * 6 + [2] * 6)
