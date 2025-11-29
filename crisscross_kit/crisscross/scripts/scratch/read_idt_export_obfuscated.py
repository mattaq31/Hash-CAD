from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
import pandas as pd
import os

folder = '/Users/matt/Desktop'
file = '20251120_tubeoligos_idtentry.xlsx'
new_file = '20251120_tubeoligos_idtentry_converted.xlsx'

input_df = pd.read_excel(os.path.join(folder, file))
input_df['Description'] = ''

generate_new_plate_from_slat_handle_df(input_df,
                                       folder,
                                       new_file,
                                       scramble_names=False,
                                       data_type='IDT_order',
                                       plate_size=96)
