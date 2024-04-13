from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import read_design_from_excel, calculate_slat_hamming
import numpy as np
import matplotlib.pyplot as plt
from crisscross.core_functions.slat_design import (generate_standard_square_slats, generate_handle_set_and_optimize)
from crisscross.core_functions.slats import Slat
from crisscross.plate_mapping import get_plateclass
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_h5_handle_plates,
                                                         crisscross_h2_handle_plates,
                                                         seed_plug_plate_corner, seed_plug_plate_center,
                                                         octahedron_patterning_v1, cargo_plate_folder,
                                                         nelson_quimby_antihandles, h2_biotin_direct)
import os

# TODO: Areas that need to be upgraded to allow for non-square designs + multi-layer:
# need to introduce 60deg slat system!
# TODO: how to mandate direction of slats?

# Step 1 - generate weird shaped design (maybe just the plus for now)

folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/scratch/plus_design'

base_array = read_design_from_excel(folder, sheets=('slats_bottom.csv', 'slats_middle.csv', 'slats_top.csv'))

# Step 2 - place cargo in a few places

cargo_array = np.zeros(base_array.shape[0:2])

cargo_array[30, 30:40] = 2
cargo_array[20, 10:20] = 3

# Step 3 - prepare assembly array optimization system - problem here - need to rejig for multiple layers and also output handle array will have to have multiple channels too

handle_array = generate_handle_set_and_optimize(base_array, unique_sequences=32, min_hamming=29, max_rounds=1)

# Step 4 - generate dictionary of slats
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)

crisscross_handle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                            crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates[3:],
                                            core_plate_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
crisscross_antihandle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[0:3] + crisscross_h2_handle_plates[0:3],
                                                core_plate_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])

seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)
center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, core_plate_folder)
cargo_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1, cargo_plate_folder)

# slat_array, x_slats, y_slats = generate_standard_square_slats(32)
# unique_slats_per_layer = []
# for i in range(slat_array.shape[2]):
#     slat_ids = np.unique(slat_array[:, :, i])
#     slat_ids = slat_ids[slat_ids != 0]
#     unique_slats_per_layer.append(slat_ids)
#
# handle_array = np.loadtxt(os.path.join('/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_feb_2024', 'optimized_handle_array.csv'), delimiter=',').astype(
#     np.float32)
# _, _, res = calculate_slat_hamming(slat_array, handle_array[..., np.newaxis], unique_slats_per_layer, unique_sequences=32)
# print(res)
megastructure = Megastructure(base_array, None)
megastructure.assign_crisscross_handles(handle_array, crisscross_antihandle_x_plates, crisscross_handle_y_plates)

seed_array = np.zeros((66, 66))

standard_seed_array = np.arange(16) + 1
standard_seed_array = np.pad(standard_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
seed_array[17:33, 1:6] = standard_seed_array
megastructure.assign_seed_handles(seed_array, seed_plate)
megastructure.assign_cargo_handles(cargo_array, cargo_plate, layer='bottom')
megastructure.patch_control_handles(core_plate)

bottom, top = megastructure.create_combined_graphical_view()

plt.imshow(bottom)
plt.show()
plt.imshow(top)
plt.show()
z = 5
# Step 5 - export slats to robot format
