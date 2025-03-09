from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.plate_mapping import get_plateclass
from crisscross.plate_mapping.plate_constants import (core_plate_folder, crisscross_h5_handle_plates,
                                                      crisscross_h2_handle_plates, slat_core)
from collections import defaultdict
import pandas as pd

# Creates the missing 6 plates for the H2 assembly handles
crisscross_y_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[3:], core_plate_folder) 
crisscross_x_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[0:3], core_plate_folder)
crisscross_x_h2_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h2_handle_plates[0:3], core_plate_folder, slat_side=2)
crisscross_y_h2_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h2_handle_plates[0:3], core_plate_folder, slat_side=2)

core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
new_plates = defaultdict(list)

# This convention does not match what we ended up using in the end - handles are x and antihandles are y
antihandle_names = ['PX1_antihandle_SW_helix_2_assembly_handles', 'PX2_antihandle_SW_helix_2_assembly_handles', 'PX3_antihandle_SW_helix_2_assembly_handles']
handle_names = ['PY1_handle_SW_helix_2_assembly_handles', 'PY2_handle_SW_helix_2_assembly_handles', 'PY3_handle_SW_helix_2_assembly_handles']

antihandle_x_addon_seqs = []
handle_y_addon_seqs = []

core_sequences = [core_plate.sequences[i+1, 2, 0] for i in range(32)]

for i in range(32):
    antihandle_x_addon_seqs.append(crisscross_x_plates.sequences[(1, 5, i+1)].split('tt')[-1])
    handle_y_addon_seqs.append(crisscross_y_plates.sequences[(1, 5, i+1)].split('tt')[-1])

for plate_index, plate_name in enumerate(antihandle_names):
    for slat_number in range(12):
        if (plate_index*12) + slat_number > 31:
            break
        for seq_num in range(32):
            seq = core_sequences[(plate_index*12) + slat_number] + 'tt' + antihandle_x_addon_seqs[seq_num]
            new_plates[plate_name].append([seq, 'Assembly handle %d, on core seq %d of 6hb helix 2' % (seq_num + 1, (plate_index*12) + slat_number), 'slat_num_handle_num_n%d_k%d' % ((plate_index*12) + slat_number, seq_num+1)])

for plate_index, plate_name in enumerate(handle_names):
    for slat_number in range(12):
        if (plate_index*12) + slat_number > 31:
            break
        for seq_num in range(32):
            seq = core_sequences[(plate_index*12) + slat_number] + 'tt' + handle_y_addon_seqs[seq_num]
            new_plates[plate_name].append([seq, 'Assembly handle %d, on core seq %d of 6hb helix 2' % (seq_num + 1, (plate_index*12) + slat_number), 'slat_num_handle_num_n%d_k%d' % ((plate_index*12) + slat_number, seq_num+1)])


for key, val in new_plates.items():
    plate = pd.DataFrame(val, columns=['Sequence', 'Name', 'Description'])
    generate_new_plate_from_slat_handle_df(plate, '/Users/matt/Desktop', '%s.xlsx' % key, data_type='2d_excel')

crisscross_z_plates = get_plateclass('CrisscrossHandlePlates', handle_names, '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/core_plates/temp', slat_side=2)



