from collections import defaultdict
import pandas as pd
from string import ascii_uppercase

from crisscross.core_functions.plate_handling import export_standardized_plate_sheet
from crisscross.plate_mapping.plate_constants import seed_plug_plate_all_8064, seed_plate_folder, flat_staple_plate_folder, slat_core_latest
from crisscross.plate_mapping import get_plateclass

edge_seed_plate = get_plateclass('HashCadPlate', seed_plug_plate_all_8064, seed_plate_folder)
flat_staple_plate = get_plateclass('HashCadPlate', slat_core_latest, flat_staple_plate_folder)

new_plate_dict = defaultdict(list)
all_staple_count = 1

# prepare seed sequences
full_seed_dict = {}
for key, seq in edge_seed_plate.sequences.items():
    seed_cargo_val = key[-1]
    seed_seq = seq.split('tt')[-1]
    if seed_cargo_val not in full_seed_dict:
        full_seed_dict[seed_cargo_val] = seed_seq

new_plate_dict = defaultdict(list)

row_tracker = 0
col_range = list(range(1,6))
for row in range(1,17):
    # generate slate positions and cargo ids
    odd_row = (row % 2) == 1
    seed_cargo_list = [ f'{i}_{row}' for i in range(1,6)]
    if odd_row:
        pos_list = list(range(6,11))
    else:
        pos_list = list(range(27,22,-1))

    # arrange layout on 96-well plate
    plate_letter = ascii_uppercase[row_tracker]
    well_list = [plate_letter + str(i) for i in col_range]
    if plate_letter == 'H':
        row_tracker = 0
        col_range = list(range(7,12))
    else:
        row_tracker += 1

    for pos, seed_cargo, well in zip(pos_list, seed_cargo_list, well_list):
        flat_seq = flat_staple_plate.sequences[('FLAT', pos, 2,'BLANK')]
        seed_seq = full_seed_dict[seed_cargo]
        full_seq = flat_seq + 'tt' + seed_seq
        new_plate_dict['name'].append(f'SEED-{seed_cargo}-h2-position_{pos}')
        new_plate_dict['sequence'].append(full_seq)
        new_plate_dict['well'].append(well)
        new_plate_dict['description'].append(f'Seed Handle For Slat Position {pos}, Side h2, 8064 Seed ID {seed_cargo}')
        new_plate_dict['concentration'].append(500)

# TODO: generate a plate layout to place inside P3643
# TODO: What to do if there are any duplicate wells in the future?

pd_df = pd.DataFrame.from_dict(new_plate_dict)
export_standardized_plate_sheet(pd_df, '/Users/matt/Desktop', 'db_seed_plate.xlsx', plate_size=96)
