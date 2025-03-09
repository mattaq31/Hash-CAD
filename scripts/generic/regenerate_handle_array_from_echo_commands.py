import pandas as pd
import numpy as np
import os

from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.core_functions.megastructures import Megastructure

from crisscross.plate_mapping.plate_constants import (slat_core, core_plate_folder, assembly_handle_folder,
                                                      crisscross_h5_handle_plates,
                                                      seed_plug_plate_corner, seed_plug_plate_center,
                                                      octahedron_patterning_v1, old_format_cargo_plate_folder,
                                                      h2_biotin_direct,
                                                      sanitize_plate_map)
from crisscross.plate_mapping import get_plateclass

stella_file = '/Users/matt/Desktop/20231023_SW082_unitsq0_cornerseed_scaledup_centered.csv'
stella_nucx_file = '/Users/matt/Desktop/20231023_SW082_unitsq0_cornerseed_scaledup_centered.csv'

stella_df = pd.read_csv(stella_file)

core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
crisscross_y_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[3:], assembly_handle_folder, plate_slat_sides=[5, 5, 5])
crisscross_x_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[0:3], assembly_handle_folder, plate_slat_sides=[5, 5, 5])
seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)
center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, core_plate_folder)
cargo_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1, old_format_cargo_plate_folder)

slats = {}

slat_array, unique_slats_per_layer = generate_standard_square_slats(32)
handle_array = np.zeros((32, 32))
handle_array_y = np.zeros((32, 32))
megastructure = Megastructure(slat_array)

h5_x = [sanitize_plate_map(x) for x in crisscross_h5_handle_plates[0:3]]
h5_y = [sanitize_plate_map(y) for y in crisscross_h5_handle_plates[3:]]

seen_rows = set()
seen_rows_y = set()

curr_slat = 0
curr_handle = 0
for index, row in stella_df.iterrows():
   if row['Source Plate Name'] in h5_x:
        if row['Destination Well'] not in seen_rows:
            curr_slat += 1
            seen_rows.add(row['Destination Well'])
            curr_handle = 0

        plate_df = crisscross_x_plates.plates[crisscross_x_plates.plate_names.index(row['Source Plate Name']+'_handles')]
        mapping = plate_df[plate_df['well'] == row['Source Well']]['description'].str.extract(r'(n\d+_k\d+)', expand=False)

        handle_array[curr_slat-1, curr_handle] = int(mapping[0].split('k')[-1])
        curr_handle += 1
curr_slat = 0
curr_handle = 0
for index, row in stella_df.iterrows():
   if row['Source Plate Name'] in h5_y:
        if row['Destination Well'] not in seen_rows_y:
            curr_slat += 1
            seen_rows_y.add(row['Destination Well'])
            curr_handle = 0
        plate_df = crisscross_y_plates.plates[crisscross_y_plates.plate_names.index(row['Source Plate Name']+'_antihandles')]
        mapping = plate_df[plate_df['well'] == row['Source Well']]['description'].str.extract(r'(n\d+_k\d+)', expand=False)

        handle_array_y[curr_handle, curr_slat-1] = int(mapping[0].split('k')[-1])
        curr_handle += 1

if np.all(handle_array_y == handle_array):
    print('Success - design regenerated!')

np.savetxt(os.path.join('/Users/matt/Desktop', 'stella_handle_array.csv'), handle_array.squeeze().astype(np.int32), delimiter=',',
           fmt='%i')
