import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_cutting_edge_plates

########################################

# SETUP
design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SM01_hexagon_battleship_v1'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
#create_dir_if_empty(echo_folder, lab_helper_folder)

# Flags for quality of life improvements
generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False

# Get plate mapping from current handle library set - tells us where the oligos we need are located on physical oligo plates
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, all_8064_seed_plugs = get_cutting_edge_plates()

# Same as above, but for cargo plates
#src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()
src_004, _, _, _, _, _ = get_cargo_plates()

# Create a Megastructure class with the design file we made in Hash CAD
myHexagon = Megastructure(import_design_file=os.path.join(design_folder, 'square_example.xlsx'))
myHexagon.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_004],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo'])
myHexagon.patch_control_handles(core_plate)

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=myHexagon.slats,
                                                        destination_plate_name='SM01_hexagon_battleship_v1',
                                                        default_transfer_volume=100,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SM01_hexagon_battleship_v1.csv')

