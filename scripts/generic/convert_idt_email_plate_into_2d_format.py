from collections import defaultdict
from string import ascii_uppercase

import pandas as pd

from crisscross.core_functions.plate_handling import add_data_to_plate_df
from crisscross.plate_mapping.plate_constants import seed_plug_plate_all, flat_staple_plate_folder
from crisscross.plate_mapping import get_plateclass



input_filename = '/Users/matt/Downloads/20250110_P3621_8064gridironplugs_v1/250110_SW_IDT_email_P3621.xlsx'
output_filename = '/Users/matt/Desktop/p8064_center_seed.xlsx'

center_seed_plate = get_plateclass('CombinedSeedPlugPlate', seed_plug_plate_all, flat_staple_plate_folder).plates[0]
center_seed_plate = center_seed_plate[~center_seed_plate['description'].str.contains('Edge', na=False)]

input_data = pd.read_excel(input_filename, engine="calamine")
input_data = input_data[input_data['Sequence'].notnull()]

center_seed_plate['sequence'] = input_data['Sequence'].values
center_seed_plate['description'] = center_seed_plate['description'] + ' (P8064 Seed)'

seq_dict = defaultdict(dict)
name_dict = defaultdict(dict)
desc_dict = defaultdict(dict)
for index, row in center_seed_plate.iterrows():
    seq_dict[row['well'][0]][row['well'][1:]] = row['sequence']
    name_dict[row['well'][0]][row['well'][1:]] = row['name']
    desc_dict[row['well'][0]][row['well'][1:]] = row['description']

seq_dict = add_data_to_plate_df([a for a in ascii_uppercase[:16]], 24, seq_dict)
name_dict = add_data_to_plate_df([a for a in ascii_uppercase[:16]], 24, name_dict)
desc_dict = add_data_to_plate_df([a for a in ascii_uppercase[:16]], 24, desc_dict)

with pd.ExcelWriter(output_filename) as writer:
    seq_dict.to_excel(writer, sheet_name='Sequences')
    name_dict.to_excel(writer, sheet_name='Names')
    desc_dict.to_excel(writer, sheet_name='Descriptions')
