from collections import defaultdict
from string import ascii_uppercase

from crisscross.plate_mapping.plate_constants import simpsons_mixplate_antihandles, cargo_plate_folder
from crisscross.plate_mapping import get_plateclass
import pandas as pd
import os

output_folder = '/Users/matt/Desktop'
output_file = 'src_007_refill.xlsx'
cargo_replenish = ['Bart','Edna']

src_007 = get_plateclass('GenericPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

idt_order_dict = defaultdict(list)
column_start = 2
row_track = 0
col_track = 0
for cargo in cargo_replenish:
    row = ascii_uppercase[row_track]
    for i in range(32):
        col_track += 1
        well = row + str(col_track + column_start)
        seq = src_007.get_sequence(i+1, 5, f'anti{cargo}')
        name = f'anti{cargo}_h5_pos_{i+1}'
        idt_order_dict['WellPosition'].append(well)
        idt_order_dict['Name'].append(name)
        idt_order_dict['Sequence'].append(seq)
        idt_order_dict['Notes'].append('')
        if ((i+1) % 8) == 0:
            row_track += 1
            row = ascii_uppercase[row_track]
            col_track -= 8

output_df = pd.DataFrame.from_dict(idt_order_dict, orient='columns')
with pd.ExcelWriter(os.path.join(output_folder, output_file)) as writer:
    output_df.to_excel(writer, sheet_name='src_007_refill', index=False)
