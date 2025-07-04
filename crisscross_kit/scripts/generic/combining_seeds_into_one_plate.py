# combines both common seeds into one plate, with a more readable format that precisely matches the organisation of the seeds themselves
from collections import defaultdict
import pandas as pd

from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.plate_mapping.plate_constants import seed_plug_plate_corner, flat_staple_plate_folder, seed_plug_plate_center
from crisscross.plate_mapping import get_plateclass

edge_seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, flat_staple_plate_folder)
center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, flat_staple_plate_folder)
new_plate_dict = defaultdict(list)
all_staple_count = 1

edge_keys = list(edge_seed_plate.wells.keys())
center_keys = list(center_seed_plate.wells.keys())
total_count = 80
seed_jump_count = 5
category_count = defaultdict(int)


# these convoluted logic pieces are intended to automate placing the seed into the plate in specific human-readable patterns.
# In this case, the goal was to have the seed occupy 5 columns and 16 rows, mirroring its actual positioning in a megastructure
def fill_dict(key, plate, name, dict_to_fill, category):
    global all_staple_count, category_count
    description = f'{name} handle for slat position {key[0]}, seed ID {key[2]}-{category_count[(name, key[2])] + 1}'
    standardized_name = f'ID-{key[2]}_h2_position-{key[0]}'
    # dict_to_fill['Name'].append(f'Oligo{all_staple_count}') # use this to obfuscate name when ordering
    dict_to_fill['Name'].append(standardized_name)
    dict_to_fill['Sequence'].append(plate.sequences[key])
    dict_to_fill['Description'].append(description)
    dict_to_fill['Category'].append(f'Group-{category}')
    category_count[(name, key[2])] += 1

for i in range(0, total_count, seed_jump_count):
    category = (i // seed_jump_count) + 1
    for key in edge_keys[i:i+seed_jump_count]:
        fill_dict(key, edge_seed_plate, 'Edge Seed', new_plate_dict, category)
        all_staple_count += 1

    new_plate_dict['Name'].append('SKIP')
    new_plate_dict['Sequence'].append('SKIP')
    new_plate_dict['Description'].append('SKIP')
    new_plate_dict['Category'].append(f'Group-{category}')

    for key in center_keys[i:i+seed_jump_count]:
        fill_dict(key, center_seed_plate, 'Center Seed', new_plate_dict, category)
        all_staple_count += 1

new_plate_df = pd.DataFrame.from_dict(new_plate_dict)

# both an IDT order and a more human-readable format generated here
generate_new_plate_from_slat_handle_df(new_plate_df,
                                       '/Users/matt/Desktop',
                                       'combined_seeds_plate_2d.xlsx',
                                       restart_row_by_column='Category',
                                       data_type='2d_excel', plate_size=384)

generate_new_plate_from_slat_handle_df(new_plate_df,
                                       '/Users/matt/Desktop',
                                       'combined_seeds_plate.xlsx',
                                       restart_row_by_column='Category',
                                       data_type='IDT_order', plate_size=384)
