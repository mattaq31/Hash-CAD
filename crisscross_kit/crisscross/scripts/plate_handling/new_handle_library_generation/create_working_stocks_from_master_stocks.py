from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_cargo_plates, get_cutting_edge_plates, sanitize_plate_map
import os
import pandas as pd


_, antihandle_plates, handle_plates, _ = get_cutting_edge_plates()

output_folder = '/Users/matt/Desktop/working_stocks_from_master_stocks'
create_dir_if_empty(output_folder)
transfer_volume = 6000 # 6ul

for group in [handle_plates, antihandle_plates]:
    for plate, plate_name in zip(group.plates, group.plate_names):
        output_command_list = []
        dest_plate = sanitize_plate_map(plate_name) + '_working_stock'
        source_plate = sanitize_plate_map(plate_name)
        for row in plate.iterrows():
            if isinstance(row[1]['name'], str):
                source_well = row[1]['well']
                dest_well = row[1]['well']
                name = row[1]['name']
                output_command_list.append([name, source_plate, source_well, dest_well, transfer_volume, dest_plate, '384PP_AQ_BP'])

        combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                                 'Destination Well', 'Transfer Volume',
                                                                 'Destination Plate Name', 'Source Plate Type'])

        combined_df.to_csv(os.path.join(output_folder, f'{dest_plate}_echo_commands.csv'), index=False)
