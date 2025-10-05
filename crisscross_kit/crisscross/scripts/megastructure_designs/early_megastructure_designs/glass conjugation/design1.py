import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import read_design_from_excel
from crisscross.slat_handle_match_evolver.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.plate_mapping import get_standard_plates
from crisscross.plate_mapping.plate_constants import seed_plug_plate_center_8064, flat_staple_plate_folder
from crisscross.plate_mapping import get_plateclass

design_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/'
slat_array = read_design_from_excel(design_folder, ['bottomlayer1.csv','toplayer1.csv'])
p8064_seed_plate = get_plateclass('CombinedSeedPlugPlate', seed_plug_plate_center_8064, flat_staple_plate_folder)
#slat_array, _ = generate_standard_square_slats(32)

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates(handle_library_v2 = True)

handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, max_rounds=150)
np.savetxt(os.path.join(design_folder, 'optimized_handle_array.csv'), handle_array.squeeze().astype(np.int32),
               delimiter=',', fmt='%i')

#handle_array = np.loadtxt(os.path.join(design_folder, 'optimized_handle_array.csv'), delimiter=',').astype(np.float32)
#handle_array = handle_array[..., np.newaxis]

insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

center_seed_array = np.zeros((66, 66))
center_seed_array[17:33, 14:14+5] = insertion_seed_array


M1 = Megastructure(slat_array)
for rev_slat in range(130,138):
    M1.slats[f'layer1-slat{rev_slat}'].reverse_direction()
for rev_slat in range(146, 154):
    M1.slats[f'layer1-slat{rev_slat}'].reverse_direction()
M1.assign_assembly_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M1.assign_seed_handles(center_seed_array, p8064_seed_plate)
M1.patch_flat_staples(core_plate)
M1.export_design('full_design_rev2.xlsx',design_folder)
M1.create_standard_graphical_report(design_folder)

