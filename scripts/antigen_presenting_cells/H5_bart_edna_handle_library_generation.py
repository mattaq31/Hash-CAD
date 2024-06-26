from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.helper_functions.standard_sequences import simpsons_anti
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, simpsons_mixplate_antihandles)
from crisscross.plate_mapping import get_plateclass
from collections import defaultdict
import pandas as pd


output_folder = '/Users/matt/Desktop'
cargo_names = ['Bart', 'Edna']
cargo = [simpsons_anti[cargo_names[0]], simpsons_anti[cargo_names[1]]]
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
seq_dict = defaultdict(list)

for cargo_seq, cargo_id in zip(cargo, cargo_names):
    for i in range(1, 33):
        core_sequence = core_plate.get_sequence(i, 5, 0)
        seq_dict['Name'].append(f'anti{cargo_id}_h5_position_{i}')
        seq_dict['Description'].append(f'anti-{cargo_id} sequence handle attached to the H5 side of position {i}, with a TT flexible linker.')
        seq_dict['Sequence'].append(core_sequence + 'tt' + cargo_seq)
        seq_dict['Category'].append(cargo_id)
        seq_dict['Slat Pos. ID'].append(i)

seq_df = pd.DataFrame.from_dict(seq_dict)

generate_new_plate_from_slat_handle_df(seq_df, output_folder, 'new_cargo_strands.xlsx',
                                       restart_row_by_column='Category', data_type='2d_excel', plate_size=96)

idt_plate = generate_new_plate_from_slat_handle_df(seq_df, output_folder,
                                                   'idt_order_new_cargo_strands.xlsx',
                                                   restart_row_by_column='Category', data_type='IDT_order',
                                                   plate_size=96)

idt_plate.columns = ['well', 'name', 'sequence', 'description']
# This plate was ordered as a 96-well version, then combined with the Nelson/Quimby plate into sw_src007 by hand
