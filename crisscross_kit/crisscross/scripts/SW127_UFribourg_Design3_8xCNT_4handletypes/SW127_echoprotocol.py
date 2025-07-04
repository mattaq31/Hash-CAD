import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_cutting_edge_plates

########################################
# NOTES

# This structure will be H30 and have 8 slats with non-conventional h1 handles. 
# These will be manually pooled and separately combined with a modified core staple pool.

########################################
# SETUP
design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW127_fribourg_design3_h1multibinding'
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
# Also just one megastructure, can treat this as a typical Unit Sq

square = Megastructure(import_design_file=os.path.join(design_folder, 'SW127_full_design.xlsx'))
square.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
square.patch_control_handles(core_plate)

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=square.slats,
                                                        destination_plate_name='ufribourg_design3_h1handles_plate',
                                                        default_transfer_volume=100,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SW127_echo_base_commands_h1handles.csv')
