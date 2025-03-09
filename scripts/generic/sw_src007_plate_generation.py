from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.helper_functions.standard_sequences import simpsons_anti
from crisscross.plate_mapping.plate_constants import (slat_core, core_plate_folder, simpsons_mixplate_antihandles)
from crisscross.plate_mapping import get_plateclass
from collections import defaultdict
import pandas as pd


output_folder = '/Users/matt/Desktop'
cargo_names = ['Nelson', 'Quimby', 'Bart', 'Edna']
cargo = [simpsons_anti[c] for c in cargo_names]
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
seq_dict = defaultdict(list)

for cargo_seq, cargo_id in zip(cargo, cargo_names):
    if cargo_id in ['Nelson', 'Quimby']:
        for i in range(1, 33):
            if i < 17:
                category = f'{cargo_id}_H2_1'
            else:
                category = f'{cargo_id}_H2_2'
            core_sequence = core_plate.get_sequence(i, 2, 0)
            seq_dict['Name'].append(f'anti{cargo_id}_h2_position_{i}')
            seq_dict['Description'].append(f'anti-{cargo_id} sequence handle attached to the H2 side of position {i}, with a TT flexible linker.')
            seq_dict['Sequence'].append(core_sequence + 'tt' + cargo_seq)
            seq_dict['Category'].append(category)
            seq_dict['Slat Pos. ID'].append(i)

    for i in range(1, 33):
        if i < 17:
            category = f'{cargo_id}_H5_1'
        else:
            category = f'{cargo_id}_H5_2'
        core_sequence = core_plate.get_sequence(i, 5, 0)
        if cargo_id != 'Quimby':
            seq_dict['Name'].append(f'anti{cargo_id}_h5_position_{i}')
            seq_dict['Description'].append(f'anti-{cargo_id} sequence handle attached to the H5 side of position {i}, with a TT flexible linker.')
            seq_dict['Sequence'].append(core_sequence + 'tt' + cargo_seq)
            seq_dict['Category'].append(category)
            seq_dict['Slat Pos. ID'].append(i)
        else:
            seq_dict['Name'].append(f'')
            seq_dict['Description'].append(f'')
            seq_dict['Sequence'].append('')
            seq_dict['Category'].append(category)
            seq_dict['Slat Pos. ID'].append('')

seq_df = pd.DataFrame.from_dict(seq_dict)

generate_new_plate_from_slat_handle_df(seq_df, output_folder, 'sw_src007_nelson_quimby_bart_edna.xlsx',
                                       restart_row_by_column='Category', data_type='2d_excel', plate_size=384)

idt_plate = generate_new_plate_from_slat_handle_df(seq_df, output_folder,
                                                   'sw_src007_nelson_quimby_bart_edna_idt_order.xlsx',
                                                   restart_row_by_column='Category', data_type='IDT_order',
                                                   plate_size=384)

idt_plate.columns = ['well', 'name', 'sequence', 'description']
cargo_plate = get_plateclass('SimpsonsMixPlate', simpsons_mixplate_antihandles,
                             output_folder,
                             pre_read_plate_dfs=[idt_plate])
