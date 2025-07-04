import matplotlib.pyplot as plt

import os
import numpy as np
import copy
import sys
import pandas as pd

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

########################################
# SETUP
design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW126_bionwire_wide_trench'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False
export_trench_design = True

np.random.seed(8)
# TODO: run the evolution algorithm for 64-seq
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, _, _, _, combined_seed_plate_8064 = get_standard_plates(handle_library_v2=True)
src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()

########################################
# Three otherwise standard megastructures, just different lengths of handles

for i in np.arange(1,3+1,1):
    square = Megastructure(import_design_file=os.path.join(design_folder, 'square_%s.xlsx' % i))
    square.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate_8064, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
    square.patch_control_handles(core_plate)

    # Can skip a ton of stuff, just a standard crisscross structure
    nominal_handle_volume = 150
    echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=square.slats,
                                                        destination_plate_name='bionwire_square_variable_handles_plate_%s' % i,
                                                        default_transfer_volume=nominal_handle_volume,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'echo_base_commands_square_%s.csv' % i)
        
    print("Finished processing square {}!".format(i))