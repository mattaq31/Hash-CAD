from core_functions.plate_handling import export_standardized_plate_sheet
from plate_mapping import get_plateclass, seed_plug_plate_all_8064, seed_plate_folder, flat_staple_plate_folder, \
    slat_core_latest
import numpy as np

all_8064_seed_plugs = get_plateclass('HashCadPlate', seed_plug_plate_all_8064, seed_plate_folder).plates[0]
flat_plate = get_plateclass('HashCadPlate', slat_core_latest, flat_staple_plate_folder)

new_plate_1 = get_plateclass('HashCadPlate', 'triple_seed_plate', '/Users/matt/Desktop')
new_plate_db = get_plateclass('HashCadPlate', 'rev_seed_plate', '/Users/matt/Desktop')

# prepare pattern - A13 - P17
pattern = []
rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
columns = [13, 14, 15, 16, 17]
for r in rows:
    for c in columns:
        pattern.append(f'{r}{c}')

# extract all seed sequences into a dict
seed_dict = []
seed_set = set()
for index, row in all_8064_seed_plugs.iterrows():
    if len(seed_dict) == 80:
        break
    if not isinstance(row['name'], str) or row['name'].split('-')[1] in seed_set:
        continue
    seed_set.add(row['name'].split('-')[1])
    seed_dict.append([row['name'].split('-')[1], row['sequence'].split('tt')[-1]])

# loop through all seqs and slat positions and place into original dataframe

slat_positions = [28, 29, 30, 31, 32]
for index, well in enumerate(pattern):
    seed_cargo_seq = seed_dict[index][1]
    seed_cargo_name = seed_dict[index][0]
    slat_position = slat_positions[index % len(slat_positions)]
    combined_seed_seq = flat_plate.get_sequence('FLAT', slat_position, 2, 'BLANK') + 'tt' + seed_cargo_seq
    all_8064_seed_plugs.loc[all_8064_seed_plugs['well'] == well] = [well, f'SEED-{seed_cargo_name}-h2-position_{slat_position}', combined_seed_seq, f'Seed Handle For Slat Position {slat_position}, Side h2, 8064 Seed ID {seed_cargo_name}', 500.0]

# copy the dataframe, and replace all rows with nans
double_barrel_seed_plug_plate = all_8064_seed_plugs.copy()
double_barrel_seed_plug_plate.loc[:, double_barrel_seed_plug_plate.columns != 'well'] = np.nan

# prepare pattern - A13 - P17
column_sets = [[1, 2, 3, 4, 5], [7, 8, 9, 10, 11]]
slat_position_sets = [[5, 4, 3, 2, 1], [32, 31, 30, 29, 28]]

for columns, slat_positions in zip(column_sets, slat_position_sets):
    pattern = []
    for r in rows:
        for c in columns:
            pattern.append(f'{r}{c}')

    for index, well in enumerate(pattern):
        seed_cargo_seq = seed_dict[index][1]
        seed_cargo_name = seed_dict[index][0]
        slat_position = slat_positions[index % len(slat_positions)]
        combined_seed_seq = flat_plate.get_sequence('FLAT', slat_position, 2, 'BLANK') + 'tt' + seed_cargo_seq
        double_barrel_seed_plug_plate.loc[all_8064_seed_plugs['well'] == well] = [well, f'SEED-{seed_cargo_name}-h2-position_{slat_position}', combined_seed_seq, f'Seed Handle For Slat Position {slat_position}, Side h2, 8064 Seed ID {seed_cargo_name}', 500.0]


# delete any rows that have a nan in them
all_8064_seed_plugs = all_8064_seed_plugs.dropna().reset_index(drop=True)
double_barrel_seed_plug_plate = double_barrel_seed_plug_plate.dropna().reset_index(drop=True)

# export new dataframe as new plate
export_standardized_plate_sheet(all_8064_seed_plugs, '/Users/matt/Desktop', 'triple_seed_plate.xlsx')
export_standardized_plate_sheet(double_barrel_seed_plug_plate, '/Users/matt/Desktop', 'rev_seed_plate.xlsx')
