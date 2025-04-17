from string import ascii_uppercase

import pandas as pd
import os
from crisscross.core_functions.plate_handling import add_data_to_plate_df
from crisscross.plate_mapping import get_plateclass, slat_core, core_plate_folder
from collections import defaultdict

output_folder = '/Users/matt/Desktop'
output_file = 'src_009_idt_form.xlsx'
output_2d_file = 'src_009_source_max.xlsx'

src_002 = get_plateclass('ControlPlate', slat_core, core_plate_folder)
src_002_df = src_002.plates[0]

src_002_df_h2 = src_002_df.iloc[:32].copy()
src_002_df_h2['name'] = 'control_h2_pos' + src_002_df_h2['name'].astype(str).str.split('-').str[1]# now the next 16 rows
src_002_df_h2['description'] = 'control staple, h2, position ' + src_002_df_h2['name'].astype(str).str.split('pos').str[-1]

src_002_df_h5 = src_002_df.iloc[32:64].copy()
src_002_df_h5['name'] = 'control_h5_pos' + (src_002_df_h5['name'].astype(str).str.split('-').str[1].astype(int) - 32).astype(str)
src_002_df_h5['description'] = 'control staple, h5, position ' + src_002_df_h5['name'].astype(str).str.split('pos').str[-1]

seq_dict = defaultdict(dict)
name_dict = defaultdict(dict)
desc_dict = defaultdict(dict)
idt_dict = defaultdict(dict)
idt_order_dict = defaultdict(list)

for g_index, group in enumerate([src_002_df_h2.iloc[0:16], src_002_df_h2.iloc[16:32], src_002_df_h5.iloc[0:16], src_002_df_h5.iloc[16:32]]):
    output_letters = ascii_uppercase[g_index * 4:g_index * 4 + 4]
    for index, row in group.iterrows():
        updated_column = str(int(row['well'][1:]) + 4)
        for l_index, l in enumerate(output_letters):
            seq_dict[l][updated_column] = row['sequence']
            name_dict[l][updated_column] = row['name']
            desc_dict[l][updated_column] = row['description'] + f', duplicate {l_index+1}'
            idt_order_dict['WellPosition'].append(l+updated_column)
            idt_order_dict['Name'].append(row['name'])
            idt_order_dict['Sequence'].append(row['sequence'])
            idt_order_dict['Notes'].append(row['description'] + f', duplicate {l_index+1}')

seq_df = add_data_to_plate_df([a for a in ascii_uppercase[:16]], 24, seq_dict)
name_df = add_data_to_plate_df([a for a in ascii_uppercase[:16]], 24, name_dict)
desc_df = add_data_to_plate_df([a for a in ascii_uppercase[:16]], 24, desc_dict)


with pd.ExcelWriter(os.path.join(output_folder, output_2d_file)) as writer:
    seq_df.to_excel(writer, sheet_name='Sequences')
    name_df.to_excel(writer, sheet_name='Names')
    desc_df.to_excel(writer, sheet_name='Descriptions')

output_df = pd.DataFrame.from_dict(idt_order_dict, orient='columns')
with pd.ExcelWriter(os.path.join(output_folder, output_file)) as writer:
    output_df.to_excel(writer, sheet_name='src_009', index=False)
