from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import read_design_from_excel
import numpy as np
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize
from crisscross.plate_mapping import get_plateclass, get_standard_plates
from crisscross.helper_functions.plate_constants import nelson_quimby_antihandles, cargo_plate_folder

# Step 1 - generate weird shaped design (maybe just the plus for now)
folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/scratch/plus_design'

base_array = read_design_from_excel(folder, sheets=('slats_bottom.csv', 'slats_middle.csv', 'slats_top.csv'))

# Step 2 - place cargo in a few places
cargo_key = {3: 'antiNelson'}
cargo_array = np.zeros(base_array.shape[0:2])
cargo_array[30, 30:40] = 3
cargo_array[20, 10:20] = 3

# Step 3 - prepare assembly array optimization system
handle_array = generate_handle_set_and_optimize(base_array, unique_sequences=32, max_rounds=1)

# Step 4 - generate dictionary of slats

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate = get_standard_plates()

cargo_plate = get_plateclass('GenericPlate', nelson_quimby_antihandles, cargo_plate_folder)

megastructure = Megastructure(base_array, None)
megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)

seed_array = np.zeros((66, 66))
standard_seed_array = np.arange(16) + 1
standard_seed_array = np.pad(standard_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
seed_array[17:33, 1:6] = standard_seed_array
megastructure.assign_seed_handles(seed_array, seed_plate)
megastructure.assign_cargo_handles_with_array(cargo_array, cargo_key, cargo_plate, layer='bottom')

megastructure.patch_control_handles(core_plate)
megastructure.create_graphical_slat_view(instant_view=True)

