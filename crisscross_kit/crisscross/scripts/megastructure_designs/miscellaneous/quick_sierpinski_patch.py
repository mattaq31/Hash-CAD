import pandas as pd
import numpy as np
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import cargo_plate_folder, simpsons_mixplate_antihandles_maxed


design_file = '/Users/matt/Desktop/20251217-Sierpinski_for_echo_final.xlsx'
no_handles_file = '/Users/matt/Desktop/sierpinski_no_handles.xlsx'

megastructure = Megastructure(import_design_file=no_handles_file)

# read in handles from design file
design_df = pd.read_excel(design_file, sheet_name=None, header=None)
layer_count = 0

for i, key in enumerate(design_df.keys()):
    if 'slat_layer_' in key:
        layer_count += 1
handle_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], layer_count - 1))

for i in range(layer_count):
    if i != layer_count - 1:
        handle_array[..., i] = design_df['handle_interface_%s' % (i + 1)].values


for key, slat in megastructure.slats.items():
    sides = []
    if slat.layer == 1:
        sides.append('top')
    elif slat.layer == len(megastructure.layer_palette):
        sides.append('bottom')
    else:
        sides.extend(['top', 'bottom'])

    for slat_position_index in range(slat.max_length):
        coords = slat.slat_position_to_coordinate[slat_position_index + 1]
        for side in sides:
            slat_side = megastructure.layer_palette[slat.layer][side]
            if side == 'top':
                handle_val = int(handle_array[coords[0], coords[1], slat.layer-1])
                sel_plates = None
                category = 'ANTIHANDLE'
            else:
                handle_val = int(handle_array[coords[0], coords[1], slat.layer-2])
                sel_plates = None
                category = 'HANDLE'
            if handle_val > 0:
                megastructure.assign_handle_to_slat(slat, slat_position_index + 1, slat_side, str(handle_val), 'ASSEMBLY_%s' % category, 'Assembly|%s|%s' % (category.capitalize(), handle_val), sel_plates, suppress_warnings=False)

main_plates = get_cutting_edge_plates(200)
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

megastructure.patch_placeholder_handles(main_plates + (src_010,))
megastructure.patch_flat_staples(main_plates[0])




