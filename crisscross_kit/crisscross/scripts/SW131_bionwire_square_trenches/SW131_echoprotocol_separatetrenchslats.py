import os
from itertools import product

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_cutting_edge_plates

########################################
# NOTES

# This design uses the full 64 handle library with the H30 handle array
# Specific wells need to be PEG precipitated independently. The folding volume is 100 µL, which should be enough for single slat PEG precipitation.

########################################
# SETUP
design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW131_bionwire_square_trenches'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False
export_trench_design = True

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, all_8064_seed_plugs = get_cutting_edge_plates()

src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()

########################################
# Just making one megastructure, but PEG precipitating slats near the trench separately

square = Megastructure(import_design_file=os.path.join(design_folder, 'SW131_trenchsquare10nts_design.xlsx'))
square.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
square.patch_control_handles(core_plate)

manual_wells = []
for x,y in product(["A","B", "C", "D", "E", "F", "G", "H"], range(3, 11)):
    if x+str(y) == "F10":
        continue
    else:
        manual_wells.append((1,x+str(y)))

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=square.slats,
                                                        destination_plate_name='bionwire_square_trench_plate',
                                                        default_transfer_volume=150,
                                                        output_folder=echo_folder,
                                                        manual_plate_well_assignments=manual_wells,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SW131_echo_base_commands_trenchsquare.csv')